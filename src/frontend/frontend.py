import json

from . import dispatcher

class Frontend(object):
    def __init__(self, config):
        self.config = config

    def handle_request(self, environ, start_request):
        environ['config'] = self.config
        return dispatcher.handle_request(environ, start_request)

