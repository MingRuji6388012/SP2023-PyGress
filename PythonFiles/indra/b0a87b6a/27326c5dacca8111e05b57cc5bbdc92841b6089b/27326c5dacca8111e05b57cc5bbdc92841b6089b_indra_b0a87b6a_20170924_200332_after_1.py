# -*- coding: utf-8 -*-

"""
Module that contains the command line app

Why does this file exist, and why not put this in __main__?
You might be tempted to import things from __main__ later, but that will cause
problems--the code will get executed twice:
 - When you run `python3 -m indra` python will execute
   ``__main__.py`` as a script. That means there won't be any
   ``indra.__main__`` in ``sys.modules``.
 - When you import __main__ it will get executed again (as a module) because
   there's no ``indra.__main__`` in ``sys.modules``.
Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""

import sys

import click
import os


@click.group()
def main():
    """INDRA"""


@main.group()
def machine():
    """RAS Machine"""


@machine.command()
@click.argument('directory')
def make(directory):
    """Makes a RAS Machine directory"""
    from indra.tools.machine.config import copy_default_config

    if os.path.exists(directory):
        if os.path.isdir(directory):
            click.echo('Directory already exists')
        else:
            click.echo('Path exists and is not a directory')
        sys.exit()

    os.makedirs(directory)
    os.mkdir(os.path.join(directory, 'json'))
    os.mkdir(os.path.join(directory, 'json', 'abstract'))
    os.mkdir(os.path.join(directory, 'json', 'full'))
    copy_default_config(os.path.join(directory, 'config.yaml'))


@machine.command()
@click.argument('model_path')
@click.option('--config', help='Specify configuration file path, otherwise '
                               'looks for config.yaml in model path')
def run_with_search(model_path, config):
    """Run with PubMed search for new papers."""
    from indra.tools.machine.utils import run_with_search_helper
    run_with_search_helper(model_path, config)


@machine.command()
@click.argument('model_path')
def summarize(model_path):
    """Print model summary."""
    from indra.tools.machine.utils import summarize_helper
    summarize_helper(model_path)


@machine.command()
@click.argument('model_path')
@click.option('--pmids', type=click.File(), default=sys.stdin,
              help="A file with a PMID on each line")
def run_with_pmids(model_path, pmids):
    """Run with given list of PMIDs."""
    from indra.tools.machine.utils import run_with_pmids_helper
    run_with_pmids_helper(model_path, pmids)


if __name__ == '__main__':
    main()
