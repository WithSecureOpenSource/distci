import os 
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("calculator-worker-install.sh", dest_path="/root/deploy/worker/")
        self.add_file("distci-calculator-worker.init", dest_path="/root/deploy/worker/", render=self.render_text)
        self.add_file("distci-calculator-worker.conf", dest_path="/root/deploy/worker/")
        self.add_dir(self.node['distci_eggs'], dest_path="/root/deploy/worker/eggs/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/worker/calculator-worker-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, '/etc/init.d/distci-calculator-worker start')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, '/etc/init.d/distci-calculator-worker stop')

