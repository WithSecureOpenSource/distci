import response

import jobs_builds_artifacts

def get_builds(environ, start_response, job_id):
    print "get builds %s" % job_id
    return response.send_error(start_response, 501)

def trigger_build(environ, start_response, job_id):
    print "trigger build %s" % job_id
    return response.send_error(start_response, 501)

def get_build_status(environ, start_response, job_id, build_id):
    print "get build status %s %s" % (job_id, build_id)
    return response.send_error(start_response, 501)

def update_build_status(environ, start_response, job_id, build_id):
    print "update build status %s %s" % (job_id, build_id)
    return response.send_error(start_response, 501)

def get_build_config(environ, start_response, job_id, build_id):
    print "get build config %s %s" % (job_id, build_id)
    return response.send_error(start_response, 501)

def get_console_log(environ, start_response, job_id, build_id):
    print "get console log %s %s" % (job_id, build_id)
    return response.send_error(start_response, 501)

def update_console_log(environ, start_response, job_id, build_id):
    print "update console log %s %s" % (job_id, build_id)
    return response.send_error(start_response, 501)

def delete_build(environ, start_response, job_id, build_id):
    print "delete build %s %s" % (job_id, build_id)
    return response.send_error(start_response, 501)

def handle_request(environ, start_response, method, job_id, parts):
    if len(parts) == 0:
        if method == 'GET':
            return get_builds(environ, start_response, job_id)
        elif method == 'POST':
            return trigger_build(environ, start_response, job_id)
        else:
            return response.send_error(start_response, 400)
    elif len(parts) == 1:
        if method == 'DELETE':
            return delete_build(environ, start_response, job_id, parts[0])
        else:
            return response.send_error(start_response, 400)
    elif parts[1] == 'artifacts':
        return jobs_builds_artifacts.handle_request(environ, start_response, method, job_id, parts[0], parts[2:])
    elif len(parts) == 2:
        if parts[1] == 'status' and method == 'GET':
            return get_build_status(environ, start_response, job_id, parts[0])
        elif parts[1] == 'status' and method == 'PUT':
            return update_build_status(environ, start_response, job_id, parts[0])
        elif parts[1] == 'config' and method == 'GET':
            return get_build_config(environ, start_response, job_id, parts[0])
        elif parts[1] == 'console' and method == 'GET':
            return get_console_log(environ, start_response, job_id, parts[0])
        elif parts[1] == 'console' and method == 'PUT':
            return update_console_log(environ, start_response, job_id, parts[0])
        else:
            return response.send_error(start_response, 400)

    return response.send_error(start_response, 400)
