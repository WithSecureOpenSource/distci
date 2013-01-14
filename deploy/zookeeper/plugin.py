from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("zookeeper-install.sh", dest_path="/root/deploy/zookeeper/")
        self.add_file("zookeeper.conf", dest_path="/root/deploy/zookeeper/")
        self.add_file("zookeeper-myid", dest_path="/root/deploy/zookeeper/")

    @config.control()
    def install(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/zookeeper/zookeeper-install.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, '/etc/init.d/zookeeper start')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, '/etc/init.d/zookeeper stop')

