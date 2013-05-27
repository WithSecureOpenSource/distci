"""
Tests for clientlib/builds/artifacts

Copyright (c) 2013 Heikki Nousiainen, F-Secure
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
    state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.mkdtemp()
        frontend_config_file = os.path.join(cls.data_directory, 'frontend.conf')
        os.mkdir(os.path.join(cls.data_directory, 'jobs'))

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

    def test_00_setup(self):
        job_config = { 'job_id': 'testjob' }
        job = self.client.jobs.set(job_config['job_id'], job_config)
        assert job is not None, "Empty result for job creation"
        self.state['job_id'] = job['job_id']

        build = self.client.builds.trigger(self.state['job_id'])
        assert build is not None, "Empty result for trigger build"
        assert build.get('job_id') == self.state['job_id'], "Job ID mismatch"
        assert build.has_key('build_number'), "Build number went missing"
        self.state['build_number'] = build['build_number']

    def test_01_put_artifact(self):
        self.state['artifact_contents'] = 'some artifact content'
        artifact = tempfile.TemporaryFile()
        artifact.write(self.state['artifact_contents'])
        artifact.seek(0)
        result = self.client.builds.artifacts.put(self.state['job_id'], self.state['build_number'], artifact, len(self.state['artifact_contents']))
        assert result is not None, "Failed to store artifact"
        assert result.get('artifact_id') is not None, "Reply is missing artifact_id"
        self.state['artifact_id'] = result['artifact_id']

    def test_02_get_artifact(self):
        artifact = tempfile.TemporaryFile()
        assert self.client.builds.artifacts.get(self.state['job_id'], self.state['build_number'], self.state['artifact_id'], artifact) == True, "Failed to retrieve artifact"
        artifact.seek(0)
        assert artifact.read() == self.state['artifact_contents'], "Artifact content mismatch"

    def test_03_delete_delete(self):
        self.client.builds.artifacts.delete(self.state['job_id'], self.state['build_number'], self.state['artifact_id'])

        artifact = tempfile.TemporaryFile()
        assert self.client.builds.artifacts.get(self.state['job_id'], self.state['build_number'], self.state['artifact_id'], artifact) == False, "Unexpected success after delete"

