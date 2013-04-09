"""
Tests for clientlib/builds/workspace

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
        job = self.client.jobs.create(job_config)
        assert job is not None, "Empty result for job creation"
        self.state['job_id'] = job['job_id']

        build = self.client.builds.trigger(self.state['job_id'])
        assert build is not None, "Empty result for trigger build"
        assert build.get('job_id') == self.state['job_id'], "Job ID mismatch"
        assert build.has_key('build_number'), "Build number went missing"
        self.state['build_number'] = build['build_number']

    def test_01_put_workspace(self):
        self.state['workspace_contents'] = 'some content'
        wspace = tempfile.TemporaryFile()
        wspace.write(self.state['workspace_contents'])
        wspace.seek(0)
        assert self.client.builds.workspace.put(self.state['job_id'], self.state['build_number'], wspace, len(self.state['workspace_contents'])) == True, "Failed to store workspace"

    def test_02_get_workspace(self):
        wspace = tempfile.TemporaryFile()
        assert self.client.builds.workspace.get(self.state['job_id'], self.state['build_number'], wspace) == True, "Failed to retrieve workspace"
        wspace.seek(0)
        assert wspace.read() == self.state['workspace_contents'], "Workspace content mismatch"

    def test_03_delete_workspace(self):
        self.client.builds.workspace.delete(self.state['job_id'], self.state['build_number'])

        wspace = tempfile.TemporaryFile()
        assert self.client.builds.workspace.get(self.state['job_id'], self.state['build_number'], wspace) == False, "Unexpected success after delete"

