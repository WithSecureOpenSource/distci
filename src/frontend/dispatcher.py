""" Top-level request dispatcher """

from . import response, jobs, tasks
import logging

def handle_request(environ, start_response):
    """ Parse top level request for dispatching """
    if 'PATH_INFO' not in environ:
        return response.send_error(start_response, 500)

    method = environ['REQUEST_METHOD']

    parts = environ['PATH_INFO'].split('/')[1:]
    if len(parts) == 0:
        return response.send_error(start_response, 400)

    if parts[0] == 'jobs':
        return jobs.handle_request(environ, start_response, method, parts[1:]) 
    elif parts[0] == 'tasks':
        return tasks.handle_request(environ, start_response, method, parts[1:])
    elif parts[0] == '':
        return response.send_response(start_response, 204)

    return response.send_error(start_response, 400)
