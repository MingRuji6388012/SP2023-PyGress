import re
import boto3
import logging
import requests
from os.path import join
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from indra import get_config, has_config

logger = logging.getLogger('aws_utils')


def kill_all(job_queue, reason='None given', states=None):
    """Terminates/cancels all RUNNING, RUNNABLE, and STARTING jobs."""
    if states is None:
        states = ['STARTING', 'RUNNABLE', 'RUNNING']
    batch = boto3.client('batch')
    runnable = batch.list_jobs(jobQueue=job_queue, jobStatus='RUNNABLE')
    job_info = runnable.get('jobSummaryList')
    if job_info:
        job_ids = [job['jobId'] for job in job_info]
        # Cancel jobs
        for job_id in job_ids:
            batch.cancel_job(jobId=job_id, reason=reason)
    res_list = []
    for status in states:
        running = batch.list_jobs(jobQueue=job_queue, jobStatus=status)
        job_info = running.get('jobSummaryList')
        if job_info:
            job_ids = [job['jobId'] for job in job_info]
            for job_id in job_ids:
                logger.info('Killing %s' % job_id)
                res = batch.terminate_job(jobId=job_id, reason=reason)
                res_list.append(res)
    return res_list


def tag_instance(instance_id, **tags):
    """Tag a single ec2 instance."""
    logger.info("Got request to add tags %s to instance %s."
                % (str(tags), instance_id))
    ec2 = boto3.resource('ec2')
    instance = ec2.Instance(instance_id)

    # Remove None's from `tags`
    filtered_tags = {k: v for k, v in tags.items() if v and k}

    # Check for existing tags
    if instance.tags is not None:
        existing_tags = {tag.get('Key'): tag.get('Value')
                         for tag in instance.tags}
        logger.info("Ignoring existing tags; %s" % str(existing_tags))
        for tag_key in existing_tags.keys():
            filtered_tags.pop(tag_key, None)

    # If we have new tags to add, add them.
    tag_list = [{'Key': k, 'Value': v} for k, v in filtered_tags.items()]
    if len(tag_list):
        logger.info('Adding project tags "%s" to instance %s'
                    % (filtered_tags, instance_id))
        instance.create_tags(Tags=tag_list)
    else:
        logger.info('No new tags from: %s' % str(tags))
    return


def tag_myself(project='untagged_indra_batch', **other_tags):
    """Function run when indra is used in an EC2 instance to apply tags."""
    base_url = "http://169.254.169.254"
    try:
        resp = requests.get(base_url + "/latest/meta-data/instance-id")
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to service. Note this should only "
                       "be run from within a batch job.")
        return
    instance_id = resp.text
    tag_instance(instance_id, project=project, **other_tags)
    return


def get_batch_command(command_list, project=None, purpose=None):
    """Get the command appropriate for running something on batch."""
    command_str = ' '.join(command_list)
    ret = ['python', '-m', 'indra.util.aws', 'run_in_batch', command_str]
    if not project and has_config('DEFAULT_AWS_PROJECT'):
        project = get_config('DEFAULT_AWS_PROJECT')
    if project:
        ret += ['--project', project]
    if purpose:
        ret += ['--purpose', purpose]
    return ret


def run_in_batch(command_list, project, purpose):
    from subprocess import call
    tag_myself(project, purpose=purpose)
    logger.info('\n'+20*'='+' Begin Primary Command Output '+20*'='+'\n')
    ret_code = call(command_list)
    logger.info('\n'+21*'='+' End Primary Command Output '+21*'='+'\n')
    return ret_code


def get_jobs(job_queue='run_reach_queue', job_status='RUNNING'):
    """Returns a list of dicts with jobName and jobId for each job with the
    given status."""
    batch = boto3.client('batch')
    jobs = batch.list_jobs(jobQueue=job_queue, jobStatus=job_status)
    return jobs.get('jobSummaryList')


def get_job_log(job_info, log_group_name='/aws/batch/job',
                write_file=True, verbose=False):
    """Gets the Cloudwatch log associated with the given job.

    Parameters
    ----------
    job_info : dict
        dict containing entries for 'jobName' and 'jobId', e.g., as returned
        by get_jobs()
    log_group_name : string
        Name of the log group; defaults to '/aws/batch/job'
    write_file : boolean
        If True, writes the downloaded log to a text file with the filename
        '%s_%s.log' % (job_name, job_id)


    Returns
    -------
    list of strings
        The event messages in the log, with the earliest events listed first.
    """
    job_name = job_info['jobName']
    job_id = job_info['jobId']
    logs = boto3.client('logs')
    batch = boto3.client('batch')
    job_description = batch.describe_jobs(jobs=[job_id])
    log_stream_name = job_description['jobs'][0]['container']['logStreamName']
    stream_resp = logs.describe_log_streams(
                            logGroupName=log_group_name,
                            logStreamNamePrefix=log_stream_name)
    streams = stream_resp.get('logStreams')
    if not streams:
        logger.warning('No streams for job')
        return None
    elif len(streams) > 1:
        logger.warning('More than 1 stream for job, returning first')
    log_stream_name = streams[0]['logStreamName']
    if verbose:
        logger.info("Getting log for %s/%s" % (job_name, job_id))
    out_file = ('%s_%s.log' % (job_name, job_id)) if write_file else None
    lines = get_log_by_name(log_group_name, log_stream_name, out_file, verbose)
    return lines


def get_log_by_name(log_group_name, log_stream_name, out_file=None,
                    verbose=True):
    """Download a log given the log's group and stream name.

    Parameters
    ----------
    log_group_name : str
        The name of the log group, e.g. /aws/batch/job.

    log_stream_name : str
        The name of the log stream, e.g. run_reach_jobdef/default/<UUID>

    Returns
    -------
    lines : list[str]
        The lines of the log as a list.
    """
    logs = boto3.client('logs')
    kwargs = {'logGroupName': log_group_name,
              'logStreamName': log_stream_name,
              'startFromHead': True}
    lines = []
    while True:
        response = logs.get_log_events(**kwargs)
        # If we've gotten all the events already, the nextForwardToken for
        # this call will be the same as the last one
        if response.get('nextForwardToken') == kwargs.get('nextToken'):
            break
        else:
            events = response.get('events')
            if events:
                lines += ['%s: %s\n' % (evt['timestamp'], evt['message'])
                          for evt in events]
            kwargs['nextToken'] = response.get('nextForwardToken')
        if verbose:
            logger.info('%d %s' % (len(lines), lines[-1]))
    if out_file:
        with open(out_file, 'wt') as f:
            for line in lines:
                f.write(line)
    return lines


def dump_logs(job_queue='run_reach_queue', job_status='RUNNING'):
    """Write logs for all jobs with given the status to files."""
    jobs = get_jobs(job_queue, job_status)
    for job in jobs:
        get_job_log(job, write_file=True)


def analyze_reach_log(log_fname=None, log_str=None):
    """Return unifinished PMIDs given a log file name."""
    assert bool(log_fname) ^ bool(log_str), 'Must specify log_fname OR log_str'
    started_patt = re.compile('Starting ([\d]+)')
    # TODO: it might be interesting to get the time it took to read
    # each paper here
    finished_patt = re.compile('Finished ([\d]+)')

    def get_content_nums(txt):
        pat = 'Retrieved content for ([\d]+) / ([\d]+) papers to be read'
        res = re.match(pat, txt)
        has_content, total = res.groups() if res else None, None
        return has_content, total

    if log_fname:
        with open(log_fname, 'r') as fh:
            log_str = fh.read()
    # has_content, total = get_content_nums(log_str)  # unused
    pmids_started = started_patt.findall(log_str)
    pmids_finished = finished_patt.findall(log_str)
    pmids_not_done = set(pmids_started) - set(pmids_finished)
    return pmids_not_done


#==============================================================================
# Functions for analyzing a db reading submission
#==============================================================================


def get_logs_from_db_reading(job_prefix, reading_queue='run_db_reading_queue'):
    """Get the logs stashed on s3 for a particular reading."""
    s3 = boto3.client('s3')
    gen_prefix = 'reading_results/%s/logs/%s' % (job_prefix, reading_queue)
    job_log_data = s3.list_objects_v2(Bucket='bigmech',
                                      Prefix=join(gen_prefix, job_prefix))
    # TODO: Track success/failure
    log_strs = []
    for fdict in job_log_data['Contents']:
        resp = s3.get_object(Bucket='bigmech', Key=fdict['Key'])
        log_strs.append(resp['Body'].read().decode('utf-8'))
    return log_strs


def separate_reach_logs(log_str):
    """Get the list of reach logs from the overall logs."""
    log_lines = log_str.splitlines()
    reach_logs = []
    reach_lines = []
    adding_reach_lines = False
    for l in log_lines[:]:
        if not adding_reach_lines and 'Beginning reach' in l:
            adding_reach_lines = True
        elif adding_reach_lines and 'Reach finished' in l:
            adding_reach_lines = False
            reach_logs.append(('SUCCEEDED', '\n'.join(reach_lines)))
            reach_lines = []
        elif adding_reach_lines:
            reach_lines.append(l.split('readers - ')[1])
            log_lines.remove(l)
    if adding_reach_lines:
        reach_logs.append(('FAILURE', '\n'.join(reach_lines)))
    return '\n'.join(log_lines), reach_logs


def get_top_level_summary_of_log(log_str):
    ret_str = 'Event Summary:'
    ret_str += '\n' + '-'*len(ret_str)
    ret_str += '\nUseful INFO:\n  '
    ret_str += '\n  '.join(re.findall(
        ('INFO: \[.*?\] indra/((?!readers).* - '
         '(?!Got no statements|Saving sparser)(?=.*\d.*).*)'),
        log_str))
    ret_str += '\nWARNINGS that occured:\n  '
    ret_str += '\n  '.join(set(get_indra_logs_by_priority(log_str, 'WARNING')))
    ret_str += '\nERRORS that occured:\n  '
    ret_str += '\n  '.join(set(get_indra_logs_by_priority(log_str, 'ERROR')))
    return ret_str


def get_top_level_summary_of_logs(log_str_list):
    ret_dict = {}
    ret_dict['total_stats'] = {}
    ret_dict['err_set'] = set()
    ret_dict['warn_set'] = set()
    ret_dict['unyielding_tcids'] = set()
    ret_dict['num_failures'] = 0
    for log_str in log_str_list:
        try:
            stat_dict = get_reading_stats(log_str)
            ret_dict['total_stats'] = {k: ret_dict['total_stats'].get(k, 0) + v
                                       for k, v in stat_dict.items()}
        except GetReadingStatsError:
            ret_dict['num_failures'] += 1
        ret_dict['err_set'] |= set(get_indra_logs_by_priority(log_str,
                                                              'ERROR'))
        ret_dict['warn_set'] |= set(get_indra_logs_by_priority(log_str,
                                                               'WARNING'))
        ret_dict['unyielding_tcids'] |= get_unyielding_tcids(log_str)
    ret_dict['err_tcids'] = {int(re.findall('(\d+)', err_str)[0])
                             for err_str in ret_dict['err_set']
                             if 'Got exception creating statements' in err_str}
    return ret_dict


def get_indra_logs_by_priority(log_str, priority='INFO'):
    return re.findall('%s: \[.*?\] indra/(.*)' % priority, log_str)


def get_unyielding_tcids(log_str):
    """Extract the set of tcids for which no statements were created."""
    tcid_strs = re.findall('INFO: \[.*?\].*? - Got no statements for (\d+).*',
                           log_str)
    return {int(tcid_str) for tcid_str in tcid_strs}


class GetReadingStatsError(Exception):
    pass


def get_reading_stats(log_str):
    def re_get_nums(patt_str, default=None):
        re_ret = re.search(patt_str, log_str)
        if re_ret is not None:
            nums = [int(num_str) for num_str in re_ret.groups()]
        elif default is None:
            raise GetReadingStatsError("couldn't match patt \"%s\"" % patt_str)
        else:
            nums = [default]*patt_str.count('(\d+)')
        return nums
    ret_dict = {}
    ret_dict['num_prex_readings'] = \
        re_get_nums('Found (\d+) pre-existing readings', 0)[0]
    ret_dict['num_new_readings'] = re_get_nums('Made (\d+) new readings')[0]
    ret_dict['num_succeeded'] = \
        re_get_nums('Adding (\d+)/\d+ reading entries')[0]
    ret_dict['num_stmts'], ret_dict['num_readings'] = \
        re_get_nums('Found (\d+) statements from (\d+) readings')
    ret_dict['num_agents'] = \
        re_get_nums('Received request to copy (\d+) entries into agents')[0]
    return ret_dict


def analyze_db_reading(job_prefix, reading_queue='run_db_reading_queue'):
    """Run various analysis on a particular reading job."""
    # Analyze reach failures
    log_strs = get_logs_from_db_reading(job_prefix, reading_queue)
    indra_log_strs = []
    all_reach_logs = []
    for log_str in log_strs:
        log_str, reach_logs = separate_reach_logs(log_str)
        all_reach_logs.extend(reach_logs)
        indra_log_strs.append(log_str)
    failed_reach_logs = [reach_log_str
                         for result, reach_log_str in all_reach_logs
                         if result == 'FAILURE']
    tcids_unfinished = {tcid for reach_log in failed_reach_logs
                        if bool(reach_log)
                        for tcid in analyze_reach_log(log_str=reach_log)}
    logger.info("Found %d unfinished tcids." % len(tcids_unfinished))
    return tcids_unfinished


if __name__ == '__main__':
    parser = ArgumentParser(
        'aws.py',
        description=('Use some of INDRA\'s aws tools. For more specific help, '
                     'select one of the Methods with the `-h` option.')
        )
    subparsers = parser.add_subparsers(title='Task')
    subparsers.required = True
    subparsers.dest = 'task'

    # Create parent parser classes for second layer of options
    parent_run_parser = ArgumentParser(add_help=False)
    parent_run_parser.add_argument(
        'command',
        help=('Enter the command as a single string to be run as if in a '
              'batch environment.')
        )
    parent_run_parser.add_argument(
        '--project', '-P',
        default='untagged_indra_batch',
        help='Give a name for the project.'
        )
    parent_run_parser.add_argument(
        '--purpose', '-p',
        help='Give the task some meaning.'
        )
    parent_kill_parser = ArgumentParser(add_help=False)
    parent_kill_parser.add_argument(
        'queue_name',
        help='Select the batch queue in which all jobs should be terminated.'
        )
    parent_kill_parser.add_argument(
        '--reason', '-R',
        help='Give a reason for killing all the jobs.'
        )
    # Make non_db_parser and get subparsers
    run_parser = subparsers.add_parser(
        'run_in_batch',
        parents=[parent_run_parser],
        description=('This should be called to run any command wtihin an aws '
                     'batch job instance.'),
        formatter_class=ArgumentDefaultsHelpFormatter
        )

    # Make db parser and get subparsers.
    kill_parser = subparsers.add_parser(
        'kill_all',
        parents=[parent_kill_parser],
        description='Kill all the jobs running in a given queue.',
        formatter_class=ArgumentDefaultsHelpFormatter
        )
    args = parser.parse_args()

    if args.task == 'run_in_batch':
        ret_code = run_in_batch(args.command.split(' '), args.project,
                                args.purpose)
        if ret_code is 0:
            logger.info('Job endend well.')
        else:
            logger.error('Job failed!')
            import sys
            sys.exit(ret_code)
    elif args.task == 'kill_all':
        kill_all(args.queue_name, args.reason)