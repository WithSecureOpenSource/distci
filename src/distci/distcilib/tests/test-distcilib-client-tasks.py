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
import json

from distci import frontend

from distci import distcilib

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
        frontend_config_file = os.path.join(cls.data_directory, 'frontend.conf')
        os.mkdir(os.path.join(cls.data_directory, 'tasks'))

        frontend_config = { "data_directory": cls.data_directory }
        json.dump(frontend_config, file(frontend_config_file, 'wb'))

        cls.frontend_app = frontend.Frontend(frontend_config)

        cls.server = wsgiref.simple_server.make_server('localhost', 0, cls.frontend_app, handler_class=SilentWSGIRequestHandler)
        cls.server_port = cls.server.socket.getsockname()[1]

        cls.slave = BackgroundHttpServer(cls.server)
        cls.slave_thread = threading.Thread(target=cls.slave.serve)
        cls.slave_thread.start()

        client_config = { 'frontends': [ 'http://localhost:%d/' % cls.server_port ],
                          'task_frontends' : [ 'http://localhost:%d/' % cls.server_port ] }
        cls.client = distcilib.DistCIClient(client_config)

        cls.state = { }

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.slave_thread.join()
        shutil.rmtree(cls.data_directory)

    def test_01_list_tasks_empty(self):
        tasks = self.client.tasks.list()
        assert tasks is not None, "Empty result for tasks query"
        assert tasks.has_key('tasks'), "Missing tasks key in tasks reply"
        assert len(tasks['tasks']) == 0, "Non-zero task count when expecting empty set"

    def test_02_create_task(self):
        task_id = self.client.tasks.create()
        assert task_id is not None, "failed to post new task"
        self.state['task_id'] = task_id

    def test_03_list_tasks(self):
        tasks = self.client.tasks.list()
        assert tasks is not None, "Empty result for tasks query"
        assert tasks.has_key('tasks'), "Missing tasks key in tasks reply"
        assert len(tasks['tasks']) == 1, "Wrong count when expecting one task"

    def test_04_get_task(self):
        task_descr = self.client.tasks.get(self.state['task_id'])
        assert task_descr is not None, "Failed to get task data"
        assert task_descr.get('status') == 'preparing', "Task data mismatch"

    def test_05_update_task(self):
        new_task_config = {'capabilities':['test'], 'testdata': 'foobar', 'status': 'pending'}
        task_descr = self.client.tasks.update(self.state['task_id'], new_task_config)
        assert task_descr is not None, "Failed to update task data"
        assert task_descr.get('testdata') == 'foobar', "Task data mismatch, %r" % task_descr

        task_descr = self.client.tasks.get(self.state['task_id'])
        assert task_descr is not None, "Failed to update task data"
        assert task_descr.get('testdata') == 'foobar', "Task data mismatch, %r" % task_descr

    def test_06_delete_task(self):
        self.client.tasks.delete(self.state['task_id'])
        task_descr = self.client.tasks.get(self.state['task_id'])
        assert task_descr is None, "Unexpected data return after task deletion"

