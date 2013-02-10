"""
Helpers for generating HTTP responses

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

_STATUS_CODES = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    500: "Server Error",
    501: "Not Implemented"
}

def send_response(start_response, code, content=None, content_type="application/json"):
    """ Send generic response """
    status = _STATUS_CODES[code]

    if content is None:
        headers = [("Content-Length", "0")]
        content = []
    else:
        headers = [("Content-Type", content_type),
                    ("Content-Length", str(len(content)))]
        content = [ content ]

    start_response('%d %s' % (code, status), headers)
    return content

def send_error(start_response, code, message=None):
    """ Build and send out error response """
    if message is not None:
        content = json.dumps({'error': message})
    else:
        content = None
    return send_response(start_response, code, content)
