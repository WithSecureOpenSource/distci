"""
Copy artifacts worker

Copy artifacts from an another job for build chaining

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import fnmatch

from distci.worker import worker_base
from distci import distcilib

class CopyArtifactsWorker(worker_base.WorkerBase):
    """ Copy artifacts worker """

    def __init__(self, config):
        worker_base.WorkerBase.__init__(self, config)
        self.worker_config['capabilities'] = ['copy_artifacts_v1']
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
            if not task.config.get('params'):
                self.send_failure(task, 'Parameters not specified')
                continue

            source_job_name = task.config['params'].get('job')
            source_artifacts = task.config['params'].get('artifacts')
            target_path = task.config['params'].get('target_directory')

            if source_job_name is None:
                self.send_failure(task, 'Job name not specified')

            if source_artifacts is None:
                self.send_failure(task, 'Artifacts not specified')
                continue

            # 1. Locate latest successful build
            last_successful_build = 0
            all_builds = self.distci_client.builds.list(source_job_name)
            if all_builds is not None:
                for build in sorted(all_builds.get('builds', []), reverse=True):
                    state = self.distci_client.builds.state.get(source_job_name, build)
                    if state is not None and state.get('state', {}).get('status') == 'complete' and state.get('state', {}).get('result') == 'success':
                        last_successful_build = build
                        break
                if last_successful_build == 0:
                    self.send_failure(task, 'Unable to locate a successful build')
                    continue
            else:
                self.send_failure(task, 'Unable to locate builds')
                continue

            # 2. glob through build artifacts
            artifacts = state['state'].get('artifacts', {})
            artifacts_to_copy = {}
            for artifact_id, artifact_path in artifacts.iteritems():
                path = '/'.join(artifact_path)
                for source_artifact in source_artifacts:
                    if fnmatch.fnmatch(path, source_artifact):
                        if target_path is not None:
                            path = os.path.join(target_path, path)
                        artifacts_to_copy[artifact_id] = path

            if len(artifacts_to_copy) > 0:
                # 3. Fetch and unpack workspace
                workspace = self.fetch_workspace(task.config['job_id'],
                                                 task.config['build_number'])
                if workspace is None:
                    self.send_failure(task, 'Failed to fetch workspace')
                    continue

                log = '%sCopying artifacts from %s build %d\n' % (log, source_job_name, last_successful_build)

                # 4. Download the requested artifacts
                for artifact_id, artifact_target_path in artifacts_to_copy.iteritems():
                    abspath = os.path.abspath(os.path.join(workspace, artifact_target_path))
                    dirname = os.path.dirname(abspath)
                    try:
                        os.makedirs(dirname)
                    except:
                        pass
                    fobj = file(abspath, 'wb')
                    self.distci_client.builds.artifacts.get(source_job_name, last_successful_build, artifact_id, fobj)
                    fobj.close()
                    log = '%s  %s\n' % (log, artifact_target_path)

                # 5. send workspace
                if self.send_workspace(task.config['job_id'],
                                       task.config['build_number'],
                                       workspace) == False:
                    self.log.debug('Sending workspace failed')
                    self.send_failure(task, 'Failed to fetch workspace')
                    continue

            # 4. push console log
            for _ in range(self.worker_config.get('retry_count', 10)):
                if self.distci_client.builds.console.append(task.config['job_id'],
                                                            task.config['build_number'],
                                                            log) == True:
                    break

            # 5. update task state
            self.send_success(task)

