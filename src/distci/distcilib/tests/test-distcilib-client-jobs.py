"""
Tests for clientlib/jobs

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
    test_state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.mkdtemp()
        frontend_config_file = os.path.join(cls.data_directory, 'frontend.conf')
        os.mkdir(os.path.join(cls.data_directory, 'tasks'))
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

    def test_01_create_job(self):
        job_config = { 'job_id': 'testjob', 'testkey': 'testvalue' }
        job = self.client.jobs.set(job_config['job_id'], job_config)
        assert job is not None, "Empty result for job creation"
        assert job.has_key('job_id'), "Missing job_id key in job reply"
        assert job['job_id'] == job_config['job_id'], "JobID mismatch"
        assert job.has_key('config'), "Missing config key in job reply"
        assert job['config'].has_key('testkey'), "Data mismatch"
        assert job['config']['testkey'] == job_config['testkey'], "Data mismatch"
        self.state['job_id'] = job['job_id']
        self.state['job_config'] = job_config

    def test_02_get_job(self):
        job = self.client.jobs.get(self.state['job_id'])
        assert job is not None, "Empty result for get job"
        assert job.has_key('job_id'), "Missing job_id key in job reply"
        assert job['job_id'] == self.state['job_id'], "JobID mismatch"
        assert job.has_key('config'), "Missing config key in job reply"
        assert job['config'].has_key('testkey'), "Data mismatch"
        assert job['config']['testkey'] == self.state['job_config']['testkey'], "Data mismatch"

    def test_03_list_jobs(self):
        jobs = self.client.jobs.list()
        assert jobs is not None, "Empty result for list jobs"
        assert jobs.has_key('jobs'), "Missing jobs key in reply"
        assert len(jobs['jobs']) == 1, "Wrong count when expecting one job"
        assert self.state['job_id'] in jobs['jobs'], "Test job missing from the list"

    def test_04_update_job(self):
        job_config = { 'job_id': 'testjob', 'testkey': 'testvalue_modified' }
        job = self.client.jobs.set(job_config['job_id'], job_config)
        assert job is not None, "Empty result for job update"
        assert job.has_key('job_id'), "Missing job_id key in job reply"
        assert job['job_id'] == self.state['job_id'], "JobID mismatch"
        assert job.has_key('config'), "Missing config key in job reply"
        assert job['config'].has_key('testkey'), "Data mismatch"
        assert job['config']['testkey'] == job_config['testkey'], "Data mismatch"

        job = self.client.jobs.get(self.state['job_id'])
        assert job is not None, "Empty result for get job"
        assert job.has_key('job_id'), "Missing job_id key in job reply"
        assert job['job_id'] == job_config['job_id'], "JobID mismatch"
        assert job.has_key('config'), "Missing config key in job reply"
        assert job['config'].has_key('testkey'), "Data mismatch"
        assert job['config']['testkey'] == job_config['testkey'], "Data mismatch"

    def test_05_delete_job(self):
        self.client.jobs.delete(self.state['job_id'])
        job = self.client.jobs.get(self.state['job_id'])
        assert job is None, "Unexpected data return after job deletion"

