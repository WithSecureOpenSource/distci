"""
Main request entry point for DistCI frontend

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

from distci.frontend import dispatcher

class Frontend(object):
    def __init__(self, config):
        self.config = config
        self.dispatcher = dispatcher.Dispatcher(config)

    def handle_request(self, environ, start_request):
        return self.dispatcher.handle_request(environ, start_request)

