"""
Git checkout worker.

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import subprocess
import os

from distci.worker import worker_base
from distci import distcilib

class GitCheckoutWorker(worker_base.WorkerBase):
    """ Git checkout worker """

    def __init__(self, config):
        worker_base.WorkerBase.__init__(self, config)
        self.worker_config['capabilities'] = ['git_checkout_v1']
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
            if not task.config.get('params') or not task.config['params'].get('repository'):
                self.send_failure(task, 'Repository not specified')
                continue

            # 1. Fetch and unpack workspace
            workspace = self.fetch_workspace(task.config['job_id'],
                                             task.config['build_number'])
            if workspace is None:
                self.send_failure(task, 'Failed to fetch workspace')
                continue

            # 2. run git clone + checkout
            if task.config['params'].get('checkout-dir'):
                checkoutdir = os.path.join(workspace, task.config['params']['checkout-dir'])
            else:
                checkoutdir = workspace

            cmd_and_args = [ "git", "clone", task.config['params']['repository'], checkoutdir ]
            proc = subprocess.Popen(cmd_and_args, cwd=workspace, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (output, _) = proc.communicate()

            log = '%s%s' % (log, output)

            if proc.returncode != 0:
                for _ in range(self.worker_config.get('retry_count', 10)):
                    if self.distci_client.builds.console.append(task.config['job_id'],
                                                                task.config['build_number'],
                                                                log) == True:
                        break
                self.send_failure(task, 'Git clone failed')
                self.delete_workspace(workspace)
                continue

            cmd_and_args = [ "git", "checkout", "-q", task.config['params'].get('ref', 'refs/heads/master') ]
            proc = subprocess.Popen(cmd_and_args, cwd=checkoutdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (output, _) = proc.communicate()

            log = '%s%s' % (log, output)

            if proc.returncode != 0:
                for _ in range(self.worker_config.get('retry_count', 10)):
                    if self.distci_client.builds.console.append(task.config['job_id'],
                                                                task.config['build_number'],
                                                                log) == True:
                        break
                self.send_failure(task, 'Git checkout failed')
                self.delete_workspace(workspace)
                continue

            # 3. pack and upload workspace
            self.send_workspace(task.config['job_id'],
                                task.config['build_number'],
                                workspace)

            # 4. clear temp dir
            self.delete_workspace(workspace)

            # 5. push console log
            for _ in range(self.worker_config.get('retry_count', 10)):
                if self.distci_client.builds.console.append(task.config['job_id'],
                                                            task.config['build_number'],
                                                            log) == True:
                    break

            # 6. update task state
            self.send_success(task)

