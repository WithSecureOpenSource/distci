import os 
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("frontend-install.sh", dest_path="/root/deploy/frontend/")
        self.add_file("distci-frontend.supervisor", dest_path="/root/deploy/frontend/")
        self.add_file("distci-frontend.conf", dest_path="/root/deploy/frontend/")
        self.add_file("distci-frontend.nginx", dest_path="/root/deploy/frontend/", render=self.render_text)
        self.add_dir(self.node['distci_eggs'], dest_path="/root/deploy/frontend/eggs/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/frontend/frontend-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, 'supervisorctl start distci-frontend')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, 'supervisorctl stop distci-frontend')

