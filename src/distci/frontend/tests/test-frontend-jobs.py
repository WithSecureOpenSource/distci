"""
Test DistCI frontend job handling

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

from nose.plugins.skip import SkipTest
from webtest import TestApp, TestRequest
import json
import tempfile
import os
import shutil

from distci.frontend import frontend

class TestJobs:
    app = None
    config_file = None
    data_directory = None
    test_state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = '/Users/noushe/CI-proto'
        cls.data_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(cls.data_directory, 'jobs'))

        config = { "data_directory": cls.data_directory }

        frontend_app = frontend.Frontend(config)
        cls.app = TestApp(frontend_app.handle_request)

    @classmethod
    def tearDownClass(cls):
        cls.app = None
        shutil.rmtree(cls.data_directory)

    def test_01_list_jobs_empty(self):
        response = self.app.request('/jobs')
        result = json.loads(response.body)
        assert result.has_key('jobs'), "Jobs entry went missing"
        assert len(result['jobs']) == 0, "Jobs entry was not empty"

    def test_02_post_job(self):
        job_data = json.dumps({ 'build_tasks': ['something'], 'job_id': 'test_job' })
        request = TestRequest.blank('/jobs', content_type='application/json')
        request.method = 'POST'
        request.body = job_data
        response = self.app.do_request(request, 201, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('config'), "config entry went missing"
        self.test_state['job_id'] = str(result['job_id'])
        assert result['config']['build_tasks'] == ['something'], "wrong config values"

        response = self.app.request('/jobs')
        result = json.loads(response.body)
        assert result.has_key('jobs'), "Jobs entry went missing"
        assert len(result['jobs']) == 1, "Invalid job count"

    def test_03_check_single_job(self):
        job_id = self.test_state.get('job_id')
        if job_id is None:
            raise SkipTest("Skipping test for single job config, no recorded state")
        response = self.app.request('/jobs/%s' % job_id)
        result = json.loads(response.body)
        assert result['job_id'] == job_id, "ID mismatch"
        assert result['config']['build_tasks'] == ['something'], "Wrong data"

    def test_04_update_job(self):
        job_id = self.test_state.get('job_id')
        if job_id is None:
            raise SkipTest("Skipping test for single job config update, no recorded state")
        new_job_config = json.dumps({'build_tasks': ['something_else'], 'job_id': 'test_job'})
        request = TestRequest.blank('/jobs/%s' % job_id, content_type='application/json')
        request.method = 'PUT'
        request.body = new_job_config
        response = self.app.do_request(request, 200, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('config'), "config entry went missing"
        assert result['config']['build_tasks'] == ['something_else'], "Wrong command"

        response = self.app.request('/jobs')
        result = json.loads(response.body)
        assert result.has_key('jobs'), "Jobs entry went missing"
        assert len(result['jobs']) == 1, "Invalid job count"

    def test_05_delete_job(self):
        job_id = self.test_state.get('job_id')
        if job_id is None:
            raise SkipTest("Skipping test for single job deletion, no recorded state")
        request = TestRequest.blank('/jobs/%s' % job_id)
        request.method = 'DELETE'
        response = self.app.do_request(request, 204, False)

        response = self.app.request('/jobs')
        result = json.loads(response.body)
        assert result.has_key('jobs'), "Jobs entry went missing"
        assert len(result['jobs']) == 0, "Invalid job count"

