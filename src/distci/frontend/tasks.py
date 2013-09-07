"""
Task management

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import uuid
import json
import logging
import webob

from distci.frontend import validators, sync, constants

class Tasks(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('tasks')
        self.zknodes = config.get('zookeeper_nodes', [])
        if len(self.zknodes) == 0:
            self.zknodes = None
        else:
            zk = sync.ZooKeeperData(self.zknodes)
            zk.set('/distci', '')
            zk.set('/distci/tasks', '')
            zk.close()

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

    def get_tasks(self):
        """ Return information on all open tasks """
        if self.zknodes:
            data_conn = sync.ZooKeeperData(self.zknodes, '/distci/tasks')
        else:
            data_conn = sync.FSData(self._data_dir())

        result = {'tasks': data_conn.list() }
        data_conn.close()
        return webob.Response(status=200, body=json.dumps(result), content_type="application/json")


    def create_new_task(self, request):
        """ Post a new task """
        try:
            task_description = json.load(request.body_file)
        except ValueError:
            self.log.error('Failed to load task data')
            return webob.Response(status=400, body=constants.ERROR_TASK_INVALID_PAYLOAD)

        task_id_candidate = str(uuid.uuid4())
        if self.zknodes:
            data_conn = sync.ZooKeeperData(self.zknodes, '/distci/tasks')
        else:
            data_conn = sync.FSData(self._data_dir())

        if data_conn.set('/%s' % task_id_candidate, json.dumps(task_description)) == True:
            data_conn.close()
            return webob.Response(status=201, body=json.dumps({'id': task_id_candidate, 'data': task_description}), content_type="application/json")
        else:
            data_conn.close()
            # FIXME: error code
            return webob.Response(status=500, body=constants.ERROR_TASK_LOCKED)

    def delete_task(self, task_id):
        """ Delete given task """
        if self.zknodes:
            data_conn = sync.ZooKeeperData(self.zknodes, '/distci/tasks')
        else:
            data_conn = sync.FSData(self._data_dir())
        data_conn.delete('/%s' % task_id)
        data_conn.close()
        return webob.Response(status=204)

    def get_task(self, task_id):
        """ Return information on a specific task """
        if self.zknodes:
            data_conn = sync.ZooKeeperData(self.zknodes, '/distci/tasks')
        else:
            data_conn = sync.FSData(self._data_dir())

        task_data = data_conn.get('/%s' % task_id)
        if task_data is None:
            data_conn.close()
            return webob.Response(status=404, body=constants.ERROR_TASK_NOT_FOUND)
        data_conn.close()
        returned_data = {'id': task_id, 'data': json.loads(task_data) }
        return webob.Response(status=200, body=json.dumps(returned_data), content_type="application/json")

    def update_task(self, request, task_id):
        """ Update data configuration for an existing task """
        if self.zknodes:
            data_conn = sync.ZooKeeperData(self.zknodes, '/distci/tasks')
        else:
            data_conn = sync.FSData(self._data_dir())

        task_data = data_conn.get('/%s' % task_id)
        if task_data is None:
            return webob.Response(status=404, body=constants.ERROR_TASK_NOT_FOUND)

        try:
            new_task_description = json.load(request.body_file)
        except ValueError:
            self.log.error("Decoding task data failed '%s'" % task_id)
            data_conn.close()
            return webob.Response(status=400, body=constants.ERROR_TASK_INVALID_PAYLOAD)
        try:
            old_task_description = json.loads(task_data)
        except:
            self.log.error("Failed to read task data '%s'" % task_id)
            data_conn.close()
            return webob.Response(status=500)
        if old_task_description.has_key('assignee') and new_task_description.has_key('assignee') and old_task_description['assignee'] != new_task_description['assignee']:
            data_conn.close()
            self.log.info("Task assignment conflict '%s'" % task_id)
            return webob.Response(status=409, body=constants.ERROR_TASK_WRONG_ACTOR)
        if data_conn.set('/%s' % task_id, json.dumps(new_task_description), task_data) == False:
            data_conn.close()
            return webob.Response(status=409, body=constants.ERROR_TASK_LOCKED)

        data_conn.close()
        return webob.Response(status=200, body=json.dumps({'id': task_id, 'data': new_task_description}), content_type="application/json")

    def handle_request(self, request, parts):
        """ Parse and dispatch task API requests """
        if len(parts) == 0:
            if request.method == 'GET':
                return self.get_tasks()
            elif request.method == 'POST':
                return self.create_new_task(request)
        elif len(parts) == 1:
            if validators.validate_task_id(parts[0]) != parts[0]:
                return webob.Response(status=400, body=constants.ERROR_TASK_INVALID_ID)

            if request.method == 'GET':
                return self.get_task(parts[0])
            elif request.method == 'PUT':
                return self.update_task(request, parts[0])
            elif request.method == 'DELETE':
                return self.delete_task(parts[0])

        return webob.Response(status=400)

