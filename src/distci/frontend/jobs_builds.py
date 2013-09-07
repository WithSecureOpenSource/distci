"""
Handle requests related to build operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
import json
import logging
import time
import shutil
import webob

from distci.frontend import validators, jobs_builds_artifacts, sync, constants

from distci import distcilib

class JobsBuilds(object):
    """ Class for handling build related requests """
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_builds')
        self.zknodes = config.get('zookeeper_nodes', [])
        if len(self.zknodes) == 0:
            self.zknodes = None
        self.jobs_builds_artifacts = jobs_builds_artifacts.JobsBuildsArtifacts(config)
        self.distci_client = distcilib.DistCIClient(config)

    def _job_dir(self, job_id):
        """ Return directory for a specific job """
        return os.path.join(self.config.get('data_directory'), 'jobs', job_id)

    def _build_dir(self, job_id, build_id):
        """ Return directory for a specific build """
        return os.path.join(self._job_dir(job_id), build_id)

    def _build_state_file(self, job_id, build_id):
        """ Return filename for a build state file """
        return os.path.join(self._build_dir(job_id, build_id), 'build.state')

    def _build_workspace_file(self, job_id, build_id):
        """ Return filename for workspace archive """
        return os.path.join(self._build_dir(job_id, build_id), 'workspace')

    def _console_log_file(self, job_id, build_id):
        """ Return filename for a build console log """
        return os.path.join(self._build_dir(job_id, build_id), 'console.log')

    def _get_build_numbers(self, job_id):
        """ Return all builds for given job """
        build_ids = []
        build_id_candidates = os.listdir(self._job_dir(job_id))
        for build_id_candidate in build_id_candidates:
            try:
                build_number = int(build_id_candidate)
                build_ids.append(build_number)
            except ValueError:
                pass
        return build_ids

    def get_builds(self, job_id):
        """ Return all builds for a specific job """
        result = { 'builds': self._get_build_numbers(job_id) }
        if len(result['builds']) > 0:
            result['last_build_number'] = max(result['builds'])
        return webob.Response(status=200, body=json.dumps(result), content_type="application/json")

    def trigger_build(self, job_id):
        """ Trigger a new build """
        if self.zknodes:
            lock = sync.ZooKeeperLock(self.zknodes, 'job-lock-%s' % job_id)
        else:
            lock = sync.PhonyLock('job-lock-%s' % job_id)
        if lock.try_lock() != True:
            lock.close()
            self.log.info("Job locked '%s'" % job_id)
            return webob.Response(status=400, body=constants.ERROR_JOB_LOCKED)

        build_ids = self._get_build_numbers(job_id)
        if len(build_ids) > 0:
            new_build_number = str(max(build_ids) + 1)
        else:
            new_build_number = "1"

        try:
            os.mkdir(self._build_dir(job_id, new_build_number))
        except OSError:
            if lock:
                lock.unlock()
                lock.close()
            self.log.error("Build directory creation failed")
            return webob.Response(status=500, body=constants.ERROR_BUILD_CREATE_FAILED)

        if lock:
            lock.unlock()
            lock.close()

        build_state = { "status": "preparing" }
        try:
            file(self._build_state_file(job_id, new_build_number), 'wb').write(json.dumps(build_state))
        except IOError:
            self.log.error('Failed to write build state, job_id %s, build %s', job_id, new_build_number)
            return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        if self.config.get('task_frontends'):
            for _ in range(10):
                task_id = self.distci_client.tasks.create()
                if task_id is not None:
                    break
            if task_id is None:
                self.log.error('Failed to create a build task')
                return webob.Response(status=500, body=constants.ERROR_BUILD_TASK_CREATION_FAILED)

            task_description = { 'capabilities': [ 'build_control_v1' ],
                                 'job_id': job_id,
                                 'build_number': new_build_number,
                                 'status': 'pending',
                                 'id': task_id }

            for _ in range(10):
                task_details = self.distci_client.tasks.update(task_id, task_description)
                if task_details is not None:
                    break
            if task_details is None:
                self.log.error("Build task creation failed")
                return webob.Response(status=500, body=constants.ERROR_BUILD_TASK_CREATION_FAILED)
        else:
            self.log.warn('No task frontends configured, unable to trigger build control task')

        return webob.Response(status=201, body=json.dumps({'job_id': job_id, 'build_number': int(new_build_number), 'state': build_state}), content_type="application/json")

    def get_build_state(self, job_id, build_id):
        """ Get job state """
        if validators.validate_build_id(build_id) != build_id:
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_JOB_NOT_FOUND)
        build_data = None
        for _ in range(10):
            try:
                build_state = json.load(file(self._build_state_file(job_id, build_id), 'rb'))
                build_data = json.dumps({'job_id': job_id, 'build_number': build_id, 'state': build_state})
                break
            except (OSError, ValueError):
                time.sleep(0.1)
        if not build_data:
            return webob.Response(status=409, body=constants.ERROR_BUILD_LOCKED)
        return webob.Response(status=200, body=build_data, content_type="application/json")

    def update_build_state(self, request, job_id, build_id):
        """ Update build state """
        try:
            build_state = json.load(request.body_file)
        except ValueError:
            self.log.error('Failed to load build state')
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_PAYLOAD)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

        try:
            file(self._build_state_file(job_id, build_id), 'wb').write(json.dumps(build_state))
        except IOError:
            self.log.error('Failed to write build state, job_id %s, build %s', job_id, build_id)
            return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        return webob.Response(status=200, body=json.dumps({'job_id': job_id, 'build_number': int(build_id), 'state': build_state}), content_type="application/json")

    def get_console_log(self, job_id, build_id):
        """ Return contents of the console log """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
        console_log = ''
        try:
            console_log = file(self._console_log_file(job_id, build_id), 'rb').read()
        except IOError:
            # can be ignored, we just return empty log
            pass
        return webob.Response(status=200, body=console_log, content_type="text/plain")

    def update_console_log(self, request, job_id, build_id):
        """ Append content to the console log """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

        try:
            log = request.body_file.read()
            file(self._console_log_file(job_id, build_id), 'ab').write(log)
        except IOError:
            # can be ignored, we just return empty log
            pass
        return webob.Response(status=204)

    def update_workspace(self, request, job_id, build_id):
        """ Store workspace archive """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

        data_len = request.content_length
        ifh = request.body_file

        try:
            ofh = open(self._build_workspace_file(job_id, build_id), 'wb')
        except IOError:
            return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        try:
            while data_len > 0:
                read_len = data_len
                if read_len > 1024*128:
                    read_len = 1024*128
                data = ifh.read(read_len)
                ofh.write(data)
                data_len = data_len - len(data)
        except IOError:
            ofh.close()
            return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        ofh.close()

        return webob.Response(status=204)

    def get_workspace(self, job_id, build_id):
        """ Get workspace archive """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isfile(self._build_workspace_file(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

        try:
            ifh = open(self._build_workspace_file(job_id, build_id))
        except IOError:
            return webob.Response(status=500, body=constants.ERROR_BUILD_READ_FAILED)

        file_len = os.path.getsize(self._build_workspace_file(job_id, build_id))

        return webob.Response(status=200, body_file=ifh, content_length=file_len, content_type="application/octet-stream")

    def delete_workspace(self, job_id, build_id):
        """ Delete workspace archive """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isfile(self._build_workspace_file(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

        try:
            os.unlink(self._build_workspace_file(job_id, build_id))
        except IOError:
            return webob.Response(status=500, body=constants.ERROR_BUILD_WRITE_FAILED)

        return webob.Response(status=204)

    def delete_build(self, job_id, build_id):
        """ Delete a specific build and all related data """
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
        try:
            shutil.rmtree(self._build_dir(job_id, build_id))
        except OSError:
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)
        return webob.Response(status=204)

    def handle_request(self, request, job_id, parts):
        """ Handle requests related to builds """
        if validators.validate_job_id(job_id) == None:
            self.log.error('Invalid job_id: %r' % job_id)
            return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_ID)
        if not os.path.isdir(self._job_dir(job_id)):
            return webob.Response(status=404, body=constants.ERROR_BUILD_NOT_FOUND)

        if len(parts) == 0:
            if request.method == 'GET':
                return self.get_builds(job_id)
            elif request.method == 'POST':
                return self.trigger_build(job_id)
        elif len(parts) == 1:
            if request.method == 'GET':
                return self.get_build_state(job_id, parts[0])
            elif request.method == 'DELETE':
                return self.delete_build(job_id, parts[0])
        elif parts[1] == 'artifacts':
            return self.jobs_builds_artifacts.handle_request(request, job_id, parts[0], parts[2:])
        elif len(parts) == 2:
            if parts[1] == 'state' and request.method == 'GET':
                return self.get_build_state(job_id, parts[0])
            elif parts[1] == 'state' and request.method == 'PUT':
                return self.update_build_state(request, job_id, parts[0])
            elif parts[1] == 'console' and request.method == 'GET':
                return self.get_console_log(job_id, parts[0])
            elif parts[1] == 'console' and request.method == 'POST':
                return self.update_console_log(request, job_id, parts[0])
            elif parts[1] == 'workspace' and request.method == 'GET':
                return self.get_workspace(job_id, parts[0])
            elif parts[1] == 'workspace' and request.method == 'PUT':
                return self.update_workspace(request, job_id, parts[0])
            elif parts[1] == 'workspace' and request.method == 'DELETE':
                return self.delete_workspace(job_id, parts[0])

        return webob.Response(status=400)

