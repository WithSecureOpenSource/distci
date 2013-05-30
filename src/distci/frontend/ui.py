"""
UI request management

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import os
try:
    from pkg_resources import resource_string, resource_exists
except ImportError:
    pass

from distci.frontend import response

class Ui(object):
    """ Class for handling UI related requests """
    def __init__(self, config):
        self.config = config

    @classmethod
    def send_file(cls, start_response, filename):
        """ send content """
        if resource_exists is None or not resource_exists('distci.frontend', filename):
            return response.send_error(start_response, 404)
        if filename.endswith('.js'):
            content_type = "application/javascript"
        elif filename.endswith('.css'):
            content_type = "text/css"
        elif filename.endswith('.html'):
            content_type = "text/html"
        else:
            content_type = "application/octet-stream"
        data = resource_string('distci.frontend', filename)
        return response.send_response(start_response, 200, data, content_type)

    def handle_request(self, _environ, start_response, method, parts):
        """ Parse and serve UI requests """
        if method != 'GET':
            return response.send_error(start_response, 403)
        if len(parts) == 0 or parts[0] == '':
            return self.send_file(start_response, os.path.join('ui', 'index.html'))
        elif len(parts) == 2:
            if parts[0] in ['js', 'css', 'html']:
                filename = os.path.join('ui', parts[0], parts[1])
                return self.send_file(start_response, filename)
        return response.send_error(start_response, 404)

