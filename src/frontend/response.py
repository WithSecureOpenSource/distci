import json

status_codes = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    404: "Not Found",
    500: "Server Error",
    501: "Not Implemented"
}

def send_response(start_response, code, content=None, content_type="application/json"):
    status = status_codes[code]

    if content is None:
        headers = []
        content = []
    else:
        headers = [("Content-Type", content_type),
                    ("Content-Length", str(len(content)))]
        content = [ content ]

    start_response('%d %s' % (code, status), headers)
    return content

def send_error(start_response, code, message=None):
    if message is not None:
        content = json.dumps({'error': message})
    else:
        content = None
    return send_response(start_response, code, content)
