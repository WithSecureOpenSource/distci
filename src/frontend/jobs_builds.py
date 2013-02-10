"""
Handle requests related to build operations

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import logging

from . import response, jobs_builds_artifacts

class JobsBuilds(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_builds')
        self.jobs_builds_artifacts = jobs_builds_artifacts.JobsBuildsArtifacts(config)

    def get_builds(self, environ, start_response, job_id):
        self.log.debug("get builds %s", job_id)
        return response.send_error(start_response, 501)

    def trigger_build(self, environ, start_response, job_id):
        self.log.debug("trigger build %s", job_id)
        return response.send_error(start_response, 501)

    def get_build_status(self, environ, start_response, job_id, build_id):
        self.log.debug("get build status %s %s", job_id, build_id)
        return response.send_error(start_response, 501)

    def update_build_status(self, environ, start_response, job_id, build_id):
        self.log.debug("update build status %s %s", job_id, build_id)
        return response.send_error(start_response, 501)

    def get_build_config(self, environ, start_response, job_id, build_id):
        self.log.debug("get build config %s %s", job_id, build_id)
        return response.send_error(start_response, 501)

    def get_console_log(self, environ, start_response, job_id, build_id):
        self.log.debug("get console log %s %s", job_id, build_id)
        return response.send_error(start_response, 501)

    def update_console_log(self, environ, start_response, job_id, build_id):
        self.log.debug("update console log %s %s", job_id, build_id)
        return response.send_error(start_response, 501)

    def delete_build(self, environ, start_response, job_id, build_id):
        self.log.debug("delete build %s %s", job_id, build_id)
        return response.send_error(start_response, 501)

    def handle_request(self, environ, start_response, method, job_id, parts):
        if len(parts) == 0:
            if method == 'GET':
                return self.get_builds(environ, start_response, job_id)
            elif method == 'POST':
                return self.trigger_build(environ, start_response, job_id)
            else:
                return response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'DELETE':
                return self.delete_build(environ, start_response, job_id, parts[0])
            else:
                return response.send_error(start_response, 400)
        elif parts[1] == 'artifacts':
            return self.jobs_builds_artifacts.handle_request(environ, start_response, method, job_id, parts[0], parts[2:])
        elif len(parts) == 2:
            if parts[1] == 'status' and method == 'GET':
                return self.get_build_status(environ, start_response, job_id, parts[0])
            elif parts[1] == 'status' and method == 'PUT':
                return self.update_build_status(environ, start_response, job_id, parts[0])
            elif parts[1] == 'config' and method == 'GET':
                return self.get_build_config(environ, start_response, job_id, parts[0])
            elif parts[1] == 'console' and method == 'GET':
                return self.get_console_log(environ, start_response, job_id, parts[0])
            elif parts[1] == 'console' and method == 'PUT':
                return self.update_console_log(environ, start_response, job_id, parts[0])
            else:
                return response.send_error(start_response, 400)

        return response.send_error(start_response, 400)

