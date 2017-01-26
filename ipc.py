#!/usr/bin/env python

import mmap
import posix_ipc

# https://github.com/mruffalo/posix_ipc/blob/master/demo/premise.py

class IPCMemory(object):
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.mapfile = None
        self.memory = None

    def bringup(self):
        self.memory = posix_ipc.SharedMemory(self.name, 0, size=self.size)
        self.mapfile = mmap.mmap(self.memory.fd, self.memory.size)

        # Once I've mmapped the file descriptor, I can close it without
        # interfering with the mmap.
        self.memory.close_fd()

    def bringdown(self):
        self.mapfile.close()
        self.memory.unlink()

    def write(self, index, data):
        self.mapfile.seek(index)
        self.mapfile.write(data)

    def read(self, index, size):
        self.mapfile.seek(index)
        return self.mapfile.read(size)

class IPCSemaphore(object):
    def __init__(self, name):
        self.name = name
        self.semaphore = None

    def bringup(self):
        self.semaphore = posix_ipc.Semaphore(self.name, 0)

    def bringdown(self):
        self.semaphore.unlink()

    def acquire(self, timeout):
        try:
            self.semaphore.acquire(timeout)
        except posix_ipc.BusyError:
            return False

        return True

    def release(self):
        self.semaphore.release()

