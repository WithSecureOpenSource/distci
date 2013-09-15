=============
DistCI readme
=============

Overview
========

DistCI is a distributed continuous integration system. Main design concerns are fault-tolerance and performance via easy horizontal scalability.

DistCI builds heavily on CEPH (http://ceph.com) for data storage and persistence and Apache ZooKeeper (http://zookeeper.apache.org/) for coordination and synchronization.

License
=======

DistCI is licensed under the Apache License, Version 2.0. Full license text is available in the ``LICENSE`` file and at http://www.apache.org/licenses/LICENSE-2.0.txt.

Goals
=====

Availability and Fault Tolerance
--------------------------------

DistCI should be responsive and capable of making progress in the case of individual node failures. There must not be single points of failures, nor single master tracking state of workers. Loss of state/progress should be limited to the failing node: either a request in fligth for frontend operations, or loss of progress for single or handful of workers on specific tasks.

Fault Recovery
--------------

DistCI should promptly recover from node failures, and regain proper state through request retries. Where progress is lost due to node losses, it should be restartable.

Scalability
-----------

DistCI must scale to thousands of registered jobs and hundreds of concurrent builds. It must support thousands of clients.

Design
======

Reversal of control flow
------------------------

DistCI departs from common CI software by eliminating any active master components. Rather, it offers a repository that is queried and manipulated by clients and workers. This eliminates the bottleneck in scheduling and tracking work, and is the main enabler for DistCI goals of availability and horizontal scale.

Shared repository is stored using Ceph storage cluster. Where resource contention - changing job configuration, is possible, DistCI uses ZooKeeper for distributed locking and synchronization.

Work is posted as tickets and remain posted until the task is completed. This allows complete restart of tasks that become stale through worker failures. The tasks are stored in ZooKeeper, and claims synchronizedi utilizing ZK operations.

Simplified workers
------------------

With no active master, a set of workers are responsible for pulling and completing work towards build progress. Rather than having complex or pluggable workers capable of complex operations, DistCI further divides work into small sub-build tasks. Different types of workers are built with Unix like philosophy: Do one thing and do it well. Independent workers can be chained for rich overall functionality.

With no active master, DistCI workers do not need pre-registration, and can be scaled in number based on real demand.

Worker execution model allows work to be run under newly created VM instances and/or LXC containers, providing for full environmental control during builds with no side-effects to latter build tasks.

Features
========
- Job configuration as JSON files
- Basic build workers:
  - Build control worker: tasked for spawning other workers based on job config
  - Git checkout worker: checkout source code from git repositories
  - Execute shell worker: execute build scripts
  - Publish artifacts worker: collect and publish build artifacts
  - Copy artifacts worker: import artifacts from other jobs for job chaining
- Build triggers:
  - Manual
  - GitHub webhooks
  - Post build triggers for job chaining
- Labels for execute shell workers, multiplatform / environment builds

