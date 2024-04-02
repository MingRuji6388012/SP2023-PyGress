import re
import boto3
from os.path import join


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
                print('Killing %s' % job_id)
                res = batch.terminate_job(jobId=job_id, reason=reason)
                res_list.append(res)
    return res_list


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
        print('No streams for job')
        return None
    elif len(streams) > 1:
        print('More than 1 stream for job, returning first')
    log_stream_name = streams[0]['logStreamName']
    if verbose:
        print("Getting log for %s/%s" % (job_name, job_id))
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
            print('%d %s' % (len(lines), lines[-1]))
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


def extract_reach_logs(log_str):
    """Get the list of reach logs from the overall logs."""
    log_lines = log_str.splitlines()
    reach_logs = []
    reach_lines = []
    adding_reach_lines = False
    for l in log_lines:
        if not adding_reach_lines and 'Beginning reach' in l:
            adding_reach_lines = True
        elif adding_reach_lines and 'Reach finished' in l:
            adding_reach_lines = False
            reach_logs.append(('SUCCEEDED', '\n'.join(reach_lines)))
            reach_lines = []
        elif adding_reach_lines:
            reach_lines.append(l.split('readers - ')[1])
    if adding_reach_lines:
        reach_logs.append(('FAILURE', '\n'.join(reach_lines)))
    return reach_logs


def analyze_db_reading(job_prefix, reading_queue='run_db_reading_queue'):
    """Run various analysis on a particular reading job."""
    # Analyze reach failures
    log_strs = get_logs_from_db_reading(job_prefix, reading_queue)
    reach_logs = [extract_reach_logs(log_str) for log_str in log_strs]
    failed_reach_logs = [reach_log_str for job_reach_logs in reach_logs
                         for result, reach_log_str in job_reach_logs
                         if result == 'FAILURE']
    tcids_unfinished = {tcid for reach_log in failed_reach_logs
                        for tcid in analyze_reach_log(log_str=reach_log)}
    print("Found %d unfinished tcids." % len(tcids_unfinished))
    return reach_logs, failed_reach_logs, tcids_unfinished