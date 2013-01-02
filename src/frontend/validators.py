""" Helpers for validating various inputs"""

import re

__TASK_ID_VALIDATOR = re.compile('^([a-f0-9]{8})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{12})$')

def validate_task_id(task_id):
    """ Validate task ID """
    matches = __TASK_ID_VALIDATOR.match(task_id)
    if matches is not None:
        return matches.group(0)
    return None

