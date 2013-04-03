"""
Task operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import time
import json

class Client(object):
    """ Client class for accessing task frontends """
    def __init__(self, parent):
        self.parent = parent

    def list(self):
        """ list all tasks """
        try:
            code, data = self.parent.rest.do_task_request('GET',
                                                          None)
        except:
            self.parent.log.exception('Failed to fetch list of task')
            return None

        if code != 200:
            self.parent.log.error('List tasks failed with HTTP code %d', code)
            return None

        try:
            return json.loads(data)
        except (TypeError, ValueError):
            self.parent.log.exception('Failed to decode reply to list tasks')
            return None

    def get(self, task_id):
        """ get info on single task """
        self.parent.log.debug('GET TASK FOR %s', task_id)
        try:
            code, data = self.parent.rest.do_task_request('GET',
                                                          task_id)
        except:
            self.parent.log.exception('Failed to fetch task %s', task_id)
            return None

        if code != 200:
            self.parent.log.error('Fetch task %s failed with HTTP code %d', task_id, code)
            return None

        try:
            return json.loads(data)['data']
        except (TypeError, ValueError, KeyError):
            self.parent.log.exception('Failed to decode reply to get task %s', task_id)
            return None

    def create(self):
        """ create a new task """
        task_description = { 'status': 'preparing',
                             'timestamp': int(time.time()) }
        try:
            code, data = self.parent.rest.do_task_request('POST',
                                                          None,
                                                          data=json.dumps(task_description))
        except:
            self.parent.log.exception('Failed to create task')
            return None

        if code != 201:
            self.parent.log.error('Create task failed with HTTP code %d', code)
            return None

        try:
            return json.loads(data)['id']
        except (TypeError, ValueError, KeyError):
            self.parent.log.exception('Failed to decode reply to task creation')
            return None

    def update(self, task_id, task_description):
        """ update an existing task """
        try:
            code, data = self.parent.rest.do_task_request('PUT',
                                                          task_id,
                                                          data=json.dumps(task_description))
        except:
            self.parent.log.exception('Failed to update task %s', task_id)
            return None

        if code != 200:
            self.parent.log.error('Update task failed with HTTP code %d', code)
            return None

        try:
            return json.loads(data)['data']
        except (TypeError, ValueError, KeyError):
            self.parent.log.exception('Failed to decode reply to task update')
            return None

    def delete(self, task_id):
        """ Delete a task """
        try:
            code, data = self.parent.rest.do_task_request('DELETE',
                                                          task_id)
        except:
            self.parent.log.exception('Failed to delete task %s', task_id)
            return False

        if code != 204 or code != 404:
            self.parent.log.error('Delete task %s failed with HTTP code %d', task_id, code)
            return False

        return True


