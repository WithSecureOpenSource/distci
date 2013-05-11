"""
Tests for DistCI task management interfaces

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

class TestTasks:
    app = None
    config_file = None
    data_directory = None
    test_state = {}

    @classmethod
    def setUpClass(cls):
        cls.data_directory = '/Users/noushe/CI-proto'
        cls.data_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(cls.data_directory, 'tasks'))

        config = { "data_directory": cls.data_directory }

        frontend_app = frontend.Frontend(config)
        cls.app = TestApp(frontend_app.handle_request)

    @classmethod
    def tearDownClass(cls):
        cls.app = None
        shutil.rmtree(cls.data_directory)

    def test_01_list_tasks_empty(self):
        response = self.app.request('/tasks')
        result = json.loads(response.body)
        assert result.has_key('tasks'), "Tasks entry went missing"
        assert len(result['tasks']) == 0, "Tasks entry was not empty"

    def test_02_post_task(self):
        task_data = json.dumps({ 'command': 'something' })
        request = TestRequest.blank('/tasks', content_type='application/json')
        request.method = 'POST'
        request.body = task_data
        response = self.app.do_request(request, 201, False)
        result = json.loads(response.body)
        assert result.has_key('id'), "ID entry went missing"
        assert result.has_key('data'), "data entry went missing"
        self.test_state['id'] = str(result['id'])

    def test_03_check_single_task(self):
        task_id = self.test_state.get('id')
        if task_id is None:
            raise SkipTest("Skipping test for single task status, no recorded state")
        response = self.app.request('/tasks/%s' % task_id)
        result = json.loads(response.body)
        assert result['id'] == task_id, "ID mismatch"
        assert result['data']['command'] == 'something', "Wrong data"

    def test_04_update(self):
        task_id = self.test_state.get('id')
        if task_id is None:
            raise SkipTest("Skipping test for single task update, no recorded state")
        new_task_data = json.dumps({'command': 'something_else', 'assignee': 'my-id'})
        request = TestRequest.blank('/tasks/%s' % task_id, content_type='application/json')
        request.method = 'PUT'
        request.body = new_task_data
        response = self.app.do_request(request, 200, False)
        result = json.loads(response.body)
        assert result.has_key('id'), "ID entry went missing"
        assert result.has_key('data'), "data entry went missing"
        assert result['data']['command'] == 'something_else', "Wrong command"
        assert result['data']['assignee'] == 'my-id', "Wrong assignee"

    def test_05_update_with_wrong_assignee(self):
        task_id = self.test_state.get('id')
        if task_id is None:
            raise SkipTest("Skipping test for single task update, no recorded state")
        new_task_data = json.dumps({'command': 'something_else', 'assignee': 'my-id-not-same'})
        request = TestRequest.blank('/tasks/%s' % task_id, content_type='application/json')
        request.method = 'PUT'
        request.body = new_task_data
        response = self.app.do_request(request, 409, False)

    def test_06_list_tasks(self):
        response = self.app.request('/tasks')
        result = json.loads(response.body)
        assert result.has_key('tasks'), "Tasks entry went missing"
        assert len(result['tasks']) == 1, "Invalid task count"
        task_id = self.test_state.get('id')
        if task_id is not None:
            assert task_id in result['tasks'], "Task not included in the list"

    def test_07_delete(self):
        task_id = self.test_state.get('id')
        if task_id is None:
            raise SkipTest("Skipping test for single task status, no recorded state")
        request = TestRequest.blank('/tasks/%s' % task_id)
        request.method = 'DELETE'
        response = self.app.do_request(request, 204, False)

        response = self.app.request('/tasks')
        result = json.loads(response.body)
        assert result.has_key('tasks'), "Tasks entry went missing"
        assert len(result['tasks']) == 0, "Invalid task count"

