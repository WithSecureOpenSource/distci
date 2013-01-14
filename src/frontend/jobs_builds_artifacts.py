import logging

from . import response

class JobsBuildsArtifacts(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_builds_artifacts')

    def handle_request(environ, start_response, method, job_id, build, parts):
        self.log.debug('method %r job_id %r build %r', method, job_id, build)
        return response.send_error(start_response, 501)

