"""
Helpers for validating various inputs

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import re

__TASK_ID_VALIDATOR = re.compile('^([a-f0-9]{8})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{12})$')
__JOB_ID_VALIDATOR = re.compile('^([a-zA-Z0-9-_]+)$')
__JOB_ID_MAX_LEN = 256
__BUILD_ID_VALIDATOR = re.compile('^([0-9]+)$')
__BUILD_ID_MAX_LEN = 16

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

def validate_build_id(build_id):
    """ Validate build id """
    if len(build_id) > __BUILD_ID_MAX_LEN:
        return None
    matches = __BUILD_ID_VALIDATOR.match(build_id)
    if matches is not None:
        return matches.group(0)
    return None

