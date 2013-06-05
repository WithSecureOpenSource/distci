"""
Execute worker

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import subprocess
import os
import tempfile
import time

from distci.worker import worker_base
from distci import distcilib

class ExecuteShellWorker(worker_base.WorkerBase):
    """ Git checkout worker """

    def __init__(self, config):
        worker_base.WorkerBase.__init__(self, config)
        self.worker_config['capabilities'] = ['execute_shell_v1']
        for label in config.get('labels', []):
            self.worker_config['capabilities'].append('nodelabel_%s' % label)
        self.distci_client = distcilib.DistCIClient(config)

        self.state = {}

    def get_workspace(self):
        """ fetch workspace """
        self.state['workspace'] = self.fetch_workspace(self.state['task'].config['job_id'], self.state['task'].config['build_number'])
        return self.state['workspace'] is not None

    def start_script(self):
        """ launch the configured script """
        # write out script to execute
        (script_handle, script_name) = tempfile.mkstemp()
        os.close(script_handle)
        fileh = open(script_name, 'wb')
        fileh.write(self.state['task'].config['params']['script'])
        fileh.close()

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
        self.state['proc'] = subprocess.Popen(cmd_and_args, cwd=wdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)

        os.unlink(script_name)
        return True

    def push_console_log(self):
        """ send and clear console log buffer """
        if len(self.state['log']) > 0:
            if self.distci_client.builds.console.append(self.state['task'].config['job_id'],
                                                        self.state['task'].config['build_number'],
                                                        self.state['log']) == True:
                self.state['log'] = ''
            else:
                return False
        return True

    def report_result(self):
        """ push all remaining artifacts back to repository """
        # flush console log
        if self.push_console_log() == False:
            return False

        # pack and upload workspace
        if self.state.get('workspace') is not None:
            if self.send_workspace(self.state['task'].config['job_id'],
                                   self.state['task'].config['build_number'],
                                   self.state.get('workspace')) == False:
                return False
            self.state['workspace'] = None

        return True

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

            if task.config['status'] == 'complete':
                if task.config.get('assignee'):
                    del task.config['assignee']
                if self.update_task(task) is not None:
                    self.state['task'] = None
                continue

            if not task.config.get('params') or not task.config['params'].get('script'):
                self.state['state'] = 'complete'
                task.config['status'] = 'complete'
                task.config['result'] = 'failure'
                task.config['error'] = 'Script not specified'
                continue

            if self.state['state'] == 'fetch-workspace':
                if self.get_workspace():
                    self.state['state'] = 'start'

            if self.state['state'] == 'start':
                if self.start_script() == True:
                    self.state['state'] = 'running'

            if self.state['state'] == 'running':
                retcode = self.state['proc'].poll()
                if retcode is not None:
                    self.state['state'] = 'reporting'
                    if retcode == 0:
                        self.state['task'].config['result'] = 'success'
                    else:
                        self.state['task'].config['result'] = 'failure'
                        self.state['task'].config['error'] = 'Executed script reported failure'
                self.state['log'] = '%s%s' % (self.state['log'], self.state['proc'].stdout.read())
                self.push_console_log()

            if self.state['state'] == 'reporting':
                if self.report_result() == True:
                    self.state['state'] = 'complete'
                    self.state['task'].config['status'] = 'complete'

            time.sleep(1)

