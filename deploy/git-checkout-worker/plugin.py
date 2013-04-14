import os
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("git-checkout-install.sh", dest_path="/root/deploy/worker/git-checkout-worker/")
        self.add_file("git-checkout.supervisor", dest_path="/root/deploy/worker/git-checkout-worker/", render=self.render_text)
        self.add_file("git-checkout.conf", dest_path="/root/deploy/worker/git-checkout-worker/")
        self.add_dir(self.node['distci_eggs'], dest_path="/root/deploy/worker/eggs/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/worker/git-checkout-worker/git-checkout-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, 'supervisorctl start distci-git-checkout-worker')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, 'supervisorctl stop distci-git-checkout-worker')

