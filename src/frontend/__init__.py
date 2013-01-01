import json

from . import dispatcher

class Frontend(object):
    def __init__(self, config_file):
        self.config = json.load(file(config_file, 'rb'))

    def handle_request(self, environ, start_request):
        environ['config'] = self.config
        return dispatcher.handle_request(environ, start_request)

