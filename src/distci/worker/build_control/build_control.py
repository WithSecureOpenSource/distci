"""
Build control worker: cruise through build steps and dispatch
                      tasks to perform the actual build

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

# TODO: this implementation is rather naive, and needs to be refactored
# TODO: this implementation is rather complex, and needs to be refactored

import time
import tempfile
import copy

from distci.worker import worker_base, task_base

class BuildControlWorker(worker_base.WorkerBase):
    """ Build control worker """
    def __init__(self, config):
        worker_base.WorkerBase.__init__(self, config)
        self.worker_config['capabilities'] = ['build_control_v1']
        self.build_states = {}

    def update_build_state(self, task_key):
        self.build_states[task_key]['last_updated'] = int(time.time())
        for _ in range(self.worker_config.get('retry_count', 10)):
            if self.distci_client.builds.state.put(self.build_states[task_key]['job_id'], self.build_states[task_key]['build_number'], self.build_states[task_key]['build_state']) is not None:
                return True

        self.log.error('Failed to update build state, job %s build %s' % (self.build_states[task_key]['job_id'], self.build_states[task_key]['build_number']))
        return False

    def prepare_build(self, task_key):
        self.log.debug('Prepare build %s', task_key)
        # fetch and store job configuration
        if self.build_states[task_key].get('job_config') is None:
            for _ in range(self.worker_config.get('retry_count', 10)):
                config = self.distci_client.jobs.get(self.build_states[task_key]['job_id'])
                if config is not None and config.get('config') is not None:
                    self.build_states[task_key]['job_config'] = config['config']
                    self.build_states[task_key]['build_state']['config'] = config['config']
                    break

            if self.build_states[task_key].get('job_config') is None:
                self.log.error('Failed to fetch job config')
                return

        # update build state
        if self.update_build_state(task_key) == False:
            return

        # create and store empty workspace
        self.log.debug('Creating workspace')
        tmp_dir = tempfile.mkdtemp()

        if self.send_workspace(self.build_states[task_key]['job_id'], self.build_states[task_key]['build_number'], tmp_dir) == True:
            self.delete_workspace(tmp_dir)
            self.build_states[task_key]['state'] = 'running'
        else:
            self.log.error('Failed to store empty workspace')
            self.delete_workspace(tmp_dir)

    def spawn_subtask(self, task_key, subtask_index):
        subtask_config = self.build_states[task_key]['job_config']['tasks'][subtask_index]
        if subtask_config['type'] == 'git-checkout':
            capabilities = [ 'git_checkout_v1' ]
        elif subtask_config['type'] == 'execute-shell':
            capabilities = [ 'execute_shell_v1' ]
            for label in subtask_config['params'].get('nodelabels', []):
                capabilities.append('nodelabel_%s' % label)
        elif subtask_config['type'] == 'publish-artifacts':
            capabilities = [ 'publish_artifacts_v1' ]
        else:
            self.build_states[task_key]['build_state']['tasks'].append({
                'status': 'complete',
                'result': 'error',
                'error_message': 'Unknown subtask type %s' % subtask_config['type'] })
            return

        task_descr = { 'status': 'pending',
                       'job_id': self.build_states[task_key]['job_id'],
                       'build_number': self.build_states[task_key]['build_number'],
                       'capabilities': capabilities,
                       'params': copy.deepcopy(self.build_states[task_key]['job_config']['tasks'][subtask_index]['params']) }

        task_obj = task_base.GenericTask(task_descr, None)
        task_obj = self.post_new_task(task_obj)
        if task_obj is None:
            self.log.error('Failed to post new task for job %s build %s', self.build_states[task_key]['job_id'], self.build_states[task_key]['build_number'])
            return

        self.build_states[task_key]['build_state']['tasks'][subtask_index] = task_obj.config
        self.build_states[task_key]['build_state']['tasks'][subtask_index]['id'] = task_obj.id

        if self.update_build_state(task_key) == False:
            return

    def update_state_after_subtask_completion(self, task_key, subtask_index):
        artifacts = self.build_states[task_key]['build_state']['tasks'][subtask_index].get('artifacts')
        if artifacts is not None:
            for artifact_id, path in artifacts.iteritems():
                self.build_states[task_key]['build_state']['artifacts'][artifact_id] = path

    def check_status_and_issue_tasks(self, task_key):
        self.log.debug('Checking status for %s', task_key)
        for subtask_index in range(len(self.build_states[task_key]['job_config']['tasks'])):
            subtask_desc = self.build_states[task_key]['build_state']['tasks'].get(subtask_index)
            if subtask_desc is None:
                if self.spawn_subtask(task_key, subtask_index) == False:
                    return
            subtask_desc = self.build_states[task_key]['build_state']['tasks'][subtask_index]
            if subtask_desc['status'] != 'complete':
                subtask = self.get_task(subtask_desc['id'])
                if subtask is not None:
                    self.build_states[task_key]['build_state']['tasks'][subtask_index].update(subtask.config)
            if subtask_desc['status'] != 'complete':
                return
            if subtask_desc['result'] != 'success':
                self.build_states[task_key]['state'] = 'complete'
                self.build_states[task_key]['build_state']['status'] = 'complete'
                self.build_states[task_key]['build_state']['result'] = 'failure'
                return
            self.update_state_after_subtask_completion(task_key, subtask_index)
        self.build_states[task_key]['state'] = 'complete'
        self.build_states[task_key]['build_state']['status'] = 'complete'
        self.build_states[task_key]['build_state']['result'] = 'success'

    def report_complete_status(self, task_key):
        # delete workspace
        for _ in range(self.worker_config.get('retry_count', 10)):
            if self.distci_client.builds.workspace.delete(self.build_states[task_key]['job_id'], self.build_states[task_key]['build_number']) == True:
                break

        if self.update_build_state(task_key) == False:
            return

        # clean up subtasks
        for _, subtask_data in self.build_states[task_key]['build_state']['tasks'].iteritems():
            if subtask_data['id'] is not None:
                for _ in range(self.worker_config.get('retry_count', 10)):
                    if self.distci_client.tasks.delete(subtask_data['id']) == True:
                        subtask_data['id'] = None
                        break
            if subtask_data['id'] is not None:
                return

        # delete our main task
        task = self.build_states[task_key]['task']
        for _ in range(self.worker_config.get('retry_count', 10)):
            if self.distci_client.tasks.delete(task.id) == True:
                task.id = None
                break
        if task.id is not None:
            return

        self.build_states[task_key]['state'] = 'reported'

    def start(self):
        while True:
            new_task = self.fetch_task(timeout=10)

            if new_task is not None:
                self.build_states[new_task.id] = {
                    'state': 'prepare',
                    'last_updated': int(time.time()),
                    'job_id': new_task.config.get('job_id'),
                    'build_number': new_task.config.get('build_number'),
                    'build_state': {
                        'status': 'running',
                        'controller': self.uuid,
                        'tasks': {},
                        'artifacts': {} },
                    'task': new_task }

            for task_key in self.build_states.keys():
                if self.build_states[task_key]['state'] == 'prepare':
                    self.prepare_build(task_key)

                if self.build_states[task_key]['state'] == 'running':
                    self.check_status_and_issue_tasks(task_key)

                if self.build_states[task_key]['state'] == 'complete':
                    self.report_complete_status(task_key)

                if self.build_states[task_key]['state'] == 'reported':
                    del self.build_states[task_key]

