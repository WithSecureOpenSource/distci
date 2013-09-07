"""
Base worker object

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import uuid
import time
import random
import logging
import tempfile
import tarfile
import os
import shutil

from distci import distcilib

from . import task_base

class WorkerBase(object):
    def __init__(self, config):
        self.worker_config = config
        self.uuid = str(uuid.uuid4())
        self.log = logging.getLogger('WorkerBase')
        self.distci_client = distcilib.DistCIClient(config)

    def fetch_task(self, timeout=None):
        start_timestamp = time.time()
        while True:
            tasks = self.list_tasks()
            if tasks is not None:
                random.shuffle(tasks['tasks'])
                for task_id in tasks['tasks']:
                    self.log.debug('Task: %r', task_id)
                    task = self.get_task(task_id)
                    if task is None or task.config.get('assignee') is not None or task.config.get('status') != 'pending':
                        self.log.debug('Task %s is not for up to grabs' % task_id)
                        continue
                    if not set(task.config['capabilities']).issubset(set(self.worker_config['capabilities'])):
                        self.log.debug("Task %s doesn't match our capabilities", task_id)
                        continue
                    task.config['assignee'] = self.uuid
                    task.config['status'] = 'running'
                    if self.update_task(task):
                        return task
                    else:
                        self.log.debug("Failed to claim the task '%s'" % task_id)
            if timeout is not None:
                if time.time() < start_timestamp + timeout:
                    time.sleep(self.worker_config.get('poll_interval', 10))
                else:
                    break
        return None

    def list_tasks(self):
        for _ in range(self.worker_config.get('retry_count', 10)):
            tasks = self.distci_client.tasks.list()
            if tasks is not None:
                return tasks
        return None

    def get_task(self, task_id):
        for _ in range(self.worker_config.get('retry_count', 10)):
            task_descr = self.distci_client.tasks.get(task_id)
            if task_descr is not None:
                return task_base.GenericTask(task_descr, task_id)
        return None

    def update_task(self, task):
        for _ in range(self.worker_config.get('retry_count', 10)):
            task_descr = self.distci_client.tasks.update(task.id,
                                                         task.config)
            if task_descr is not None:
                return task_base.GenericTask(task_descr, task.id)
        return None

    def post_new_task(self, task):
        task_id = None
        for _ in range(self.worker_config.get('retry_count', 10)):
            if task_id is None:
                task_id = self.distci_client.tasks.create()
            if task_id is not None:
                task_descr = self.distci_client.tasks.update(task_id, task.config)
                if task_descr is not None:
                    return task_base.GenericTask(task_descr, task_id)
        return None

    def fetch_workspace(self, job_id, build_id):
        archive = None
        for _ in range(self.worker_config.get('retry_count', 10)):
            archive = tempfile.TemporaryFile()
            if self.distci_client.builds.workspace.get(job_id, build_id, archive) == True:
                break
            archive.close()
            archive = None

        if archive is None:
            return None

        archive.seek(0)
        wsdir = tempfile.mkdtemp()
        tarf = tarfile.open(fileobj=archive, mode='r')
        for member in tarf.getmembers():
            absname = os.path.abspath(os.path.join(wsdir, member.name))
            if ((not absname.startswith('%s%s' % (wsdir, os.path.sep))) or
                (not (member.isreg() or member.issym() or member.isdir()))):
                tarf.close()
                archive.close()
                shutil.rmtree(wsdir)
                return None

        tarf.extractall(wsdir)
        tarf.close()
        archive.close()

        return wsdir

    def send_workspace(self, job_id, build_id, workspace):
        archive = tempfile.TemporaryFile()
        tarf = tarfile.open(fileobj=archive, mode='w:gz')

        for root_file in os.listdir(workspace):
            tarf.add(os.path.join(workspace, root_file), root_file)

        tarf.close()
        ws_len = archive.tell()
        self.log.debug('Workspace archive size: %d', ws_len)

        for _ in range(self.worker_config.get('retry_count', 10)):
            archive.seek(0)
            if self.distci_client.builds.workspace.put(job_id, build_id, archive, ws_len) == True:
                archive.close()
                return True
        archive.close()
        return False

    def delete_workspace(self, workspace):
        try:
            shutil.rmtree(workspace)
        except OSError:
            return False
        return True

