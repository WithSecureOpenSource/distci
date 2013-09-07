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

        self.state = {}
        self.log.debug('Starting with capabilities: %r', self.worker_config['capabilities'])

    def get_workspace(self):
        """ fetch workspace """
        self.log.debug('Fetching workspace')
        self.state['workspace'] = self.fetch_workspace(self.state['task'].config['job_id'], self.state['task'].config['build_number'])
        return self.state['workspace'] is not None

    def start_script(self):
        """ launch the configured script """
        self.log.debug('Launching build script')
        # write out script to execute
        (script_handle, script_name) = tempfile.mkstemp()
        os.close(script_handle)
        fileh = open(script_name, 'wb')
        fileh.write(self.state['task'].config['params']['script'])
        fileh.close()

        self.state['script_name'] = script_name

        self.state['start_timestamp'] = time.time()

        # execute
        if self.state['task'].config['params'].get('working_directory'):
            wdir = os.path.join(self.state['workspace'], self.state['task'].config['params']['working_directory'])
        else:
            wdir = self.state['workspace']

        cmd_and_args = [ "sh", script_name ]
        env = os.environ.copy()
        env['JOB_NAME'] = self.state['task'].config['job_id']
        env['BUILD_NUMBER'] = self.state['task'].config['build_number']
        env['WORKSPACE'] = self.state['workspace']
        console_log_fd, console_log_name = tempfile.mkstemp()
        self.state['console_output'] = { 'in': os.fdopen(console_log_fd),
                                         'out': open(console_log_name, 'rb'),
                                         'name': console_log_name }
        self.state['proc'] = subprocess.Popen(cmd_and_args, cwd=wdir, stdout=self.state['console_output']['in'], stderr=subprocess.STDOUT, env=env, preexec_fn=os.setpgrp, bufsize=1)

        self.log.debug('Build script PID %d', self.state['proc'].pid)

        return True

    def push_console_log(self):
        """ send and clear console log buffer """
        if len(self.state['log']) > 0:
            if self.distci_client.builds.console.append(self.state['task'].config['job_id'],
                                                        self.state['task'].config['build_number'],
                                                        self.state['log']) == True:
                self.state['log'] = ''
            else:
                self.log.error('Console log submit failed')
                return False
        return True

    def watch_process(self):
        """ check output and status of a running background process """
        retcode = self.state['proc'].poll()
        self.log.debug('Watch process, retcode %r', retcode)

        console_output_len = self.state['console_output']['in'].tell() - self.state['console_output']['out'].tell()
        if console_output_len > 0:
            try:
                output = self.state['console_output']['out'].read(console_output_len)
                self.state['log'] = '%s%s' % (self.state['log'], output.decode('utf-8').encode('ascii', 'replace'))
            except:
                self.log.exception('Console output decoding/encoding error')
        self.push_console_log()
        if retcode is not None:
            self.state['console_output']['in'].close()
            self.state['console_output']['out'].close()
            os.unlink(self.state['console_output']['name'])

            if retcode == 0:
                self.state['task'].config['result'] = 'success'
            else:
                self.state['task'].config['result'] = 'failure'
                self.state['task'].config['error'] = 'Executed script reported failure, exitcode %d' % retcode
            return True

        timeout = self.state['task'].config['params'].get('timeout')
        if timeout:
            ttl = self.state['start_timestamp'] + timeout - time.time()
            if ttl < -60.0:
                self.state['log'] = '%s\nTimed out, killing process...' % self.state['log']
                self.state['proc'].kill()
            elif ttl < 0.0:
                self.state['log'] = '%s\nTimed out, terminating...' % self.state['log']
                self.state['proc'].terminate()
        return False

    def report_result(self):
        """ push all remaining artifacts back to repository """
        self.log.debug('Reporting result')
        # delete temporary script
        if self.state.get('script_name') is not None and os.path.isfile(self.state['script_name']):
            os.unlink(self.state['script_name'])
            self.state['script_name'] = None
            self.log.debug('Build script deleted')

        # flush console log
        if self.push_console_log() == False:
            return False

        # pack and upload workspace
        if self.state.get('workspace') is not None:
            self.log.debug('Sending workspace')
            if self.send_workspace(self.state['task'].config['job_id'],
                                   self.state['task'].config['build_number'],
                                   self.state.get('workspace')) == False:
                self.log.debug('Sending workspace failed')
                return False
            self.state['workspace'] = None

        self.log.debug('Reporting complete')
        return True

    def perform_step(self):
        """ perform single step in state machine """
        self.log.debug('Performing state %s for task %s', self.state['state'], self.state['task'].id)
        if self.state['state'] == 'fetch-workspace' and self.get_workspace():
            self.state['state'] = 'start'
            return True
        elif self.state['state'] == 'start' and self.start_script():
            self.state['state'] = 'running'
            return True
        elif self.state['state'] == 'running' and self.watch_process():
            self.state['state'] = 'reporting'
        elif self.state['state'] == 'reporting' and self.report_result():
            self.state['state'] = 'complete'
            self.state['task'].config['status'] = 'complete'
            return True
        elif self.state['state'] == 'complete':
            if self.state['task'].config.get('assignee'):
                del self.state['task'].config['assignee']
            if self.update_task(self.state['task']) is not None:
                self.log.debug('Reported task as complete')
                self.state['task'] = None
                return True
        return False

    def start(self):
        """ main loop """
        while True:
            task = self.state.get('task')
            if task is None:
                task = self.fetch_task(timeout=60)
                if task is None:
                    continue
                self.state['task'] = task
                self.state['state'] = 'fetch-workspace'
                self.state['log'] = ''

                if not task.config.get('params') or not task.config['params'].get('script'):
                    self.state['state'] = 'complete'
                    task.config['status'] = 'complete'
                    task.config['result'] = 'failure'
                    task.config['error'] = 'Script not specified'

            if self.perform_step() == False:
                time.sleep(1)

