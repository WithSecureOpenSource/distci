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

import frontend
from worker import worker_base
from worker import task_base

class BackgroundHttpServer:
    def __init__(self, server):
        self.server = server
        self.running = True

    def serve(self):
        while True:
            if self.running == False:
                break
            self.server.handle_request()

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
                          'frontends': [ 'http://localhost:8800/' ] }
        cls.worker = worker_base.WorkerBase()
        cls.worker.worker_config = worker_config

    @classmethod
    def tearDownClass(cls):
        cls.slave.running = False
        r = urllib2.urlopen('http://localhost:8800/')
        _ = r.read()
        cls.slave_thread.join()
        shutil.rmtree(cls.data_directory)

    def test_01_list_tasks_empty(self):
        task = self.worker.fetch_task(1)
        assert task is None, "didn't expect task to be returned"

    def test_02_post_task(self):
        new_task = task_base.GenericTask({'capabilities': ['test']})
        task_id = self.worker.post_new_task(new_task)
        assert task_id is not None, "failed to post new task"

    def test_03_fetch_task(self):
        task = self.worker.fetch_task(1)
        assert task is not None, "failed to allocate our task"

    def test_04_fetch_task_with_all_assigned(self):
        task = self.worker.fetch_task(1)
        assert task is None, "didn't expect task to be returned"

