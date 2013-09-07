"""
Test DistCI frontend build handling

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

from nose.plugins.skip import SkipTest
from webtest import TestApp, TestRequest
import json
import tempfile
import os
import shutil
import threading
import urllib2
import wsgiref.simple_server

from distci import frontend

class BackgroundHttpServer:
    def __init__(self, server):
        self.server = server

    def serve(self):
        self.server.serve_forever()

class SilentWSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, *args):
        pass

class TestJobsBuilds:
    frontend_app = None
    app = None
    config_file = None
    data_directory = None
    test_state = {}

    @classmethod
    def route_request(cls, environ, start_request):
        return cls.frontend_app(environ, start_request)

    @classmethod
    def setUpClass(cls):
        cls.data_directory = tempfile.mkdtemp()
        config_file = os.path.join(cls.data_directory, 'frontend.conf')
        os.mkdir(os.path.join(cls.data_directory, 'jobs'))
        os.mkdir(os.path.join(cls.data_directory, 'tasks'))

        cls.server = wsgiref.simple_server.make_server('localhost', 0, cls.route_request, handler_class=SilentWSGIRequestHandler)
        cls.server_port = cls.server.socket.getsockname()[1]

        config = { "data_directory": cls.data_directory,
                   "task_frontends": [ 'http://localhost:%d/' % cls.server_port ] }
        json.dump(config, file(config_file, 'wb'))

        cls.frontend_app = frontend.Frontend(config)
        cls.app = TestApp(cls.frontend_app)

        cls.slave = BackgroundHttpServer(cls.server)
        cls.slave_thread = threading.Thread(target=cls.slave.serve)
        cls.slave_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.slave_thread.join()
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

    def test_01_get_builds_empty(self):
        response = self.app.request('/jobs/%s/builds' % self.test_state['job_id'])
        result = json.loads(response.body)
        assert result.has_key('builds'), "Missing builds key"
        assert len(result['builds']) == 0, "Returned builds when expecting none"

    def test_02_trigger_build(self):
        request = TestRequest.blank('/jobs/%s/builds' % self.test_state['job_id'])
        request.method = 'POST'
        response = self.app.do_request(request, 201, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        self.test_state['build_number'] = result['build_number']

    def test_03_get_build_state(self):
        response = self.app.request('/jobs/%s/builds/%s/state' % (self.test_state['job_id'], self.test_state['build_number']))
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        assert result.has_key('state'), "state went missing"
        assert result['state'].has_key('status'), "status went missing"
        assert result['state']['status'] == 'preparing', "wrong status"

    def test_04_update_build_state(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/state' % (self.test_state['job_id'], self.test_state['build_number']), content_type='application/json')
        request.method = 'PUT'
        request.body = json.dumps({"status": "pending", "config": {"name": "test"}})
        response = self.app.do_request(request, 200, False)
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        assert result.has_key('state'), "state went missing"
        assert result['state'].has_key('status'), "status went missing"
        assert result['state']['status'] == 'pending', "wrong status"
        assert result['state'].has_key('config'), "config went missing"
        assert result['state']['config'].has_key('name'), "config/name went missing"
        assert result['state']['config']['name'] == 'test', "wrong name"

        response = self.app.request('/jobs/%s/builds/%s/state' % (self.test_state['job_id'], self.test_state['build_number']))
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"
        assert result.has_key('state'), "state went missing"
        assert result['state'].has_key('status'), "status went missing"
        assert result['state']['status'] == 'pending', "wrong status"
        assert result['state'].has_key('config'), "config went missing"
        assert result['state']['config'].has_key('name'), "config/name went missing"
        assert result['state']['config']['name'] == 'test', "wrong name"

    def test_05_console_log(self):
        response = self.app.request('/jobs/%s/builds/%s/console' % (self.test_state['job_id'], self.test_state['build_number']))
        assert response.body == '', "console log was not empty"

        request = TestRequest.blank('/jobs/%s/builds/%s/console' % (self.test_state['job_id'], self.test_state['build_number']), content_type='text/plain')
        request.method = 'POST'
        request.body = 'line1\n'
        _ = self.app.do_request(request, 204, False)

        response = self.app.request('/jobs/%s/builds/%s/console' % (self.test_state['job_id'], self.test_state['build_number']))
        assert response.body == 'line1\n', "Wrong content"

        request = TestRequest.blank('/jobs/%s/builds/%s/console' % (self.test_state['job_id'], self.test_state['build_number']), content_type='text/plain')
        request.method = 'POST'
        request.body = 'line2\n'
        _ = self.app.do_request(request, 204, False)

        response = self.app.request('/jobs/%s/builds/%s/console' % (self.test_state['job_id'], self.test_state['build_number']))
        assert response.body == 'line1\nline2\n', "Wrong content"

    def test_06_set_workspace(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/workspace' % (self.test_state['job_id'], self.test_state['build_number']), content_type='application/octet-stream')
        request.method = 'PUT'
        request.body = 'test_content'
        _ = self.app.do_request(request, 204, False)

    def test_07_get_workspace(self):
        response = self.app.request('/jobs/%s/builds/%s/workspace' % (self.test_state['job_id'], self.test_state['build_number']))
        assert response.body == 'test_content', "Wrong data"

    def test_08_update_workspace(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/workspace' % (self.test_state['job_id'], self.test_state['build_number']), content_type='application/octet-stream')
        request.method = 'PUT'
        request.body = 'updated_test_content'
        _ = self.app.do_request(request, 204, False)

        response = self.app.request('/jobs/%s/builds/%s/workspace' % (self.test_state['job_id'], self.test_state['build_number']))
        assert response.body == 'updated_test_content', "Wrong data"

    def test_09_delete_workspace(self):
        request = TestRequest.blank('/jobs/%s/builds/%s/workspace' % (self.test_state['job_id'], self.test_state['build_number']))
        request.method = 'DELETE'
        _ = self.app.do_request(request, 204, False)

    def test_10_delete_build(self):
        request = TestRequest.blank('/jobs/%s/builds/%s' % (self.test_state['job_id'], self.test_state['build_number']))
        request.method = 'DELETE'
        _ = self.app.do_request(request, 204, False)

    def test_11_github_webhook(self):
        response = self.app.post('/jobs/%s/github-webhook' % self.test_state['job_id'], {'payload': json.dumps({'ref':'refs/heads/master'})})
        result = json.loads(response.body)
        assert result.has_key('job_id'), "ID entry went missing"
        assert result.has_key('build_number'), "build_number went missing"

    def test_12_github_webhook_negative(self):
        request = TestRequest.blank('/jobs/%s/github-webhook' % self.test_state['job_id'])
        request.method = 'POST'
        request.body = 'unexpected content'
        _response = self.app.do_request(request, 400, True)
        request = TestRequest.blank('/jobs/%s/github-webhook' % self.test_state['job_id'])
        request.method = 'POST'
        request.body = json.dumps({'ref': 'refs/heads/wrongbranch'})
        _response = self.app.do_request(request, 400, True)

