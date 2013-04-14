import os
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("build-control-install.sh", dest_path="/root/deploy/worker/build-control-worker/")
        self.add_file("build-control.supervisor", dest_path="/root/deploy/worker/build-control-worker/")
        self.add_file("build-control.conf", dest_path="/root/deploy/worker/build-control-worker/")
        self.add_dir(self.node['distci_eggs'], dest_path="/root/deploy/worker/eggs/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/worker/build-control-worker/build-control-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, 'supervisorctl start distci-build-control-worker')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, 'supervisorctl stop distci-build-control-worker')

