"""
Tests for clientlib/tasks

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import tempfile
import os
import shutil
import threading
import urllib2
import wsgiref.simple_server

from distci.frontend import frontend

from distci.distcilib import client

class BackgroundHttpServer:
    def __init__(self, server):
        self.server = server

    def serve(self):
        self.server.serve_forever()

class SilentWSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, *args):
        pass

class TestDistcilibClientTasks:
    app = None
    config_file = None
    data_directory = None
    test_state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(cls.data_directory, 'tasks'))

        frontend_config = { "data_directory": cls.data_directory }

        cls.frontend_app = frontend.Frontend(frontend_config)

        cls.server = wsgiref.simple_server.make_server('localhost', 8888, cls.frontend_app.handle_request, handler_class=SilentWSGIRequestHandler)

        cls.slave = BackgroundHttpServer(cls.server)
        cls.slave_thread = threading.Thread(target=cls.slave.serve)
        cls.slave_thread.start()

        client_config = { 'frontends': [ 'http://localhost:8888/' ],
                          'task_frontends' : [ 'http://localhost:8888/' ] }
        cls.client = client.Client(client_config)

        cls.state = { 'task_id': None }

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.slave_thread.join()
        shutil.rmtree(cls.data_directory)

    def test_01_list_tasks_empty(self):
        tasks = self.client.list_tasks()
        assert tasks is not None, "Empty result for tasks query"
        assert tasks.has_key('tasks'), "Missing tasks key in tasks reply"
        assert len(tasks['tasks']) == 0, "Non-zero task count when expecting empty set"

    def test_02_create_task(self):
        new_task_config = {'capabilityes':['test'], 'testdata': 'foobar'}
        task = self.client.create_task(new_task_config)
        assert task is not None, "failed to post new task"
        assert task.has_key('id'), "Reply is missing task_id"
        self.state['task_id'] = task['id']

    def test_03_list_tasks(self):
        tasks = self.client.list_tasks()
        assert tasks is not None, "Empty result for tasks query"
        assert tasks.has_key('tasks'), "Missing tasks key in tasks reply"
        assert len(tasks['tasks']) == 1, "Wrong count when expecting one task"

    def test_04_get_task(self):
        task = self.client.get_task(self.state['task_id'])
        assert task is not None, "failed to get task data"
        assert task['id'] == self.state['task_id'], "task ID mismatch"
        assert task['data'].get('testdata', '') == 'foobar', "task data mismatch"

    def test_05_delete_task(self):
        self.client.delete_task(self.state['task_id'])
        task = self.client.get_task(self.state['task_id'])
        assert task is None, "unexpected data return after task deletion"

