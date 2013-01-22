import json

class GenericTask(object):
    def __init__(self, task_data):
        self.id = None
        self.config = task_data 

    def dumps(self):
        return json.dumps(self.config)

