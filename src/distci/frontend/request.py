"""
Helpers for parsing incoming requests

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

def read_request_data(environ):
    """ Read request body """
    try:
        content_len = int(environ.get('CONTENT_LENGTH'))
        data = environ.get('wsgi.input').read(content_len)
        return data
    except (TypeError, AttributeError):
        return None

def get_request_data_handle_and_length(environ):
    """ Return request body handle and content-length as a tuple """
    try:
        content_len = int(environ.get('CONTENT_LENGTH'))
        return environ.get('wsgi.input'), content_len
    except (TypeError, AttributeError):
        return None, None

