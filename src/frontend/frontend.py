import json

from . import dispatcher

class Frontend(object):
    def __init__(self, config):
        self.config = config
        self.dispatcher = dispatcher.Dispatcher(config)

    def handle_request(self, environ, start_request):
        return self.dispatcher.handle_request(environ, start_request)

