import re

# eadd0caa-a625-4501-a7bb-ec1e8a1a0712
_task_id_validator = re.compile('^([a-f0-9]{8})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{12})$')

def validate_task_id(task_id):
    matches = _task_id_validator.match(task_id)
    if matches is not None:
        return matches.group(0)
    return None

