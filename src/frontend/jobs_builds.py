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

from . import validators, request, response, jobs_builds_artifacts, distlocks, constants

from distcilib import client

class JobsBuilds(object):
    """ Class for handling build related requests """
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_builds')
        self.zknodes = config.get('zookeeper_nodes', [])
        if len(self.zknodes) == 0:
            self.zknodes = None
        self.jobs_builds_artifacts = jobs_builds_artifacts.JobsBuildsArtifacts(config)
        self.distci_client = client.Client(config)

    def _job_dir(self, job_id):
        """ Return directory for a specific job """
        return os.path.join(self.config.get('data_directory'), 'jobs', job_id)

    def _build_dir(self, job_id, build_id):
        """ Return directory for a specific build """
        return os.path.join(self._job_dir(job_id), build_id)

    def _build_state_file(self, job_id, build_id):
        """ Return filename for a build state file """
        return os.path.join(self._build_dir(job_id, build_id), 'build.state')

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

    def get_builds(self, start_response, job_id):
        """ Return all builds for a specific job """
        if validators.validate_job_id(job_id) == None:
            self.log.error("Job_id validation failure")
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        result = { 'builds': self._get_build_numbers(job_id) }
        if len(result['builds']) > 0:
            result['last_build_number'] = max(result['builds'])
        return response.send_response(start_response, 200, json.dumps(result))

    def trigger_build(self, start_response, job_id):
        """ Trigger a new build """
        if validators.validate_job_id(job_id) == None:
            self.log.error("Job_id validation failure, '%s'", job_id)
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if self.zknodes:
            lock = distlocks.ZooKeeperLock(self.zknodes, 'job-lock-%s' % job_id)
            if lock.try_lock() != True:
                lock.close()
                self.log.debug("Job locked '%s'" % job_id)
                return response.send_error(start_response, 400, constants.ERROR_JOB_LOCKED)
        else:
            lock = None

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
            return response.send_error(start_response, 500, constants.ERROR_BUILD_CREATE_FAILED)

        if lock:
            lock.unlock()
            lock.close()

        build_state = { "status": "preparing" }
        try:
            file(self._build_state_file(job_id, new_build_number), 'wb').write(json.dumps(build_state))
        except IOError:
            self.log.debug('Failed to write build state, job_id %s, build %s', job_id, new_build_number)
            return response.send_error(start_response, 500, constants.ERROR_BUILD_WRITE_FAILED)

        task_description = { 'capabilities': [ 'build_control_v1' ],
                             'job_id': job_id,
                             'build_number': new_build_number,
                             'status': 'pending' }

        task_details = self.distci_client.create_task(task_description)
        if task_details is None or not task_details.has_key('id'):
            self.log.error("Build task creation failed")
            return response.send_error(start_response, 500, constants.ERROR_BUILD_TASK_CREATION_FAILED)

        return response.send_response(start_response, 201, json.dumps({'job_id': job_id, 'build_number': int(new_build_number), 'state': build_state}))

    def get_build_state(self, start_response, job_id, build_id):
        """ Get job state """
        if validators.validate_job_id(job_id) != job_id:
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return response.send_error(start_response, 404, constants.ERROR_JOB_NOT_FOUND)
        build_data = None
        for _ in range(10):
            try:
                build_state = json.load(file(self._build_state_file(job_id, build_id), 'rb'))
                build_data = json.dumps({'job_id': job_id, 'build_number': build_id, 'state': build_state})
                break
            except (OSError, ValueError):
                time.sleep(0.1)
        if not build_data:
            return response.send_error(start_response, 409, constants.ERROR_BUILD_LOCKED)
        return response.send_response(start_response, 200, build_data)

    def update_build_state(self, environ, start_response, job_id, build_id):
        """ Update build state """
        try:
            build_state = json.loads(request.read_request_data(environ))
        except ValueError:
            self.log.error('Failed to load build state')
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_PAYLOAD)
        if validators.validate_job_id(job_id) == None:
            self.log.error("Job_id validation failure, '%s'", job_id)
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return response.send_error(start_response, 404, constants.ERROR_BUILD_NOT_FOUND)

        try:
            file(self._build_state_file(job_id, build_id), 'wb').write(json.dumps(build_state))
        except IOError:
            self.log.debug('Failed to write build state, job_id %s, build %s', job_id, build_id)
            return response.send_error(start_response, 500, constants.ERROR_BUILD_WRITE_FAILED)

        return response.send_response(start_response, 200, json.dumps({'job_id': job_id, 'build_number': int(build_id), 'state': build_state}))

    def get_console_log(self, start_response, job_id, build_id):
        """ Return contents of the console log """
        if validators.validate_job_id(job_id) == None:
            self.log.error("Job_id validation failure, '%s'", job_id)
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return response.send_error(start_response, 404, constants.ERROR_BUILD_NOT_FOUND)
        console_log = ''
        try:
            console_log = file(self._console_log_file(job_id, build_id), 'rb').read()
        except IOError:
            # can be ignored, we just return empty log
            pass
        return response.send_response(start_response, 200, console_log, content_type="text/plain")

    def update_console_log(self, environ, start_response, job_id, build_id):
        """ Append content to the console log """
        if validators.validate_job_id(job_id) == None:
            self.log.error("Job_id validation failure, '%s'", job_id)
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return response.send_error(start_response, 404, constants.ERROR_BUILD_NOT_FOUND)
        try:
            file(self._console_log_file(job_id, build_id), 'ab').write(request.read_request_data(environ))
        except IOError:
            # can be ignored, we just return empty log
            pass
        return response.send_response(start_response, 204)

    def delete_build(self, start_response, job_id, build_id):
        """ Delete a specific build and all related data """
        if validators.validate_job_id(job_id) == None:
            self.log.debug('Invalid job_id: %r' % job_id)
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_ID)
        if not os.path.isdir(self._build_dir(job_id, build_id)):
            return response.send_error(start_response, 404, constants.ERROR_BUILD_NOT_FOUND)
        self.log.debug("delete build %s/%s" % (job_id, build_id))
        try:
            shutil.rmtree(self._build_dir(job_id, build_id))
        except OSError:
            return response.send_error(start_response, 404, constants.ERROR_BUILD_NOT_FOUND)
        return response.send_response(start_response, 204)

    def handle_request(self, environ, start_response, method, job_id, parts):
        """ Handle requests related to builds """
        if len(parts) == 0:
            if method == 'GET':
                return self.get_builds(start_response, job_id)
            elif method == 'POST':
                return self.trigger_build(start_response, job_id)
            else:
                return response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'DELETE':
                return self.delete_build(start_response, job_id, parts[0])
            else:
                return response.send_error(start_response, 400)
        elif parts[1] == 'artifacts':
            return self.jobs_builds_artifacts.handle_request(environ, start_response, method, job_id, parts[0], parts[2:])
        elif len(parts) == 2:
            if parts[1] == 'state' and method == 'GET':
                return self.get_build_state(start_response, job_id, parts[0])
            elif parts[1] == 'state' and method == 'PUT':
                return self.update_build_state(environ, start_response, job_id, parts[0])
            elif parts[1] == 'console' and method == 'GET':
                return self.get_console_log(start_response, job_id, parts[0])
            elif parts[1] == 'console' and method == 'POST':
                return self.update_console_log(environ, start_response, job_id, parts[0])
            else:
                return response.send_error(start_response, 400)

        return response.send_error(start_response, 400)

