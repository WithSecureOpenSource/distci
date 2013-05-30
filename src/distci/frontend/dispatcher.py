"""
Top-level request dispatcher

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

from distci.frontend import response, jobs, tasks, ui
import logging

class Dispatcher(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('dispatcher')
        self.tasks = tasks.Tasks(config)
        self.jobs = jobs.Jobs(config)
        self.ui = ui.Ui(config)

    def handle_request(self, environ, start_response):
        """ Parse top level request for dispatching """

        if 'PATH_INFO' not in environ:
            self.log.error('PATH_INFO not specified')
            return response.send_error(start_response, 500)

        method = environ['REQUEST_METHOD']

        parts = environ['PATH_INFO'].split('/')[1:]
        if len(parts) == 0:
            self.log.error('Invalid PATH_INFO, (%r)', environ['PATH_INFO'])
            return response.send_error(start_response, 400)

        if parts[0] == 'jobs':
            return self.jobs.handle_request(environ, start_response, method, parts[1:])
        elif parts[0] == 'tasks':
            return self.tasks.handle_request(environ, start_response, method, parts[1:])
        elif parts[0] == 'ui':
            return self.ui.handle_request(environ, start_response, method, parts[1:])
        elif parts[0] == '':
            return response.send_response(start_response, 204)

        self.log.warn('Unknown command %r', parts[0])
        return response.send_error(start_response, 400)

