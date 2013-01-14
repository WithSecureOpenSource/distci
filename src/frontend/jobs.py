import logging

from . import response, jobs_builds, jobs_tags

class Jobs(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs')
        self.jobs_builds = jobs_builds.JobsBuilds(config)
        self.jobs_tags = jobs_tags.JobsTags(config)

    def get_jobs(self, environ, start_response):
        self.log.debug("get jobs")
        return response.send_error(start_response, 501)

    def create_new_job(self, environ, start_response):
        self.log.debug("create job")
        return response.send_error(start_response, 501)

    def delete_job(self, environ, start_response, job_id):
        self.log.debug("delete job")
        return response.send_error(start_response, 501)

    def get_job_config(self, environ, start_response, job_id):
        self.log.debug("get job config")
        return response.send_error(start_response, 501)

    def update_job_config(self, environ, start_response, job_id):
        self.log.debug("update job config")
        return response.send_error(start_response, 501)

    def handle_request(self, environ, start_response, method, parts):
        if len(parts) == 0:
            if method == 'GET':
                return self.get_jobs(environ, start_response)
            elif method == 'POST':
                return self.create_new_job(environ, start_response)
            else:
                return response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'GET':
                return self.get_job_config(environ, start_response, parts[0])
            elif method == 'PUT':
                return self.update_job_config(environ, start_response, parts[0])
            elif method == 'DELETE':
                return self.delete_job(environ, start_response, parts[0])
            else:
                return response.send_error(start_response, 400)
        elif parts[1] == 'builds':
            return self.jobs_builds.handle_request(environ, start_response, method, parts[0], parts[2:])
        elif parts[1] == 'tags':
            return self.jobs_tags.handle_request(environ, start_response, method, parts[0], parts[2:])

        return response.send_error(start_response, 400)

