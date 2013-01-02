from . import response

def handle_request(environ, start_response, method, job_id, build, parts):
    response.send_error(start_response, 501)
