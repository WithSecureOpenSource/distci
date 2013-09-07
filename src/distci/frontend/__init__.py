"""
DistCI

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json
from webob.dec import wsgify

from distci.frontend import dispatcher

class Frontend(object):
    def __init__(self, config):
        self.config = config
        self.dispatcher = dispatcher.Dispatcher(self.config)

    @wsgify
    def __call__(self, request):
        return self.dispatcher.handle_request(request)

def build_frontend_app(config_file):
    config = json.load(file(config_file))
    return Frontend(config)

