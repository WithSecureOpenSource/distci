"""
Handler for job tagging management

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import logging
import webob

class JobsTags(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('jobs_tags')

    def get_tags(self, job_id):
        self.log.debug("get tags %s", job_id)
        return webob.Response(status=501)

    def get_tag(self, job_id, tag_id):
        self.log.debug("get single tag %s %s", job_id, tag_id)
        return webob.Response(status=501)

    def update_tag(self, _request, job_id, tag_id):
        self.log.debug("update tag %s %s", job_id, tag_id)
        return webob.Response(status=501)

    def delete_tag(self, job_id, tag_id):
        self.log.debug("delete tag %s %s", job_id, tag_id)
        return webob.Response(status=501)

    def handle_request(self, request, job_id, parts):
        if len(parts) == 0:
            if request.method == 'GET':
                return self.get_tags(job_id)
            else:
                return webob.Response(status=400)
        elif len(parts) == 1:
            if request.method == 'GET':
                return self.get_tag(job_id, parts[0])
            if request.method == 'PUT':
                return self.update_tag(request, job_id, parts[0])
            if request.method == 'DELETE':
                return self.delete_tag(job_id, parts[0])
            else:
                return webob.Response(status=400)

        return webob.Response(status=400)

