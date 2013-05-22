"""
Tests for clientlib/builds

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import tempfile
import os
import shutil
import threading
import urllib2
import wsgiref.simple_server

from distci.frontend import frontend

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
    state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(cls.data_directory, 'jobs'))

        frontend_config = { "data_directory": cls.data_directory }

        cls.frontend_app = frontend.Frontend(frontend_config)

        cls.server = wsgiref.simple_server.make_server('localhost', 0, cls.frontend_app.handle_request, handler_class=SilentWSGIRequestHandler)
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

    def test_00_setup(self):
        job_config = { 'job_id': 'testjob' }
        job = self.client.jobs.set(job_config['job_id'], job_config)
        assert job is not None, "Empty result for job creation"
        self.state['job_id'] = job['job_id']

    def test_01_list_builds_empty(self):
        builds = self.client.builds.list(self.state['job_id'])
        assert builds is not None, "Empty result for list builds"
        assert builds.has_key('builds'), "Missing builds key in list reply"
        assert len(builds['builds']) == 0, "Non-empty builds list"

    def test_02_trigger_build(self):
        build = self.client.builds.trigger(self.state['job_id'])
        assert build is not None, "Empty result for trigger build"
        assert build.get('job_id') == self.state['job_id'], "Job ID mismatch"
        assert build.has_key('build_number'), "Build number went missing"
        self.state['build_number'] = build['build_number']

    def test_03_list_builds(self):
        builds = self.client.builds.list(self.state['job_id'])
        assert builds is not None, "Empty result for list builds"
        assert builds.has_key('builds'), "Missing builds key in list reply"
        assert self.state['build_number'] in builds['builds'], "Our build not present on builds list"

    def test_04_delete_build(self):
        self.client.builds.delete(self.state['job_id'], self.state['build_number'])

        builds = self.client.builds.list(self.state['job_id'])
        assert builds is not None, "Empty result for list builds"
        assert builds.has_key('builds'), "Missing builds key in list reply"
        assert self.state['build_number'] not in builds['builds'], "Our build is present on builds list"

