"""
Top-level request dispatcher

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

from distci.frontend import jobs, tasks, ui
import logging
import webob

class Dispatcher(object):
    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger('dispatcher')
        self.tasks = tasks.Tasks(config)
        self.jobs = jobs.Jobs(config)
        self.ui = ui.Ui(config)

    def handle_request(self, request):
        """ Parse top level request for dispatching """

        if not request.path_info:
            self.log.error('PATH_INFO not specified')
            return webob.Response(status=500)

        parts = request.path_info.split('/')[1:]
        if len(parts) == 0:
            self.log.error('Invalid PATH_INFO, (%r)', request.path_info)
            return webob.Response(status=400)

        if parts[0] == 'jobs':
            return self.jobs.handle_request(request, parts[1:])
        elif parts[0] == 'tasks':
            return self.tasks.handle_request(request, parts[1:])
        elif parts[0] == 'ui':
            return self.ui.handle_request(request, parts[1:])
        elif parts[0] == '':
            return webob.Response(status=204)

        self.log.warn('Unknown command %r', parts[0])
        return webob.Response(status=404)

