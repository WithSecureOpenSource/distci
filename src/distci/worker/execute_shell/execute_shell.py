"""
Execute worker

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import subprocess
import os
import tempfile
import time
import logging

from distci.worker import worker_base
from distci import distcilib

class ExecuteShellWorker(worker_base.WorkerBase):
    """ Git checkout worker """

    def __init__(self, config):
        worker_base.WorkerBase.__init__(self, config)
        self.log = logging.getLogger('execute-shell')
        self.worker_config['capabilities'] = ['execute_shell_v1']
        for label in config.get('labels', []):
            self.worker_config['capabilities'].append('nodelabel_%s' % label)
        self.distci_client = distcilib.DistCIClient(config)

        self.tasks = {}
        self.log.debug('Starting with capabilities: %r', self.worker_config['capabilities'])

    def get_workspace(self, task_id):
        """ fetch workspace """
        self.log.debug('Fetching workspace for task %s', task_id)
        self.tasks[task_id]['workspace'] = self.fetch_workspace(self.tasks[task_id]['task'].config['job_id'], self.tasks[task_id]['task'].config['build_number'])
        if self.tasks[task_id]['workspace']:
            self.tasks[task_id]['state'] = 'start'
            return True
        else:
            return False

    def start_script(self, task_id):
        """ launch the configured script """
        self.log.debug('Launching build script for task %s', task_id)
        # write out script to execute
        (script_handle, script_name) = tempfile.mkstemp()
        os.close(script_handle)
        fileh = open(script_name, 'wb')
        fileh.write(self.tasks[task_id]['task'].config['params']['script'])
        fileh.close()

        self.tasks[task_id]['script_name'] = script_name

        self.tasks[task_id]['start_timestamp'] = time.time()

        # execute
        if self.tasks[task_id]['task'].config['params'].get('working_directory'):
            wdir = os.path.join(self.tasks[task_id]['workspace'], self.tasks[task_id]['task'].config['params']['working_directory'])
        else:
            wdir = self.tasks[task_id]['workspace']

        cmd_and_args = [ "sh", script_name ]
        env = os.environ.copy()
        env['JOB_NAME'] = self.tasks[task_id]['task'].config['job_id']
        env['BUILD_NUMBER'] = self.tasks[task_id]['task'].config['build_number']
        env['WORKSPACE'] = self.tasks[task_id]['workspace']
        console_log_fd, console_log_name = tempfile.mkstemp()
        self.tasks[task_id]['console_output'] = {
                'in': os.fdopen(console_log_fd),
                'out': open(console_log_name, 'rb'),
                'name': console_log_name
            }
        try:
            self.tasks[task_id]['proc'] = subprocess.Popen(cmd_and_args, cwd=wdir, stdout=self.tasks[task_id]['console_output']['in'], stderr=subprocess.STDOUT, env=env, preexec_fn=os.setpgrp, bufsize=1)
        except OSError, exc:
            self.log.exception('Failed to launch script')
            self.tasks[task_id]['task'].config['result'] = 'failure'
            self.tasks[task_id]['task'].config['error'] = 'Failed to run the specified script'
            self.tasks[task_id]['log'] = '%s\nFailed to run the specified script\n%s\n' % (self.tasks[task_id]['log'], str(exc))
            self.tasks[task_id]['state'] = 'reporting'
            self.tasks[task_id]['console_output']['in'].close()
            self.tasks[task_id]['console_output']['out'].close()
            os.unlink(self.tasks[task_id]['console_output']['name'])
            return True

        self.log.debug('Build script PID %d', self.tasks[task_id]['proc'].pid)
        self.tasks[task_id]['state'] = 'running'
        return True

    def push_console_log(self, task_id):
        """ send and clear console log buffer """
        if len(self.tasks[task_id]['log']) > 0:
            if self.distci_client.builds.console.append(self.tasks[task_id]['task'].config['job_id'],
                                                        self.tasks[task_id]['task'].config['build_number'],
                                                        self.tasks[task_id]['log']) == True:
                self.tasks[task_id]['log'] = ''
            else:
                self.log.error('Console log submit failed for task %s', task_id)
                return False
        return True

    def watch_process(self, task_id):
        """ check output and status of a running background process """
        retcode = self.tasks[task_id]['proc'].poll()
        self.log.debug('Watch process for task %s, retcode %r', task_id, retcode)

        console_output_len = self.tasks[task_id]['console_output']['in'].tell() - self.tasks[task_id]['console_output']['out'].tell()
        if console_output_len > 0:
            try:
                output = self.tasks[task_id]['console_output']['out'].read(console_output_len)
                self.tasks[task_id]['log'] = '%s%s' % (self.tasks[task_id]['log'], output.decode('utf-8').encode('ascii', 'replace'))
            except:
                self.log.exception('Console output decoding/encoding error')
        self.push_console_log(task_id)
        if retcode is not None:
            self.tasks[task_id]['console_output']['in'].close()
            self.tasks[task_id]['console_output']['out'].close()
            os.unlink(self.tasks[task_id]['console_output']['name'])

            if retcode == 0:
                self.tasks[task_id]['task'].config['result'] = 'success'
            else:
                self.tasks[task_id]['task'].config['result'] = 'failure'
                self.tasks[task_id]['task'].config['error'] = 'Executed script reported failure, exitcode %d' % retcode
            self.tasks[task_id]['state'] = 'reporting'
            return True

        timeout = self.tasks[task_id]['task'].config['params'].get('timeout')
        if timeout:
            ttl = self.tasks[task_id]['start_timestamp'] + timeout - time.time()
            if ttl < -60.0:
                self.tasks[task_id]['log'] = '%s\nTimed out, killing process...' % self.tasks[task_id]['log']
                self.tasks[task_id]['proc'].kill()
            elif ttl < 0.0:
                self.tasks[task_id]['log'] = '%s\nTimed out, terminating...' % self.tasks[task_id]['log']
                self.tasks[task_id]['proc'].terminate()
        return False

    def report_result(self, task_id):
        """ push all remaining artifacts back to repository """
        self.log.debug('Reporting result for task %s', task_id)
        # delete temporary script
        if self.tasks[task_id].get('script_name') is not None and os.path.isfile(self.tasks[task_id]['script_name']):
            os.unlink(self.tasks[task_id]['script_name'])
            self.tasks[task_id]['script_name'] = None
            self.log.debug('Build script deleted')

        # flush console log
        if self.push_console_log(task_id) == False:
            return False

        # pack and upload workspace
        if self.tasks[task_id].get('workspace') is not None:
            self.log.debug('Sending workspace')
            if self.send_workspace(self.tasks[task_id]['task'].config['job_id'],
                                   self.tasks[task_id]['task'].config['build_number'],
                                   self.tasks[task_id]['workspace']) == False:
                self.log.debug('Sending workspace failed')
                return False
            self.tasks[task_id]['workspace'] = None

        self.log.debug('Reporting complete')
        self.tasks[task_id]['state'] = 'complete'
        self.tasks[task_id]['task'].config['status'] = 'complete'
        return True

    def perform_step(self, task_id):
        """ perform single step in state machine """
        self.log.debug('Performing state %s for task %s', self.tasks[task_id]['state'], task_id)
        if self.tasks[task_id]['state'] == 'fetch-workspace':
            return self.get_workspace(task_id)
        elif self.tasks[task_id]['state'] == 'start':
            return self.start_script(task_id)
        elif self.tasks[task_id]['state'] == 'running':
            return self.watch_process(task_id)
        elif self.tasks[task_id]['state'] == 'reporting':
            return self.report_result(task_id)
        elif self.tasks[task_id]['state'] == 'complete':
            if self.tasks[task_id]['task'].config.get('assignee'):
                del self.tasks[task_id]['task'].config['assignee']
            if self.update_task(self.tasks[task_id]['task']) is not None:
                self.log.debug('Reported task as complete')
                del self.tasks[task_id]
                return True
        return False

    def start(self):
        """ main loop """
        while True:
            progress_made = False
            if len(self.tasks) < self.worker_config.get('executors', 1):
                new_task = self.fetch_task(timeout=10)
                if new_task:
                    self.tasks[new_task.id] = {
                            'task': new_task,
                            'state': 'fetch-workspace',
                            'log': ''
                        }
                    if not new_task.config.get('params') or not new_task.config['params'].get('script'):
                        self.tasks[new_task.id]['state'] = 'complete'
                        new_task.config['status'] = 'complete'
                        new_task.config['result'] = 'failure'
                        new_task.config['error'] = 'Script not specified'

            for task_id in self.tasks.keys():
                if self.perform_step(task_id):
                    progress_made = True

            if progress_made == False:
                time.sleep(1)

