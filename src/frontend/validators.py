""" Helpers for validating various inputs"""

import re

__TASK_ID_VALIDATOR = re.compile('^([a-f0-9]{8})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{12})$')
__JOB_ID_VALIDATOR = re.compile('^([a-zA-Z0-9-_]+)$')
__JOB_ID_MAX_LEN = 256

def validate_task_id(task_id):
    """ Validate task ID """
    matches = __TASK_ID_VALIDATOR.match(task_id)
    if matches is not None:
        return matches.group(0)
    return None

def validate_job_id(job_id):
    """ Validate job ID """
    if len(job_id) > __JOB_ID_MAX_LEN:
        return None
    matches = __JOB_ID_VALIDATOR.match(job_id)
    if matches is not None:
        return matches.group(0)
    return None

