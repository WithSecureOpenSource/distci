import os
import uuid
import json
import shutil

import validators

import response
import request

ERROR_INVALID_TASK_ID  = 'Invalid task ID'
ERROR_TASK_NOT_FOUND   = 'Task not found'
ERROR_INVALID_PAYLOAD  = 'Decoding task data failed'
ERROR_TASK_WRONG_ACTOR = 'Task ownership mismatch'

def _data_dir(environ):
    return os.path.join(environ['config'].get('data_directory'), 'tasks')

def _task_dir(environ, task_id):
    return os.path.join(_data_dir(environ), task_id)

def _task_config_file(environ, task_id):
    return os.path.join(_task_dir(environ, task_id), 'task.description')

def _load_task_config(environ, task_id):
    return json.loads(file(_task_config_file(environ, task_id), 'rb').read())

def _save_task_config(environ, task_id, task_config):
    file(_task_config_file(environ, task_id), 'wb').write(json.dumps(task_config))

def _prepare_task_data(environ, task_id):
    return {'id': task_id, 'data': _load_task_config(environ, task_id)}

def get_tasks(environ, start_response):
    result = { 'tasks': [] }
    task_ids = os.listdir(_data_dir(environ))
    for task_id in task_ids:
        if not os.path.isdir(_task_dir(environ, task_id)):
            continue
        result['tasks'].append(_prepare_task_data(environ, task_id))
    return response.send_response(start_response, 200, json.dumps(result))

def create_new_task(environ, start_response):
    task_id_candidate = str(uuid.uuid4())
    try:
        task_description = json.loads(request.read_request_data(environ))
    except ValueError:
        return response.send_error(start_response, 400, ERROR_INVALID_PAYLOAD)
    os.mkdir(_task_dir(environ, task_id_candidate))
    _save_task_config(environ, task_id_candidate, task_description)
    return response.send_response(start_response, 201, json.dumps(_prepare_task_data(environ, task_id_candidate)))

def delete_task(environ, start_response, task_id):
    if validators.validate_task_id(task_id) != task_id:
        return response.send_error(start_response, 400, ERROR_INVALID_TASK_ID)
    if not os.path.isdir(_task_dir(environ, task_id)):
        return response.send_error(start_response, 404, ERROR_TASK_NOT_FOUND)
    shutil.rmtree(_task_dir(environ, task_id))
    return response.send_response(start_response, 204)

def get_task(environ, start_response, task_id):
    if validators.validate_task_id(task_id) != task_id:
        return response.send_error(start_response, 400, ERROR_INVALID_TASK_ID)
    if not os.path.isdir(_task_dir(environ, task_id)):
        return response.send_error(start_response, 404, ERROR_TASK_NOT_FOUND)
    return response.send_response(start_response, 200, json.dumps(_prepare_task_data(environ, task_id)))

def update_task(environ, start_response, task_id):
    if validators.validate_task_id(task_id) != task_id:
        return response.send_error(start_response, 400, ERROR_INVALID_TASK_ID)
    if not os.path.isdir(_task_dir(environ, task_id)):
        return response.send_error(start_response, 404, ERROR_TASK_NOT_FOUND)
    try:
        task_description = json.loads(request.read_request_data(environ))
    except ValueError:
        return response.send_error(start_response, 400, ERROR_INVALID_PAYLOAD)
    _save_task_config(environ, task_id, task_description)
    return response.send_response(start_response, 200, json.dumps(_prepare_task_data(environ, task_id)))

def handle_request(environ, start_response, method, parts):
    if len(parts) == 0:
        if method == 'GET':
            return get_tasks(environ, start_response)
        elif method == 'POST':
            return create_new_task(environ, start_response)
        else:
            return response.send_error(start_response, 400)
    elif len(parts) == 1:
        if method == 'GET':
            return get_task(environ, start_response, parts[0])
        elif method == 'PUT':
            return update_task(environ, start_response, parts[0])
        elif method == 'DELETE':
            return delete_task(environ, start_response, parts[0])
        else:
            return response.send_error(start_response, 400)

    return response.send_error(start_response, 400)
