def read_request_data(environ):
    try:
       content_len = int(environ.get('CONTENT_LENGTH'))
       data = environ.get('wsgi.input').read(content_len)
       return data
    except (TypeError, AttributeError):
       return None

