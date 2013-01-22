import subprocess

from distci.worker import worker_base

class CalculatorWorker(worker_base.WorkerBase):
    def __init__(self, config):
        worker_base.WorkerBase.__init__(self)
        self.worker_config = config
        self.worker_config['capabilities'] = ['calculator']

    def start(self):
        while True:
            task = self.fetch_task(timeout=60)

            if task is None:
                continue

            equation = task.config.get('equation')
            if equation is None:
                task.config['status'] = 'error'
                del task.config['assignee']
                self.update_task(task)
            else:
                cmd_and_args = ['bc']
                proc = subprocess.Popen(cmd_and_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                (sout, serr) = proc.communicate('%s\n' % equation)
                task.config['status'] = 'complete'
                task.config['worker_uuid'] = self.uuid
                task.config['result'] = sout.strip()
                del task.config['assignee']
                self.update_task(task)
 
