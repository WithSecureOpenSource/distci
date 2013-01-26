from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("node-prepare.sh", dest_path="/root/deploy/common/")
        self.add_file("apt-wheezy-sources", dest_path="/root/deploy/common/")
        self.add_file("hosts", dest_path="/root/deploy/common/")

    @config.control()
    def setup(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/common/node-prepare.sh')

