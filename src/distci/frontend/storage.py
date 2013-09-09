"""
Storage abstraction.

Supports CephFS via libcephfs and local filesystem

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

try:
    import cephfs
except ImportError:
    pass
import os
import stat
import ctypes
import shutil
import errno

class NotFound(Exception):
    """ object not found """

class ObjectExists(Exception):
    """ object already exists """

class CephFSFile(object):
    """ Limited file object wrapper around CephFS targets """
    def __init__(self, monitors):
        self.conn = None
        self.fdesc = None
        self.monitors = str(monitors)

    def __del__(self):
        """ destructor """
        self.close()

    def __enter__(self):
        """ enter hook for with statements """
        return self

    def __exit__(self, _type, _value, _traceback):
        """ exit hook for with statements """
        self.close()
        return False

    def close(self):
        """ close file object """
        if self.fdesc:
            self.conn.close(self.fdesc)
            self.fdesc = None
        if self.conn:
            self.conn.shutdown()
            self.conn = None

    def open(self, path, mode='r'):
        """ open a file """
        if self.fdesc:
            self.conn.close(self.fdesc)
            self.fdesc = None
        if not self.conn:
            self.conn = cephfs.LibCephFS({"mon_host": self.monitors})
            self.conn.mount()
        if mode in ['r', 'rb']:
            flags = os.O_RDONLY
        elif mode in ['r+', 'r+b']:
            flags = os.O_RDWR
        elif mode in ['w', 'wb']:
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        elif mode in ['w+', 'w+b']:
            flags = os.O_RDWR | os.O_CREAT | os.O_TRUNC
        elif mode in ['a', 'ab']:
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        elif mode in ['a+', 'a+b']:
            flags = os.O_RDWR | os.O_CREAT | os.O_APPEND

        try:
            self.fdesc = self.conn.open(str(path), flags, 0644)
        except cephfs.ObjectNotFound:
            raise NotFound

    def read(self, limit=-1):
        """ Read at most 'limit' bytes. If zero or negative, read until EOF. """
        if self.fdesc is None:
            return ''
        retbuf = ''
        if limit and limit > 0:
            readbuf = ctypes.create_string_buffer(limit)
        else:
            readbuf = ctypes.create_string_buffer(128*1024)
        while True:
            readlen = 128*1024
            if limit and limit > 0:
                if len(retbuf) >= limit:
                    return retbuf
                else:
                    if limit - len(readbuf) < readlen:
                        readlen = limit - len(retbuf)
            ret = self.conn.libcephfs.ceph_read(self.conn.cluster, self.fdesc, readbuf, ctypes.c_longlong(readlen), ctypes.c_longlong(-1))
            if ret == 0:
                return retbuf
            elif ret > 0:
                retbuf += readbuf[0:ret]
            else:
                raise cephfs.make_ex(ret, "error in read")
        return retbuf

    def seek(self, offset, whence=0):
        """ seek """
        if self.fdesc is None:
            return
        ret = self.conn.libcephfs.ceph_lseek(self.conn.cluster, self.fdesc, ctypes.c_longlong(offset), ctypes.c_int(whence))
        if ret < 0:
            raise cephfs.make_ex(ret, "error in seek")

    def write(self, data):
        """ write data """
        if self.fdesc is None:
            return
        offset = 0
        total = len(data)
        while offset < total:
            datalen = len(data) - offset
            if datalen > 128*1024:
                datalen = 128*1024
            ret = self.conn.libcephfs.ceph_write(self.conn.cluster, self.fdesc, ctypes.c_char_p(data[offset:offset+datalen]), ctypes.c_longlong(datalen), ctypes.c_longlong(-1))

            if ret >= 0:
                offset += ret
            else:
                raise cephfs.make_ex(ret, "error in write")

class CephFSStorage(object):
    """ Wrapper around cephfs bindings with some additional functionality """
    def __init__(self, monitors):
        self.monitors = str(monitors)
        self.conn = None

    def __del__(self):
        """ destructor """
        self.shutdown()

    def __enter__(self):
        """ enter hook for with statements """
        self.connect()
        return self

    def __exit__(self, _type, _value, _traceback):
        """ exit hook for with statements """
        self.shutdown()
        return False

    def connect(self):
        """ connect to Ceph cluster """
        if self.conn is None:
            self.conn = cephfs.LibCephFS({"mon_host": self.monitors})
            self.conn.mount()

    def exists(self, path):
        """ check whether path exists """
        try:
            _res = self.conn.stat(str(path))
        except cephfs.ObjectNotFound:
            return False
        return True

    def getsize(self, path):
        """ get size of a file """
        try:
            res = self.conn.stat(str(path))
        except cephfs.ObjectNotFound:
            raise NotFound
        return res['st_size']

    def isdir(self, path):
        """ check whether path exists and is a directory """
        try:
            res = self.conn.stat(str(path))
        except cephfs.ObjectNotFound:
            return False
        return stat.S_ISDIR(res['st_mode'])

    def isfile(self, path):
        """ check whether path exists and is a regular file """
        try:
            res = self.conn.stat(str(path))
        except cephfs.ObjectNotFound:
            return False
        return stat.S_ISREG(res['st_mode'])

    def listdir(self, path):
        """ return directory contents, excluding . and .. """
        entries = []
        dirp = ctypes.c_void_p()
        ret = self.conn.libcephfs.ceph_opendir(self.conn.cluster,
                                               str(path),
                                               ctypes.byref(dirp))
        if ret < 0:
            if ret == -errno.ENOENT:
                raise NotFound
            raise cephfs.make_ex(ret, "error in opendir: %s" % path)

        buf = ctypes.create_string_buffer(1024)
        ret = self.conn.libcephfs.ceph_getdnames(self.conn.cluster,
                                                 dirp,
                                                 buf,
                                                 ctypes.c_int(1024))
        if ret < 0:
            raise cephfs.make_ex(ret, "error in getdnames: %s" % path)

        start = 0
        offset = 0
        while offset < ret:
            if buf[offset] == '\0' or offset == ret:
                fname = buf[start:offset]
                if fname != '.' and fname != '..':
                    entries.append(fname)
                start = offset + 1
            offset += 1

        ret = self.conn.libcephfs.ceph_closedir(self.conn.cluster, dirp)
        if ret < 0:
            raise cephfs.make_ex(ret, "error in closedir: %s" % path)

        return entries

    def mkdir(self, path, mode=0755):
        """ create directory """
        try:
            self.conn.mkdir(str(path), mode)
        except cephfs.ObjectNotFound:
            raise NotFound
        except cephfs.ObjectExists:
            raise ObjectExists

    # makedirs, based on os.makedirs
    def makedirs(self, path, mode=0755):
        """ create directory, with intermediary directories if missing """
        head, tail = os.path.split(path)
        if not tail:
            head, tail = os.path.split(head)
        if head and tail and not self.exists(head):
            try:
                self.makedirs(head, mode)
            except ObjectExists:
                pass
        self.mkdir(path, mode)

    def open(self, path, mode='r'):
        """ open file """
        fileo = CephFSFile(self.monitors)
        fileo.open(path, mode)
        return fileo

    def unlink(self, path):
        """ unlink a file """
        try:
            self.conn.unlink(str(path))
        except cephfs.ObjectNotFound:
            raise NotFound

    def rmdir(self, path):
        """ delete directory """
        ret = self.conn.libcephfs.ceph_rmdir(self.conn.cluster, str(path))
        if ret < 0:
            if ret == -errno.ENOENT:
                raise NotFound
            raise cephfs.make_ex(ret, "error in rmdir: %s" % path)

    def rmtree(self, path):
        """ delete a directory and its contents """
        items = self.listdir(path)
        for item in items:
            full_path = os.path.join(path, item)
            if self.isdir(full_path):
                self.rmtree(full_path)
            else:
                self.unlink(full_path)
        self.rmdir(path)

    def shutdown(self):
        """ close Ceph session """
        if self.conn:
            self.conn.shutdown()
            self.conn = None

    def stat(self, path):
        """ stat a path """
        try:
            return self.conn.stat(str(path))
        except cephfs.ObjectNotFound:
            raise NotFound

class LocalFSStorage(object):
    """ storage abstraction for local filesystem """
    def __init__(self):
        pass

    def __enter__(self):
        """ enter hook for with statements """
        return self

    def __exit__(self, _type, _value, _traceback):
        """ exit hook for with statements """
        return False

    @classmethod
    def connect(cls):
        """ connect to storage, noop for local storage """
        pass

    @classmethod
    def exists(cls, path):
        """ check whether path exists """
        return os.path.exists(path)

    @classmethod
    def getsize(cls, path):
        """ get size of a file """
        try:
            return os.path.getsize(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def isdir(cls, path):
        """ check whether path exists and is a directory """
        return os.path.isdir(path)

    @classmethod
    def isfile(cls, path):
        """ check whether path exists and is a regular file """
        return os.path.isfile(path)

    @classmethod
    def listdir(cls, path):
        """ return directory contents, excluding . and .. """
        try:
            return os.listdir(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def mkdir(cls, path, mode=0755):
        """ create directory """
        try:
            os.mkdir(path, mode)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def makedirs(cls, path, mode=0755):
        """ create directory, with intermediary directories if missing """
        os.makedirs(path, mode)

    @classmethod
    def open(cls, path, mode='r'):
        """ open file """
        try:
            return open(path, mode)
        except IOError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def unlink(cls, path):
        """ unlink a file """
        try:
            os.unlink(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def rmdir(cls, path):
        """ delete directory """
        try:
            os.rmdir(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def rmtree(cls, path):
        """ delete a directory and its contents """
        try:
            shutil.rmtree(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

    @classmethod
    def shutdown(cls):
        """ shutdown, noop for local storage """
        pass

    @classmethod
    def stat(cls, path):
        """ stat a path """
        try:
            return os.stat(path)
        except OSError, e:
            if e.errno == errno.ENOENT:
                raise NotFound
            raise

