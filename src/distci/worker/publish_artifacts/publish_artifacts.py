"""
Artifact publishing worker

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import glob

from distci.worker import worker_base
from distci import distcilib

class PublishArtifactsWorker(worker_base.WorkerBase):
    """ Artifact publishing worker """

    def __init__(self, config):
        worker_base.WorkerBase.__init__(self, config)
        self.worker_config['capabilities'] = ['publish_artifacts_v1']
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
            if not task.config.get('params') or not task.config['params'].get('artifacts'):
                self.send_failure(task, 'Artifacts not specified')
                continue

            # 1. Fetch and unpack workspace
            workspace = self.fetch_workspace(task.config['job_id'],
                                             task.config['build_number'])
            if workspace is None:
                self.send_failure(task, 'Failed to fetch workspace')
                continue

            # 2. Upload artifacts matching the specified fileglobs
            task.config['artifacts'] = {}
            for mask in task.config['params'].get('artifacts'):
                path = os.path.abspath(os.path.join(workspace, mask))
                if path.startswith(os.path.join(workspace, '')):
                    for artifact in glob.iglob(path):
                        artifact_reply = None
                        abs_artifact = os.path.abspath(artifact)
                        rel_artifact = os.path.relpath(artifact, workspace)
                        for _ in range(self.worker_config.get('retry_count', 10)):
                            fh = open(abs_artifact, 'rb')
                            st = os.stat(abs_artifact)
                            artifact_reply = self.distci_client.builds.artifacts.put(task.config['job_id'], task.config['build_number'], fh, st.st_size)
                            fh.close()
                            if artifact_reply is not None and artifact_reply.get('artifact_id') is not None:
                                log = '%s\nStored \'%s\' as artifact \'%s\'' % (log, rel_artifact, artifact_reply.get('artifact_id'))
                                filename_parts = []
                                tail = rel_artifact
                                while tail != '':
                                    (tail, head) = os.path.split(tail)
                                    filename_parts.insert(0, head)
                                task.config['artifacts'][artifact_reply.get('artifact_id')] = filename_parts
                                break
                        if artifact_reply is None:
                            log = '%s\nFailed to store artifact \'%s\'' % (log, rel_artifact)
                            task.config['result'] = 'failure'

            # 3. clear temp dir
            self.delete_workspace(workspace)

            # 4. push console log
            for _ in range(self.worker_config.get('retry_count', 10)):
                if self.distci_client.builds.console.append(task.config['job_id'],
                                                            task.config['build_number'],
                                                            log) == True:
                    break

            # 5. update task state
            if task.config.get('result') == 'failure':
                self.send_failure(task, 'Failed to store artifacts')
            else:
                self.send_success(task)

