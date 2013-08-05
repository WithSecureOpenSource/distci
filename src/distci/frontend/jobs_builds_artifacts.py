"""
Handle requests related to build artifacts

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import logging
import uuid
import os
import json
import webob

from distci.frontend import validators, constants

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

    def create_or_update_artifact(self, request, job_id, build_id, artifact_id_param = None):
        """ Create or update an artifact """
        if artifact_id_param is not None:
            artifact_id = artifact_id_param
            if validators.validate_artifact_id(artifact_id) != artifact_id:
                return webob.Response(status=400, body=constants.ERROR_ARTIFACT_INVALID_ID)
            if not os.path.isfile(self._build_artifact_file(job_id, build_id, artifact_id)):
                return webob.Response(status=404, body=constants.ERROR_ARTIFACT_NOT_FOUND)
        else:
            artifact_id = str(uuid.uuid4())

        if not os.path.isdir(self._build_artifact_dir(job_id, build_id)):
            try:
                os.mkdir(self._build_artifact_dir(job_id, build_id))
            except IOError:
                return webob.Response(status=400, body=constants.ERROR_ARTIFACT_WRITE_FAILED)

        data_len = request.content_length
        ifh = request.body_file

        try:
            ofh = open(self._build_artifact_file(job_id, build_id, artifact_id), 'wb')
        except IOError:
            return webob.Response(status=400, body=constants.ERROR_ARTIFACT_WRITE_FAILED)

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
            return webob.Response(status=400, body=constants.ERROR_ARTIFACT_WRITE_FAILED)

        ofh.close()

        return webob.Response(status=200 if artifact_id_param else 201, body=json.dumps({'job_id': job_id, 'build_number': int(build_id), 'artifact_id': artifact_id}), content_type="application/json")

    def get_artifact(self, job_id, build_id, artifact_id):
        """ Get artifact data """
        if validators.validate_artifact_id(artifact_id) != artifact_id:
            return webob.Response(status=400, body=constants.ERROR_ARTIFACT_INVALID_ID)
        if not os.path.isfile(self._build_artifact_file(job_id, build_id, artifact_id)):
            return webob.Response(status=404, body=constants.ERROR_ARTIFACT_NOT_FOUND)
        try:
            ifh = open(self._build_artifact_file(job_id, build_id, artifact_id))
        except IOError:
            return webob.Response(status=400, body=constants.ERROR_ARTIFACT_READ_FAILED)

        file_len = os.path.getsize(self._build_artifact_file(job_id, build_id, artifact_id))

        return webob.Response(status=200, body_file=ifh, content_length=file_len)

    def delete_artifact(self, job_id, build_id, artifact_id):
        """ Delete artifact """
        if validators.validate_artifact_id(artifact_id) != artifact_id:
            return webob.Response(status=400, body=constants.ERROR_ARTIFACT_INVALID_ID)
        if not os.path.isfile(self._build_artifact_file(job_id, build_id, artifact_id)):
            return webob.Response(status=404, body=constants.ERROR_ARTIFACT_NOT_FOUND)
        try:
            os.unlink(self._build_artifact_file(job_id, build_id, artifact_id))
        except IOError:
            return webob.Response(status=400, body=constants.ERROR_ARTIFACT_WRITE_FAILED)

        return webob.Response(status=204)

    def handle_request(self, request, job_id, build_id, parts):
        """ Handle requests related to build artifacts """
        if validators.validate_job_id(job_id) == None:
            self.log.error('Invalid job_id: %r' % job_id)
            return webob.Response(status=400, body=constants.ERROR_JOB_INVALID_ID)
        if validators.validate_build_id(build_id) != build_id:
            self.log.error("Build_id validation failure, '%s'", build_id)
            return webob.Response(status=400, body=constants.ERROR_BUILD_INVALID_ID)

        if len(parts) == 0:
            if request.method == 'POST':
                return self.create_or_update_artifact(request, job_id, build_id)
        elif len(parts) == 1:
            if request.method == 'GET':
                return self.get_artifact(job_id, build_id, parts[0])
            elif request.method == 'PUT':
                return self.create_or_update_artifact(request, job_id, build_id, parts[0])
            elif request.method == 'DELETE':
                return self.delete_artifact(job_id, build_id, parts[0])
        elif len(parts) == 2:
            if request.method == 'GET':
                return self.get_artifact(job_id, build_id, parts[0])

        return webob.Response(status=400)

