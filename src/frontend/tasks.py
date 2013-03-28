"""
Task management

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import uuid
import json
import shutil
import logging
import time

from . import validators, response, request, distlocks, constants

class Tasks(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('tasks')
        self.zknodes = config.get('zookeeper_nodes', [])
        if len(self.zknodes) == 0:
            self.zknodes = None

    def _data_dir(self):
        """ Return tasks directory """
        return os.path.join(self.config.get('data_directory'), 'tasks')

    def _task_dir(self, task_id):
        """ Return directory for specific task """
        return os.path.join(self._data_dir(), task_id)

    def _task_config_file(self, task_id):
        """ Return filename for task configuration """
        return os.path.join(self._task_dir(task_id), 'task.description')

    def _load_task_config(self, task_id):
        """ Load and parse task configuration file """
        return json.loads(file(self._task_config_file(task_id), 'rb').read())

    def _save_task_config(self, task_id, task_config):
        """ Serialize and store task configuration """
        file(self._task_config_file(task_id), 'wb').write(json.dumps(task_config))

    def _prepare_task_data(self, task_id):
        """ Format task configuration for HTTP replies """
        return {'id': task_id, 'data': self._load_task_config(task_id)}

    def get_tasks(self, start_response):
        """ Return information on all open tasks """
        result = { 'tasks': [] }
        task_ids = os.listdir(self._data_dir())
        for task_id in task_ids:
            if not os.path.isdir(self._task_dir(task_id)):
                continue
            task_data = None
            for _ in range(10):
                try:
                    task_data = self._prepare_task_data(task_id)
                    break
                except:
                    time.sleep(0.1)
            if task_data:
                result['tasks'].append(task_data)
        return response.send_response(start_response, 200, json.dumps(result))

    def create_new_task(self, environ, start_response):
        """ Post a new task """
        try:
            task_description = json.loads(request.read_request_data(environ))
        except ValueError:
            self.log.debug('Failed to load task data')
            return response.send_error(start_response, 400, constants.ERROR_TASK_INVALID_PAYLOAD)

        task_id_candidate = str(uuid.uuid4())
        os.mkdir(self._task_dir(task_id_candidate))
        self._save_task_config(task_id_candidate, task_description)
        return response.send_response(start_response, 201, json.dumps({'id': task_id_candidate, 'data': task_description}))

    def delete_task(self, start_response, task_id):
        """ Delete given task """
        if validators.validate_task_id(task_id) != task_id:
            return response.send_error(start_response, 400, constants.ERROR_TASK_INVALID_ID)
        if not os.path.isdir(self._task_dir(task_id)):
            return response.send_error(start_response, 404, constants.ERROR_TASK_NOT_FOUND)
        shutil.rmtree(self._task_dir(task_id))
        return response.send_response(start_response, 204)

    def get_task(self, start_response, task_id):
        """ Return information on a specific task """
        if validators.validate_task_id(task_id) != task_id:
            return response.send_error(start_response, 400, constants.ERROR_TASK_INVALID_ID)
        if not os.path.isdir(self._task_dir(task_id)):
            return response.send_error(start_response, 404, constants.ERROR_TASK_NOT_FOUND)
        task_data = None
        for _ in range(10):
            try:
                task_data = json.dumps(self._prepare_task_data(task_id))
                break
            except:
                time.sleep(0.1)
        if not task_data:
            return response.send_error(start_response, 409, constants.ERROR_TASK_LOCKED)
        return response.send_response(start_response, 200, task_data)

    def update_task(self, environ, start_response, task_id):
        """ Update data configuration for an existing task """
        if validators.validate_task_id(task_id) != task_id:
            self.log.error("Failed to pass validation: '%s'" % task_id)
            return response.send_error(start_response, 400, constants.ERROR_TASK_INVALID_ID)
        if not os.path.isdir(self._task_dir(task_id)):
            self.log.debug("Task not found '%s'" % task_id)
            return response.send_error(start_response, 404, constants.ERROR_TASK_NOT_FOUND)
        try:
            new_task_description = json.loads(request.read_request_data(environ))
        except ValueError:
            self.log.error("Decoding task data failed '%s'" % task_id)
            return response.send_error(start_response, 400, constants.ERROR_TASK_INVALID_PAYLOAD)
        if self.zknodes:
            lock = distlocks.ZooKeeperLock(self.zknodes, 'task-lock-%s' % task_id)
            if lock.try_lock() != True:
                lock.close()
                self.log.debug("Task locked '%s'" % task_id)
                return response.send_response(start_response, 409, constants.ERROR_TASK_LOCKED)
        else:
            lock = None
        try:
            old_task_description = self._load_task_config(task_id)
        except:
            if lock:
                lock.unlock()
                lock.close()
            self.log.error("Failed to read task data '%s'" % task_id)
            return response.send_response(start_response, 500)
        if old_task_description.has_key('assignee') and new_task_description.has_key('assignee') and old_task_description['assignee'] != new_task_description['assignee']:
            if lock:
                lock.unlock()
                lock.close()
            self.log.debug("Task assignment conflict '%s'" % task_id)
            return response.send_response(start_response, 409, constants.ERROR_TASK_WRONG_ACTOR)
        self._save_task_config(task_id, new_task_description)
        if lock:
            lock.unlock()
            lock.close()
        return response.send_response(start_response, 200, json.dumps({'id': task_id, 'data': new_task_description}))

    def handle_request(self, environ, start_response, method, parts):
        """ Parse and dispatch task API requests """
        self.log.debug('%s %r' % (method, parts))
        if len(parts) == 0:
            if method == 'GET':
                retval = self.get_tasks(start_response)
            elif method == 'POST':
                retval = self.create_new_task(environ, start_response)
            else:
                retval = response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'GET':
                retval = self.get_task(start_response, parts[0])
            elif method == 'PUT':
                retval = self.update_task(environ, start_response, parts[0])
            elif method == 'DELETE':
                retval = self.delete_task(start_response, parts[0])
            else:
                retval = response.send_error(start_response, 400)
        else:
            retval = response.send_error(start_response, 400)
        return retval

