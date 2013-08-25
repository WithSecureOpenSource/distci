"""
Distributed state and lock management

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

try:
    import zookeeper
except:
    pass
import threading
import uuid
import logging

ZOO_OPEN_ACL_UNSAFE = {"perms": 0x1f, "scheme": "world", "id": "anyone"}

SYNC_LOCK_SUCCESS = 0
SYNC_LOCK_CONNECTION_FAILURE = 1

class SyncError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, message)
        self.code = code
        self.message = message

    def __str__(self):
        return '%r (%r)' % (self.message, self.code)

class ZooKeeperLock(object):
    def __init__(self, zkservers, lockname):
        self.connected = False
        self.lockname = "/" + lockname
        self.uuid = str(uuid.uuid4())
        self.cv = threading.Condition()
        self.log = logging.getLogger('zookeeper')

        def connection_watcher(_handle, _type, _state, _path):
            self.cv.acquire()
            self.connected = True
            self.cv.notify()
            self.cv.release()

        self.cv.acquire()
        try:
            self.handle = zookeeper.init(",".join(zkservers), connection_watcher, 4000)
        except:
            self.log.exception('Failed to connect Zookeeper cluster (%r)' % zkservers)
            self.cv.release()
            raise SyncError(SYNC_LOCK_CONNECTION_FAILURE, "Failed to connect to Zookeeper cluster")

        self.cv.wait(4.0)
        if not self.connected:
            self.log.error('Failed to connect to Zookeeper cluster (%r)' % zkservers)
            self.cv.release()
            raise SyncError(SYNC_LOCK_CONNECTION_FAILURE, "Failed to connect to Zookeeper cluster")
        self.cv.release()

    def try_lock(self):
        while True:
            try:
                zookeeper.create(self.handle, self.lockname, self.uuid, [ZOO_OPEN_ACL_UNSAFE], zookeeper.EPHEMERAL)
            except:
                self.log.info('Failed to acquire lock (%r)' % self.lockname)
                return False

            try:
                (data, _) = zookeeper.get(self.handle, self.lockname, None)
                break
            except:
                self.log.exception('try_lock: create succeeded but get failed? (%r)' % self.lockname)
                continue

        if data == self.uuid:
            self.log.debug('Lock acquired (%r)' % self.lockname)
            return True
        else:
            self.log.error('try_lock: create succeeded but data is wrong? (%r)' % self.lockname)
            print "failed to acquire lock"
            return False

    def unlock(self):
        try:
            (data, _) = zookeeper.get(self.handle, self.lockname, None)
            if data == self.uuid:
                zookeeper.delete(self.handle, self.lockname)
        except:
            self.log.exception('unlock')

    def close(self):
        if self.connected:
            try:
                zookeeper.close(self.handle)
            except:
                self.log.exception('close')
            self.connected = False
            self.handle = None

class PhonyLock(object):
    def __init__(self, _lockname):
        pass

    def try_lock(self):
        return True

    def unlock(self):
        pass

    def close(self):
        pass

