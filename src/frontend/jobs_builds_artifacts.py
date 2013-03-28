"""
Handle requests related to build artifacts

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import logging
import uuid
import os
import json

from . import validators, request, response, constants

class JobsBuildsArtifacts(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_builds_artifacts')

    def _job_dir(self, job_id):
        """ Return directory for a specific job """
        return os.path.join(self.config.get('data_directory'), 'jobs', job_id)

    def _build_dir(self, job_id, build_id):
        """ Return directory for a specific build """
        return os.path.join(self._job_dir(job_id), build_id)

    def _build_artifact_dir(self, job_id, build_id):
        """ Return directory for artifacts for a specific build """
        return os.path.join(self._build_dir(job_id, build_id), 'artifacts')

    def _build_artifact_file(self, job_id, build_id, artifact_id):
        """ Return filename for a build state file """
        return os.path.join(self._build_artifact_dir(job_id, build_id), artifact_id)

    def create_or_update_artifact(self, environ, start_response, job_id, build_id, artifact_id_param = None):
        """ Create or update an artifact """
        if artifact_id_param is not None:
            artifact_id = artifact_id_param
            if validators.validate_artifact_id(artifact_id) != artifact_id:
                return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_INVALID_ID)
            if not os.path.isfile(self._build_artifact_file(job_id, build_id, artifact_id)):
                return response.send_error(start_response, 404, constants.ERROR_ARTIFACT_NOT_FOUND)
        else:
            artifact_id = str(uuid.uuid4())

        if not os.path.isdir(self._build_artifact_dir(job_id, build_id)):
            try:
                os.mkdir(self._build_artifact_dir(job_id, build_id))
            except IOError:
                return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_WRITE_FAILED)

        ifh, data_len = request.get_request_data_handle_and_length(environ)

        try:
            ofh = open(self._build_artifact_file(job_id, build_id, artifact_id), 'wb')
        except IOError:
            return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_WRITE_FAILED)

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
            return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_WRITE_FAILED)

        ofh.close()

        return response.send_response(start_response, 200 if artifact_id_param else 201, json.dumps({'job_id': job_id, 'build_number': int(build_id), 'artifact_id': artifact_id}))

    def get_artifact(self, environ, start_response, job_id, build_id, artifact_id):
        """ Get artifact data """
        if validators.validate_artifact_id(artifact_id) != artifact_id:
            return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_INVALID_ID)
        if not os.path.isfile(self._build_artifact_file(job_id, build_id, artifact_id)):
            return response.send_error(start_response, 404, constants.ERROR_ARTIFACT_NOT_FOUND)
        try:
            ifh = open(self._build_artifact_file(job_id, build_id, artifact_id))
        except IOError:
            return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_READ_FAILED)

        file_len = os.path.getsize(self._build_artifact_file(job_id, build_id, artifact_id))

        return response.send_response_file(environ, start_response, 200, ifh, file_len)

    def delete_artifact(self, start_response, job_id, build_id, artifact_id):
        """ Delete artifact """
        if validators.validate_artifact_id(artifact_id) != artifact_id:
            return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_INVALID_ID)
        if not os.path.isfile(self._build_artifact_file(job_id, build_id, artifact_id)):
            return response.send_error(start_response, 404, constants.ERROR_ARTIFACT_NOT_FOUND)
        try:
            os.unlink(self._build_artifact_file(job_id, build_id, artifact_id))
        except IOError:
            return response.send_error(start_response, 400, constants.ERROR_ARTIFACT_WRITE_FAILED)

        return response.send_response(start_response, 204)

    def handle_request(self, environ, start_response, method, job_id, build_id, parts):
        """ Handle requests related to build artifacts """
        if validators.validate_job_id(job_id) == None:
            self.log.error('Invalid job_id: %r' % job_id)
            return response.send_error(start_response, 400, constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return response.send_error(start_response, 400, constants.ERROR_BUILD_INVALID_ID)

        if len(parts) == 0:
            if method == 'POST':
                return self.create_or_update_artifact(environ, start_response, job_id, build_id)
            else:
                return response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'GET':
                return self.get_artifact(environ, start_response, job_id, build_id, parts[0])
            elif method == 'PUT':
                return self.create_or_update_artifact(environ, start_response, job_id, build_id, parts[0])
            elif method == 'DELETE':
                return self.delete_artifact(start_response, job_id, build_id, parts[0])
            else:
                return response.send_error(start_response, 400)

        return response.send_response(start_response, 400)

