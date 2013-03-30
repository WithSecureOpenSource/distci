"""
Handler for job tagging management

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import logging

from distci.frontend import response

class JobsTags(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_tags')

    def get_tags(self, environ, start_response, job_id):
        self.log.debug("get tags %s", job_id)
        return response.send_error(start_response, 501)

    def get_tag(self, environ, start_response, job_id, tag_id):
        self.log.debug("get single tag %s %s", job_id, tag_id)
        return response.send_error(start_response, 501)

    def update_tag(self, environ, start_response, job_id, tag_id):
        self.log.debug("update tag %s %s", job_id, tag_id)
        return response.send_error(start_response, 501)

    def delete_tag(self, environ, start_response, job_id, tag_id):
        self.log.debug("delete tag %s %s", job_id, tag_id)
        return response.send_error(start_response, 501)

    def handle_request(self, environ, start_response, method, job_id, parts):
        if len(parts) == 0:
            if method == 'GET':
                return self.get_tags(environ, start_response, job_id)
            else:
                return response.send_error(start_response, 400)
        elif len(parts) == 1:
            if method == 'GET':
                return self.get_tag(environ, start_response, job_id, parts[0])
            if method == 'PUT':
                return self.update_tag(environ, start_response, job_id, parts[0])
            if method == 'DELETE':
                return self.delete_tag(environ, start_response, job_id, parts[0])
            else:
                return response.send_error(start_response, 400)

        return response.send_error(start_response, 400)

