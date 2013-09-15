""" DistCI command line client

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import sys
import argparse
import os
import logging
import json

from distci import distcilib

def jobs_list(ctx):
    """ List jobs """
    jobs = ctx['client'].jobs.list()
    if jobs:
        for job in jobs['jobs']:
            print job
        return 0
    else:
        print "Failed to list jobs"
        return -1

def jobs_get(ctx, job_name):
    """ Get job config """
    job_config = ctx['client'].jobs.get(job_name)
    if job_config:
        print json.dumps(job_config['config'], indent=4)
        return 0
    else:
        print "Failed to get job configuration for", job_name
        return -1

def jobs_set(ctx, job_name, job_config_file):
    """ Set job config. Creates a new job if it does not exist. """
    job_config = json.load(file(job_config_file, 'rb'))
    job_config['job_id'] = job_name
    result = ctx['client'].jobs.set(job_name, job_config)
    if result:
        print "Success"
    else:
        print "Failed to set job configuration"
        return -1

def builds_trigger(ctx, job_name):
    """ Trigger a new build """
    result = ctx['client'].builds.trigger(job_name)
    if result:
        print "Success, build number", result['build_number']
    else:
        print "Failed to trigger build"
        return -1

def builds_list(ctx, job_name):
    """ List builds """
    result = ctx['client'].builds.list(job_name)
    if result:
        print ', '.join([str(val) for val in sorted(result['builds'])])
    else:
        print "Failed to list builds"
        return -1

def builds_get_state(ctx, job_name, build_number):
    """ Get build state """
    result = ctx['client'].builds.state.get(job_name, str(build_number))
    if result:
        print json.dumps(result['state'], indent=4)
    else:
        print "Failed to get state for %s %s" % (job_name, build_number)
        return -1

def tasks_list(ctx):
    """ List tasks """
    result = ctx['client'].tasks.list()
    if result:
        for task in result['tasks']:
            print task
    else:
        print "Failed to get list of tasks"
        return -1

def tasks_get(ctx, task_id):
    """ Get task data """
    result = ctx['client'].tasks.get(task_id)
    if result:
        print json.dumps(result, indent=4)
    else:
        print "Failed to get task data for %s" % task_id
        return -1

def main():
    """ Main """
    log_level = logging.getLevelName('INFO')
    logging.basicConfig(level=log_level, format='%(asctime)s\t%(threadName)s\t%(name)s\t%(levelname)s\t%(message)s')

    parser = argparse.ArgumentParser(description='DistCI CLI')
    parser.add_argument('-c', '--conf', type=str, nargs='?', default=os.path.expanduser('~/.distci'))

    subparsers = parser.add_subparsers(title='subcommands', dest='parser')

    job_parser = subparsers.add_parser('job', help='job commands')
    job_subparsers = job_parser.add_subparsers(title='job subcommands', dest='sub_parser')

    job_subparsers.add_parser('list', help='list jobs')
    job_get_parser = job_subparsers.add_parser('get', help='get job config')
    job_get_parser.add_argument('job_name', type=str)
    job_set_parser = job_subparsers.add_parser('set', help='set or create job config')
    job_set_parser.add_argument('job_name', type=str)
    job_set_parser.add_argument('job_config_file', type=str)

    build_parser = subparsers.add_parser('build', help='build commands')
    build_subparsers = build_parser.add_subparsers(title='build subcommands', dest='sub_parser')
    build_trigger_parser = build_subparsers.add_parser('trigger', help='trigger a new build')
    build_trigger_parser.add_argument('job_name', type=str)
    build_list_parser = build_subparsers.add_parser('list', help='list builds')
    build_list_parser.add_argument('job_name', type=str)
    build_state_parser = build_subparsers.add_parser('state', help='get build state')
    build_state_parser.add_argument('job_name', type=str)
    build_state_parser.add_argument('build_number', type=int)

    tasks_parser = subparsers.add_parser('task', help='task commands')
    tasks_subparsers = tasks_parser.add_subparsers(title='task subcommands', dest='sub_parser')
    tasks_subparsers.add_parser('list', help='list tasks')
    tasks_get_parser = tasks_subparsers.add_parser('get', help='get task data')
    tasks_get_parser.add_argument('task_id', type=str)

    args = parser.parse_args()

    config = json.load(file(args.conf, 'rb'))
    ctx = { "client": distcilib.DistCIClient(config) }

    if args.parser == 'job':
        if args.sub_parser == 'list':
            return jobs_list(ctx)
        elif args.sub_parser == 'get':
            return jobs_get(ctx, args.job_name)
        elif args.sub_parser == 'set':
            return jobs_set(ctx, args.job_name, args.job_config_file)
    elif args.parser == 'build':
        if args.sub_parser == 'trigger':
            return builds_trigger(ctx, args.job_name)
        elif args.sub_parser == 'list':
            return builds_list(ctx, args.job_name)
        elif args.sub_parser == 'state':
            return builds_get_state(ctx, args.job_name, args.build_number)
    elif args.parser == 'task':
        if args.sub_parser == 'list':
            return tasks_list(ctx)
        elif args.sub_parser == 'get':
            return tasks_get(ctx, args.task_id)
    print "Unknown command"
    return -1

if __name__ == "__main__":
    sys.exit(main())

