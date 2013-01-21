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

echo "Initializing poni repository..."
poni init

echo "Adding system 'distci'"
poni add-system distci

echo "Adding system 'distci/frontend'"
poni add-system distci/frontend

echo "Adding system 'distci/zookeeper'"
poni add-system distci/zookeeper 

echo "Adding nodes 'distci/frontend/fenodeN'"
poni add-node distci/frontend/fenode0
poni set distci/frontend/fenode0 cloud.vm_name=fenode0

echo "Adding nodes 'distci/zookeeper/zknodeN'"
poni add-node distci/zookeeper/zknode0
poni set distci/zookeeper/zknode0 cloud.vm_name=zknode0 zkindex=1

poni add-node distci/zookeeper/zknode1
poni set distci/zookeeper/zknode1 cloud.vm_name=zknode1 zkindex=2

poni add-node distci/zookeeper/zknode2
poni set distci/zookeeper/zknode2 cloud.vm_name=zknode2 zkindex=3

echo "Configuring nodes 'distci/*'"
poni add-config distci/ nodes-prepare
poni update-config nodes-prepare nodes-prepare/plugin.py nodes-prepare/node-prepare.sh nodes-prepare/apt-wheezy-sources

echo "Configuring nodes 'distci/frontend/*'"
poni add-config distci/frontend frontend-setup
poni update-config frontend-setup frontend/plugin.py frontend/frontend-install.sh frontend/distci-frontend.init frontend/distci-frontend.conf frontend/distci-frontend.nginx

echo "Configuring nodes 'distci/zookeeper/*'"
poni add-config distci/zookeeper zookeeper-setup
poni update-config zookeeper-setup zookeeper/plugin.py zookeeper/zookeeper-install.sh zookeeper/zookeeper.conf zookeeper/zookeeper-myid

echo "Configuring cloud properties"
poni set distci cloud.provider=eucalyptus cloud.image=emi-B33133CB cloud.kernel=eki-8CC5369F cloud.ramdisk=eri-DF7638C3 cloud.type=m1.small cloud.key_pair=noushe-euca user=root

