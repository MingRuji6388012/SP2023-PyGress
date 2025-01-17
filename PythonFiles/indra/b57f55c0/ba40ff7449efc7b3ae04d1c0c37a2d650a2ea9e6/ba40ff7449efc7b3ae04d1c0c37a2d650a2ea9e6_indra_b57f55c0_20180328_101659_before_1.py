"""This tool provides a uniform method for createing a robust indra version
string, both from within python and from commandline. If possible, the version
will include the git commit hash. Otherwise, the version will be marked with
'UNHASHED'.
"""

from subprocess import check_output, CalledProcessError
from os.path import dirname
from os import devnull

from indra import __version__


def get_version(with_git_hash=True):
    """Get an indra version string, including a git hash."""
    version = __version__
    if with_git_hash:
        with open(devnull, 'w') as nul:
            try:
                ret = check_output(['git', 'rev-parse', 'HEAD'],
                                   cwd=dirname(__file__), stderr=nul)
            except CalledProcessError:
                ret = 'UNHASHED'
        version = '%s-%s' % (version, ret.strip())
    return version


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-n', '--no_hash', action='store_true',
                        help='Choose to not include the git hash.')
    args = parser.parse_args()
    version = get_version(not args.no_hash)
    print(version)
