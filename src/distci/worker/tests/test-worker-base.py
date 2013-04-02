"""
Tests for basic worker tasks

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import tempfile
import os
import shutil
import threading
import urllib2
import wsgiref.simple_server

from distci import frontend
from distci.worker import worker_base
from distci.worker import task_base

class BackgroundHttpServer:
    def __init__(self, server):
        self.server = server

    def serve(self):
        self.server.serve_forever()

class SilentWSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, *args):
        pass

class TestWorkerBase:
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

        cls.server = wsgiref.simple_server.make_server('localhost', 8800, cls.frontend_app.handle_request, handler_class=SilentWSGIRequestHandler)

        cls.slave = BackgroundHttpServer(cls.server)
        cls.slave_thread = threading.Thread(target=cls.slave.serve)
        cls.slave_thread.start()

        worker_config = { 'capabilities': [ 'test' ],
                          'poll_interval': 1,
                          'retry_count': 10,
                          'task_frontends': [ 'http://localhost:8800/' ] }
        cls.worker = worker_base.WorkerBase(worker_config)

        cls.test_state = {}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.slave_thread.join()
        shutil.rmtree(cls.data_directory)

    def test_01_list_tasks_empty(self):
        task = self.worker.fetch_task(0)
        assert task is None, "didn't expect task to be returned"

    def test_02_post_task(self):
        new_task = task_base.GenericTask({'status': 'pending',
                                          'capabilities': ['test']})
        task_data = self.worker.post_new_task(new_task)
        assert task_data is not None, "failed to post new task"
        self.test_state['task_id'] = task_data.id

    def test_03_fetch_task(self):
        task = self.worker.fetch_task(0)
        assert task is not None, "failed to allocate our task"

    def test_04_get_task(self):
        task = self.worker.get_task(self.test_state['task_id'])
        assert task is not None, "failed to get task data"

    def test_05_fetch_task_with_all_assigned(self):
        task = self.worker.fetch_task(0)
        assert task is None, "didn't expect task to be returned"

