"""
Execute worker

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import subprocess
import os
import tempfile

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

    def send_failure(self, task, error):
        """ report error """
        task.config['status'] = 'complete'
        task.config['result'] = 'failure'
        task.config['error'] = error
        del task.config['assignee']
        self.update_task(task)

    def send_success(self, task):
        """ report success """
        task.config['status'] = 'complete'
        task.config['result'] = 'success'
        del task.config['assignee']
        self.update_task(task)

    def start(self):
        """ main loop """
        while True:
            task = self.fetch_task(timeout=60)

            if task is None:
                continue

            log = ''

            # 0. check parameters
            if not task.config.get('params') or not task.config['params'].get('script'):
                self.send_failure(task, 'Script not specified')
                continue

            # 1. Fetch and unpack workspace
            workspace = self.fetch_workspace(task.config['job_id'],
                                             task.config['build_number'])
            if workspace is None:
                self.send_failure(task, 'Failed to fetch workspace')
                continue

            # 2. create temporary script
            (script_handle, script_name) = tempfile.mkstemp()
            os.close(script_handle)
            fh = open(script_name, 'wb')
            fh.write(task.config['params']['script'])
            fh.close()

            # 3. run the script
            if task.config['params'].get('working_directory'):
                wdir = os.path.join(workspace, task.config['params']['working_directory'])
            else:
                wdir = workspace

            cmd_and_args = [ "sh", script_name ]
            proc = subprocess.Popen(cmd_and_args, cwd=wdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (output, _) = proc.communicate()

            log = '%s%s' % (log, output)

            if proc.returncode != 0:
                for _ in range(self.worker_config.get('retry_count', 10)):
                    if self.distci_client.builds.console.append(task.config['job_id'],
                                                                task.config['build_number'],
                                                                log) == True:
                        break
                self.send_failure(task, 'Executed script reported failure')
                self.delete_workspace(workspace)
                os.unlink(script_name)
                continue

            # 4. pack and upload workspace
            self.send_workspace(task.config['job_id'],
                                task.config['build_number'],
                                workspace)

            # 5. clear temp dir and script
            self.delete_workspace(workspace)
            os.unlink(script_name)

            # 6. push console log
            for _ in range(self.worker_config.get('retry_count', 10)):
                if self.distci_client.builds.console.append(task.config['job_id'],
                                                            task.config['build_number'],
                                                            log) == True:
                    break

            # 6. update task state
            self.send_success(task)

