""" Helpers for parsing incoming requests """

def read_request_data(environ):
    """ Read request body """
    try:
        content_len = int(environ.get('CONTENT_LENGTH'))
        data = environ.get('wsgi.input').read(content_len)
        return data
    except (TypeError, AttributeError):
        return None

