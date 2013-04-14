import os
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("publish-artifacts-install.sh", dest_path="/root/deploy/worker/publish-artifacts-worker/")
        self.add_file("publish-artifacts.supervisor", dest_path="/root/deploy/worker/publish-artifacts-worker/")
        self.add_file("publish-artifacts.conf", dest_path="/root/deploy/worker/publish-artifacts-worker/")
        self.add_dir(self.node['distci_eggs'], dest_path="/root/deploy/worker/eggs/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/worker/publish-artifacts-worker/publish-artifacts-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, 'supervisorctl start distci-publish-artifacts-worker')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, 'supervisorctl stop distci-publish-artifacts-worker')

