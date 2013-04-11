import os
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("execute-shell-install.sh", dest_path="/root/deploy/worker/execute-shell-worker/")
        self.add_file("execute-shell.init", dest_path="/root/deploy/worker/execute-shell-worker/", render=self.render_text)
        self.add_file("execute-shell.conf", dest_path="/root/deploy/worker/execute-shell-worker/")
        self.add_dir(self.node['distci_eggs'], dest_path="/root/deploy/worker/eggs/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/worker/execute-shell-worker/execute-shell-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, '/etc/init.d/distci-execute-shell-worker start')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, '/etc/init.d/distci-execute-shell-worker stop')

