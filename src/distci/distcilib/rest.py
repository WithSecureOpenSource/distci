"""
REST helpers for DistCILib

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import httplib
import urlparse
import random

class RESTHelper(object):
    """ Helper class for REST operations """
    def __init__(self, parent):
        self.parent = parent

    @classmethod
    def _do_request(cls, base_url, method, path, extra_headers=None, data=None, data_len=None, content_type='application/json'):
        """ Internal helper for HTTP/HTTPS requests """
        parsed = urlparse.urlsplit(base_url)
        resource = urlparse.urljoin(parsed.path, path)
        if parsed.scheme == 'http':
            conn = httplib.HTTPConnection(parsed.netloc)
        else:
            conn = httplib.HTTPSConnection(parsed.netloc)
        headers = {}
        if extra_headers:
            headers.update(extra_headers)
        if data is not None:
            headers.update({ "Content-Type": content_type })
            if data_len is not None:
                headers.update({ "Content-Length": str(data_len) })
            elif isinstance(data, str):
                headers.update({ "Content-Length": str(len(data)) })
            conn.request(method, resource, data, headers)
        else:
            headers.update({ "Content-Length": "0" })
            conn.request(method, resource, None, headers)
        response = conn.getresponse()
        return response

    def do_task_request(self, method, task_id, **kwargs):
        """ Perform a request on task frontends """
        base_url = random.choice(self.parent.config['task_frontends'])
        if task_id is None:
            path = 'tasks'
        else:
            path = 'tasks/%s' % task_id
        return self._do_request(base_url,
                                method,
                                path,
                                **kwargs)

    def do_job_request(self, method, job_id, **kwargs):
        """ Perform a job related request on frontends """
        base_url = random.choice(self.parent.config['frontends'])
        if job_id is None:
            path = 'jobs'
        else:
            path = 'jobs/%s' % job_id
        return self._do_request(base_url,
                                method,
                                path,
                                **kwargs)

    def do_build_request(self, method, job_id, build_id, subcommand, **kwargs):
        """ Perform a build related request on frontends """
        base_url = random.choice(self.parent.config['frontends'])
        path = 'jobs/%s/builds' % job_id
        if build_id is not None:
            path = '%s/%s' % (path, build_id)
            if subcommand is not None:
                path = '%s/%s' % (path, subcommand)
        return self._do_request(base_url,
                                method,
                                path,
                                **kwargs)

