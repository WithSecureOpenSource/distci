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

import webob

class Ui(object):
    """ Class for handling UI related requests """
    def __init__(self, config):
        self.config = config

    @classmethod
    def send_file(cls, filename):
        """ send content """
        if resource_exists is None or not resource_exists('distci.frontend', filename):
            return webob.Response(status=404)
        if filename.endswith('.js'):
            content_type = "application/javascript"
        elif filename.endswith('.css'):
            content_type = "text/css"
        elif filename.endswith('.html'):
            content_type = "text/html"
        else:
            content_type = "application/octet-stream"
        return webob.Response(status=200, body=resource_string('distci.frontend', filename), content_type=content_type)

    def handle_request(self, request, parts):
        """ Parse and serve UI requests """
        if request.method != 'GET':
            return webob.Response(status=403)
        if len(parts) == 0 or parts[0] == '':
            return self.send_file(os.path.join('ui', 'index.html'))
        elif len(parts) == 2:
            if parts[0] in ['js', 'css', 'html']:
                filename = os.path.join('ui', parts[0], parts[1])
                return self.send_file(filename)
        return webob.Response(status=404)

