from . import response, jobs_builds, jobs_tags

def get_jobs(environ, start_response):
    print "get jobs"
    return response.send_error(start_response, 501)

def create_new_job(environ, start_response):
    print "create job"
    return response.send_error(start_response, 501)

def delete_job(environ, start_response, job_id):
    print "delete job"
    return response.send_error(start_response, 501)

def get_job_config(environ, start_response, job_id):
    print "get job config"
    return response.send_error(start_response, 501)

def update_job_config(environ, start_response, job_id):
    print "update job config"
    return response.send_error(start_response, 501)

def handle_request(environ, start_response, method, parts):
    if len(parts) == 0:
        if method == 'GET':
            return get_jobs(environ, start_response)
        elif method == 'POST':
            return create_new_job(environ, start_response)
        else:
            return response.send_error(start_response, 400)
    elif len(parts) == 1:
        if method == 'GET':
            return get_job_config(environ, start_response, parts[0])
        elif method == 'PUT':
            return update_job_config(environ, start_response, parts[0])
        elif method == 'DELETE':
            return delete_job(environ, start_response, parts[0])
        else:
            return response.send_error(start_response, 400)
    elif parts[1] == 'builds':
        return jobs_builds.handle_request(environ, start_response, method, parts[0], parts[2:])
    elif parts[1] == 'tags':
        return jobs_tags.handle_request(environ, start_response, method, parts[0], parts[2:])

    return response.send_error(start_response, 400)
