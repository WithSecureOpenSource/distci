#!/bin/sh

if [ -z "$PONI_ROOT" ]
then
    echo PONI_ROOT environmental variable is not set
    exit 127
fi

if [ -z "$DISTCI_EGGS" ]
then
    echo DISTCI_EGGS environmental variable is not set
    exit 127
fi

echo "Creating CEPH deployment keys"
if [ -f ceph-storage/ceph-setup-key ]; then rm ceph-storage/ceph-setup-key; fi
if [ -f ceph-storage/ceph-setup-key.pub ]; then rm ceph-storage/ceph-setup-key.pub; fi
ssh-keygen -f ceph-storage/ceph-setup-key -N ""

echo "Initializing poni repository..."
poni init

echo "Adding system 'distci'"
poni add-system distci

echo "Adding system 'distci/frontend'"
poni add-system distci/frontend

echo "Adding system 'distci/zookeeper'"
poni add-system distci/zookeeper

echo "Adding system 'distci/worker'"
poni add-system distci/worker

echo "Adding system 'distci/ceph-storage'"
poni add-system distci/ceph-storage

echo "Adding nodes 'distci/frontend/fenodeN'"
poni add-node distci/frontend/fenode0
poni set distci/frontend/fenode0 cloud.vm_name=fenode0

poni add-node distci/frontend/fenode1
poni set distci/frontend/fenode1 cloud.vm_name=fenode1

echo "Adding nodes 'distci/zookeeper/zknodeN'"
poni add-node distci/zookeeper/zknode0
poni set distci/zookeeper/zknode0 cloud.vm_name=zknode0 zkindex=1

poni add-node distci/zookeeper/zknode1
poni set distci/zookeeper/zknode1 cloud.vm_name=zknode1 zkindex=2

poni add-node distci/zookeeper/zknode2
poni set distci/zookeeper/zknode2 cloud.vm_name=zknode2 zkindex=3

echo "Adding nodes 'distci/worker/wnodeN'"
poni add-node distci/worker/wnode0
poni set distci/worker/wnode0 cloud.vm_name=wnode0

poni add-node distci/worker/wnode1
poni set distci/worker/wnode1 cloud.vm_name=wnode1

poni add-node distci/worker/wnode2
poni set distci/worker/wnode2 cloud.vm_name=wnode2

echo "Adding nodes 'distci/ceph-storage/cnodeN'"
poni add-node distci/ceph-storage/cnode0
poni set distci/ceph-storage/cnode0 cloud.vm_name=cnode0 cindex=0

poni add-node distci/ceph-storage/cnode1
poni set distci/ceph-storage/cnode1 cloud.vm_name=cnode1 cindex=1

poni add-node distci/ceph-storage/cnode2
poni set distci/ceph-storage/cnode2 cloud.vm_name=cnode2 cindex=2

echo "Configuring nodes 'distci/*'"
poni add-config distci/ nodes-prepare
poni update-config nodes-prepare nodes-prepare/plugin.py nodes-prepare/node-prepare.sh nodes-prepare/apt-wheezy-sources nodes-prepare/hosts

echo "Configuring nodes 'distci/frontend/*'"
poni add-config distci/frontend/ frontend-setup
poni update-config frontend-setup frontend/plugin.py frontend/frontend-install.sh frontend/distci-frontend.supervisor frontend/distci-frontend.conf frontend/distci-frontend.nginx
poni set distci/frontend distci_eggs=$DISTCI_EGGS

echo "Configuring nodes 'distci/zookeeper/*'"
poni add-config distci/zookeeper/ zookeeper-setup
poni update-config zookeeper-setup zookeeper/plugin.py zookeeper/zookeeper-install.sh zookeeper/zookeeper.conf zookeeper/zookeeper-myid

echo "Configuring nodes 'distci/worker/*'"
poni add-config distci/worker/ build-control-worker-setup
poni update-config build-control-worker-setup build-control-worker/plugin.py build-control-worker/build-control-install.sh build-control-worker/build-control.conf build-control-worker/build-control.supervisor

poni add-config distci/worker/ git-checkout-worker-setup
poni update-config git-checkout-worker-setup git-checkout-worker/plugin.py git-checkout-worker/git-checkout-install.sh git-checkout-worker/git-checkout.conf git-checkout-worker/git-checkout.supervisor

poni add-config distci/worker/ execute-shell-worker-setup
poni update-config execute-shell-worker-setup execute-shell-worker/plugin.py execute-shell-worker/execute-shell-install.sh execute-shell-worker/execute-shell.conf execute-shell-worker/execute-shell.supervisor

poni add-config distci/worker/ publish-artifacts-worker-setup
poni update-config publish-artifacts-worker-setup publish-artifacts-worker/plugin.py publish-artifacts-worker/publish-artifacts-install.sh publish-artifacts-worker/publish-artifacts.conf publish-artifacts-worker/publish-artifacts.supervisor

poni set distci/worker distci_eggs=$DISTCI_EGGS

echo "Configuring nodes 'distci/ceph-storage/*'"
poni add-config distci/ceph-storage/ ceph-storage-setup
poni update-config ceph-storage-setup ceph-storage/plugin.py ceph-storage/ceph-storage-install-stage1.sh ceph-storage/ceph-storage-install-stage2.sh ceph-storage/ceph-storage-install-stage3.sh ceph-storage/ceph.conf ceph-storage/apt-ceph-sources ceph-storage/ceph-repo-key.asc ceph-storage/ceph-setup-key ceph-storage/ceph-setup-key.pub

echo "Configuring cloud properties"
poni set distci cloud.provider=eucalyptus cloud.image=emi-292D3844 cloud.type=m1.small cloud.key_pair=noushe-euca user=root

