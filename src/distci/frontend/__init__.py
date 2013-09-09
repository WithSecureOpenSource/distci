"""
DistCI

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json
from webob.dec import wsgify
import logging

from distci.frontend import dispatcher

class Frontend(object):
    def __init__(self, config):
        self.config = config
        self.dispatcher = dispatcher.Dispatcher(self.config)
        if config.get('log_level'):
            log_level = logging._levelNames.get(config.get('log_level').upper())
            logging.basicConfig(level=log_level, format='%(asctime)s\t%(threadName)s\t%(name)s\t%(levelname)s\t%(message)s')

    @wsgify
    def __call__(self, request):
        return self.dispatcher.handle_request(request)

def build_frontend_app(config_file):
    config = json.load(file(config_file))
    return Frontend(config)

