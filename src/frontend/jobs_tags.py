import response

def get_tags(environ, start_response, job_id):
    print "get tags %s" % job_id
    return response.send_error(start_response, 501)

def get_tag(environ, start_response, job_id, tag_id):
    print "get single tag %s %s" % (job_id, tag_id)
    return response.send_error(start_response, 501)

def update_tag(environ, start_response, job_id, tag_id):
    print "update tag %s %s" % (job_id, tag_id)
    return response.send_error(start_response, 501)

def delete_tag(environ, start_response, job_id, tag_id):
    print "delete tag %s %s" % (job_id, tag_id)
    return response.send_error(start_response, 501)

def handle_request(environ, start_response, method, job_id, parts):
    if len(parts) == 0:
        if method == 'GET':
            return get_tags(environ, start_response, job_id)
        else:
            return response.send_error(start_response, 400)
    elif len(parts) == 1:
        if method == 'GET':
            return get_tag(environ, start_response, job_id, parts[0])
        if method == 'PUT':
            return update_tag(environ, start_response, job_id, parts[0])
        if method == 'DELETE':
            return delete_tag(environ, start_response, job_id, parts[0])
        else:
            return response.send_error(start_response, 400)

    return response.send_error(start_response, 400)
