"""
Client library for accessing DistCI

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import httplib
import urlparse
import random
import json
import logging

class Client(object):
    """ Client class for accessing DistCI """
    def __init__(self, client_config):
        self.client_config = client_config
        self.log = logging.getLogger('DistCIClient')

    def _do_get_request(self, base_url, command):
        """ Internal helper for HTTP GET requests """
        parsed = urlparse.urlsplit(base_url)
        resource = urlparse.urljoin(parsed.path, command)
        conn = httplib.HTTPConnection(parsed.netloc)
        conn.request("GET", resource)
        response = conn.getresponse()
        if response.status >= 200 and response.status < 300:
            return response.status, response.read()
        else:
            return response.status, None

    def _do_post_request(self, base_url, command, data=None):
        """ Internal helper for HTTP POST requests """
        parsed = urlparse.urlsplit(base_url)
        resource = urlparse.urljoin(parsed.path, command)
        conn = httplib.HTTPConnection(parsed.netloc)
        if data is not None:
            headers = { "Content-Type": "application/json",
                        "Content-Length": str(len(data)) }
            conn.request("POST", resource, data, headers)
        else:
            conn.request("POST", resource)
        response = conn.getresponse()
        if response.status >= 200 and response.status < 300:
            return response.status, response.read()
        else:
            return response.status, None

    def _do_put_request(self, base_url, command, data=None):
        """ Internal helper for HTTP PUT requests """
        parsed = urlparse.urlsplit(base_url)
        resource = urlparse.urljoin(parsed.path, command)
        conn = httplib.HTTPConnection(parsed.netloc)
        if data is not None:
            headers = { "Content-Type": "application/json",
                        "Content-Length": str(len(data)) }
            conn.request("PUT", resource, data, headers)
        else:
            conn.request("PUT", resource)
        response = conn.getresponse()
        if response.status >= 200 and response.status < 300:
            return response.status, response.read()
        else:
            return response.status, None

    def _do_delete_request(self, base_url, command):
        """ Internal helper for HTTP DELETE requests """
        parsed = urlparse.urlsplit(base_url)
        resource = urlparse.urljoin(parsed.path, command)
        conn = httplib.HTTPConnection(parsed.netloc)
        conn.request("DELETE", resource)
        response = conn.getresponse()
        if response.status >= 200 and response.status < 300:
            return response.status, response.read()
        else:
            return response.status, None

    def _create_task_command(self, task_id=None):
        """ Create URL path related to task requests """
        if task_id is None:
            return 'tasks'
        else:
            return 'tasks/%s' % task_id

    def _create_job_command(self, job_id=None):
        """ Create URL path related to job requests """
        if job_id is None:
            return 'jobs'
        else:
            return 'jobs/%s' % job_id

    def _create_build_command(self, job_id, build_id=None):
        """ Create URL path related to build requests """
        if build_id is None:
            return '%s/builds' % self._create_job_command(job_id)
        else:
            return '%s/builds/%s' % (job_id, build_id)

    def _get_task_list(self):
        """ Intenal implementation for getting list of tasks """
        base_url = random.choice(self.client_config['task_frontends'])
        command = self._create_task_command()
        try:
            code, data = self._do_get_request(base_url, command)
        except:
            return None
        if code == 200 and data is not None:
            try:
                result = json.loads(data)
            except:
                return None
            return result
        else:
            return None

    def _get_task(self, task_id):
        """ Internal call for getting a single task data """
        base_url = random.choice(self.client_config['task_frontends'])
        command = self._create_task_command(task_id)
        try:
            code, data = self._do_get_request(base_url, command)
        except:
            return None
        if code == 200 and data is not None:
            try:
                result = json.loads(data)
            except:
                return None
            return result
        else:
            return None

    def _create_new_task(self):
        """ Internal call for creating a new task """
        base_url = random.choice(self.client_config['task_frontends'])
        command = self._create_task_command()
        task_data = json.dumps({"status": "creating"})
        try:
            code, data = self._do_post_request(base_url, command, task_data)
        except:
            return None
        if code == 201 and data is not None:
            try:
                result = json.loads(data)
            except:
                return None
            return result
        else:
            return None

    def _update_task(self, task_id, task_description):
        """ Internal call for updating a single task """
        base_url = random.choice(self.client_config['task_frontends'])
        command = self._create_task_command(task_id)
        task_data = json.dumps(task_description)
        try:
            code, data = self._do_put_request(base_url, command, task_data)
        except:
            return None
        if code == 200 and data is not None:
            try:
                result = json.loads(data)
            except:
                return None
            return result
        else:
            return None

    def _delete_task(self, task_id):
        """ Internal call for deleting a single task """
        base_url = random.choice(self.client_config['task_frontends'])
        command = self._create_task_command(task_id)
        try:
            code, _ = self._do_delete_request(base_url, command)
        except:
            return False
        if code == 204:
            return True
        else:
            return False

    def list_tasks(self, retries=10):
        """ Get list of posted tasks """
        for _ in range(retries):
            tasks = self._get_task_list()
            if tasks is not None:
                return tasks
        return None

    def get_task(self, task_id, retries=10):
        """ Get contents of single task """
        for _ in range(retries):
            task = self._get_task(task_id)
            if task is not None:
                return task
        return None

    def create_task(self, task_description, retries=10):
        """ Post a new task """
        task_id = None
        for _ in range(retries):
            if task_id is None:
                task_data = self._create_new_task()
                if task_data is not None and task_data.has_key('id'):
                    task_id = task_data['id']
            if task_id is not None:
                task_data = self._update_task(task_id, task_description)
                if task_data is not None:
                    return task_data
        return None

    def update_task(self, task_id, task_description, retries=10):
        """ Update task contents """
        for _ in range(retries):
            task_data = self.update_task(task_id, task_description)
            if task_data is not None:
                return task_data
        return None

    def delete_task(self, task_id, retries=10):
        """ Delete an existing task """
        for _ in range(retries):
            task_success = self._delete_task(task_id)
            if task_success == True:
                return True
        return False

