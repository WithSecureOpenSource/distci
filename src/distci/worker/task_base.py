"""
Base task object

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json

class GenericTask(object):
    def __init__(self, task_data):
        self.id = None
        self.config = task_data

    def dumps(self):
        return json.dumps(self.config)

