"""
Base worker object

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import uuid
import httplib
import urlparse
import random
import json
import time
import logging

from . import task_base

class WorkerBase(object):
    def __init__(self):
        self.worker_config = None
        self.uuid = str(uuid.uuid4())
        self.log = logging.getLogger('WorkerBase')

    def _create_task_url_components(self, base_url, task_id=None):
        if task_id is None:
            url = urlparse.urljoin(base_url, 'tasks')
        else:
            url = urlparse.urljoin(base_url, 'tasks/%s' % task_id)
        parsed = urlparse.urlsplit(url)
        return (parsed.netloc, parsed.path)

    def _get_task_list(self, base_url):
        host, path = self._create_task_url_components(base_url)
        conn = httplib.HTTPConnection(host)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
        except:
            raise
        if response.status != 200:
            return None

        try:
            tasks = json.loads(response.read())['tasks']
        except:
            raise

        return tasks

    def _post_new_task(self, base_url, task):
        host, path = self._create_task_url_components(base_url)
        data_str = task.dumps()

        headers = { "Content-Type": "application/json",
                    "Content-Length": str(len(data_str)) }

        conn = httplib.HTTPConnection(host)
        try:
            conn.request("POST", path, data_str, headers)
            response = conn.getresponse()
        except:
            raise

        if response.status != 201:
            return None

        try:
            task = json.loads(response.read())
        except:
            raise

        return task

    def _update_task(self, base_url, task_id, task):
        host, path = self._create_task_url_components(base_url, task_id)
        data_str = task.dumps()

        headers = { "Content-Type": "application/json",
                    "Content-Length": str(len(data_str)) }

        conn = httplib.HTTPConnection(host)
        try:
            conn.request("PUT", path, data_str, headers)
            response = conn.getresponse()
        except:
            raise

        if response.status != 200:
            return None

        try:
            task = json.loads(response.read())
        except:
            raise

        return task

    def fetch_task(self, timeout=None):
        start_timestamp = time.time()
        while timeout is None or time.time() < start_timestamp + timeout:
            random.shuffle(self.worker_config['frontends'])
            tasks = self._get_task_list(self.worker_config['frontends'][0])
            if tasks is not None:
                random.shuffle(tasks)
                for entry in tasks:
                    task = task_base.GenericTask(entry['data'])
                    if task is None or task.config.get('assignee') is not None or task.config.get('status') != 'pending':
                        self.log.debug('Task %s is not for up to grabs' % entry['id'])
                        continue
                    if set(task.config['capabilities']) != set(task.config['capabilities']) & set(self.worker_config['capabilities']):
                        self.log.debug("Task %s doesn't match our capabilities")
                        continue
                    task.config['assignee'] = self.uuid
                    task.config['status'] = 'running'
                    task.id = entry['id']
                    if self._update_task(self.worker_config['frontends'][0], entry['id'], task):
                        return task
                    else:
                        self.log.debug("Failed to claim the task '%s'" % entry['id'])
            if timeout is not None or time.time() >= start_timestamp + timeout:
                time.sleep(self.worker_config.get('poll_interval', 10))
        return None

    def update_task(self, task):
        for _ in range(self.worker_config.get('retry_count', 30)):
            random.shuffle(self.worker_config['frontends'])
            if self._update_task(self.worker_config['frontends'][0], task.id, task):
                return True
            time.sleep(self.worker_config.get('poll_interval', 10))
        return False

    def post_new_task(self, task):
        task_id = None
        for _ in range(self.worker_config.get('retry_count', 30)):
            random.shuffle(self.worker_config['frontends'])
            if task_id is None:
                task.config['status'] = 'creating'
                task_data = self._post_new_task(self.worker_config['frontends'][0], task)
                if task_data is not None:
                    task_id = task_data['id']
                    task.config['status'] = 'pending'
            if task_id is not None:
                if self._update_task(self.worker_config['frontends'][0], task_id, task):
                    task.id = task_id
                    return task_id
            time.sleep(self.worker_config.get('poll_interval', 10))
        return None

