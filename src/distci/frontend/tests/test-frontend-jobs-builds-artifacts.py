"""
Test DistCI frontend build artifact handling

Copyright (c) 2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

from nose.plugins.skip import SkipTest
from webtest import TestApp, TestRequest
import json
import tempfile
import os
import shutil

from distci.frontend import frontend

class TestJobsBuildArtifacts:
    app = None
    config_file = None
    data_directory = None
    test_state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(cls.data_directory, 'jobs'))

        config = { "data_directory": cls.data_directory }

        cls.frontend_app = frontend.Frontend(config)
        cls.app = TestApp(cls.frontend_app.handle_request)

    @classmethod
    def tearDownClass(cls):
        cls.app = None
        shutil.rmtree(cls.data_directory)

    def test_00_setup(self):
        test_job_data_file = os.path.join(os.path.dirname(__file__), 'test-frontend-jobs-builds_job-config.json')
        test_job_data = json.load(file(test_job_data_file, 'rb'))
        request = TestRequest.blank('/jobs/%s' % str(test_job_data['job_id']), content_type='application/json')
        request.method = 'PUT'
        request.body = json.dumps(test_job_data)
        response = self.app.do_request(request, 200, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('config'), "config entry went missing"
        self.test_state['job_id'] = str(result['job_id'])

        request = TestRequest.blank('/jobs/%s/builds' % self.test_state['job_id'])
        request.method = 'POST'
        response = self.app.do_request(request, 201, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        self.test_state['build_number'] = str(result['build_number'])

    def test_01_create_artifact(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/artifacts' % (self.test_state['job_id'], self.test_state['build_number']), content_type='application/octet-stream')
        request.method = 'POST'
        request.body = 'test_content'
        response = self.app.do_request(request, 201, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        assert result.has_key('artifact_id'), "Artifact ID went missing"
        self.test_state['artifact_id'] = str(result['artifact_id'])

    def test_02_get_artifact(self):
        response = self.app.request('/jobs/%s/builds/%s/artifacts/%s' % (self.test_state['job_id'], self.test_state['build_number'], self.test_state['artifact_id']))
        assert response.body == 'test_content', "Wrong data"

    def test_03_get_artifact_alternate(self):
        response = self.app.request('/jobs/%s/builds/%s/artifacts/%s/test_data.txt' % (self.test_state['job_id'], self.test_state['build_number'], self.test_state['artifact_id']))
        assert response.body == 'test_content', "Wrong data"

    def test_04_update_artifact(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/artifacts/%s' % (self.test_state['job_id'], self.test_state['build_number'], self.test_state['artifact_id']), content_type='application/octet-stream')
        request.method = 'PUT'
        request.body = 'test_content_modified'
        response = self.app.do_request(request, 200, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        assert result.has_key('artifact_id'), "Artifact ID went missing"
        assert result['artifact_id'] == self.test_state['artifact_id'], "Artifact ID mismatch"

        response = self.app.request('/jobs/%s/builds/%s/artifacts/%s' % (self.test_state['job_id'], self.test_state['build_number'], self.test_state['artifact_id']))
        assert response.body == 'test_content_modified', "Wrong data"

    def test_05_delete_artifact(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/artifacts/%s' % (self.test_state['job_id'], self.test_state['build_number'], self.test_state['artifact_id']), content_type='application/octet-stream')
        request.method = 'DELETE'
        _ = self.app.do_request(request, 204, False)

