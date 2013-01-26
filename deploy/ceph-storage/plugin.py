import os 
from poni import config

class PlugIn(config.PlugIn):
    def add_actions(self):
        self.add_file("ceph-storage-install-stage1.sh", dest_path="/root/deploy/ceph/")
        self.add_file("ceph-storage-install-stage2.sh", dest_path="/root/deploy/ceph/")
        self.add_file("ceph-storage-install-stage3.sh", dest_path="/root/deploy/ceph/")
        self.add_file("ceph-setup-key", dest_path="/root/deploy/ceph/")
        self.add_file("ceph-setup-key.pub", dest_path="/root/deploy/ceph/")
        self.add_file("ceph.conf", dest_path="/root/deploy/ceph/")
        self.add_file("ceph-repo-key.asc", dest_path="/root/deploy/ceph/")
        self.add_file("apt-ceph-sources", dest_path="/root/deploy/ceph/")

    @config.control()
    def install_stage1(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/ceph/ceph-storage-install-stage1.sh')

    @config.control()
    def install_stage2(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/ceph/ceph-storage-install-stage2.sh')

    @config.control()
    def install_stage3(self, arg):
        self.remote_execute(arg, 'sh /root/deploy/ceph/ceph-storage-install-stage3.sh')

    @config.control()
    def start(self, arg):
        self.remote_execute(arg, '/etc/init.d/ceph start')

    @config.control()
    def stop(self, arg):
        self.remote_execute(arg, '/etc/init.d/ceph stop')

