"""
Base worker object

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import uuid
import time
import random
import logging

from distci.distcilib import client

from . import task_base

class WorkerBase(object):
    def __init__(self, config):
        self.worker_config = config
        self.uuid = str(uuid.uuid4())
        self.log = logging.getLogger('WorkerBase')
        self.distci_client = client.Client(config)

    def fetch_task(self, timeout=None):
        start_timestamp = time.time()
        while True:
            tasks = self.distci_client.list_tasks(retries=1)
            if tasks is not None:
                random.shuffle(tasks['tasks'])
                for entry in tasks['tasks']:
                    self.log.debug('Entry: %r', entry)
                    task = task_base.GenericTask(entry['data'], entry['id'])
                    if task is None or task.config.get('assignee') is not None or task.config.get('status') != 'pending':
                        self.log.debug('Task %s is not for up to grabs' % entry['id'])
                        continue
                    if set(task.config['capabilities']) != set(task.config['capabilities']) & set(self.worker_config['capabilities']):
                        self.log.debug("Task %s doesn't match our capabilities", entry['id'])
                        continue
                    task.config['assignee'] = self.uuid
                    task.config['status'] = 'running'
                    if self.update_task(task):
                        return task
                    else:
                        self.log.debug("Failed to claim the task '%s'" % entry['id'])
            if timeout is not None:
                if time.time() < start_timestamp + timeout:
                    time.sleep(self.worker_config.get('poll_interval', 10))
                else:
                    break
        return None

    def get_task(self, task_id):
        task_data = self.distci_client.get_task(task_id,
                                                self.worker_config.get('retry_count', 10))
        if task_data is not None:
            return task_base.GenericTask(task_data, task_id)
        return None

    def update_task(self, task):
        task_data = self.distci_client.update_task(task.id,
                                                   task.config,
                                                   self.worker_config.get('retry_count', 10))
        if task_data is not None:
            return task_base.GenericTask(task_data['data'], task.id)
        return None

    def post_new_task(self, task):
        task_data = self.distci_client.create_task(task.config, self.worker_config.get('retry_count', 10))
        if task_data is not None:
            return task_base.GenericTask(task_data['data'], task.id)
        return None

