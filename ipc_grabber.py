#!/usr/bin/env python

import time
import threading
import cv2
import numpy as np
import posix_ipc
import struct
from ipc import IPCMemory, IPCSemaphore
from frame import Frame

current_milli_time = lambda: int(round(time.time() * 1000))

class IPCGrabber(object):
    def __init__(self, frame_queue):
        self.frame_queue = frame_queue
        self.memory = None

    def start(self):
        self.can_run = True
        self.stopped = threading.Event()
        t_cap = threading.Thread(target=self.on_read_frames)
        t_cap.daemon = True
        t_cap.start()

    def stop(self, timeout=1):
        self.can_run = False
        self.stopped.wait(timeout)

    def read_frame(self):
        mem_header_size = 6 * 4; # 6x uint32_t's

        if self.memory == None:
            print "Allocating memory: {0}".format(mem_header_size)
            self.memory = IPCMemory("/picamera_grabber_mem", mem_header_size)
            self.memory.bringup()

        mem_struct_data = self.memory.read(0, mem_header_size)
        memory_size, xres, yres, slot1_offset, slot2_offset, current_slot = struct.unpack('@IIIIII', mem_struct_data)

        if self.memory.size != memory_size:
            print "Reallocating memory: {0}".format(memory_size)
            self.memory = IPCMemory("/picamera_grabber_mem", memory_size)
            self.memory.bringup()

        if current_slot == 0:
            frame_offset = slot1_offset
        else:
            frame_offset = slot2_offset

        frame_header_size = (2 * 4) + 1; # 2x uint32_t's + bool
        frame_struct_data = self.memory.read(frame_offset, frame_header_size)
        real_size, compressed_size, compressed = struct.unpack('@II?', frame_struct_data)
        if compressed:
            size = compressed_size
        else:
            size = real_size

        print "Slot: {0} | size: {1} | compressed: {2}".format(current_slot, size, compressed),
        frame = self.memory.read(frame_offset + frame_header_size, size)
        return frame, xres, yres

    def on_read_frames(self):
        print "IPC Grabber starting"
        last_timestamp = time.time()
        time.sleep(0.1)

        sem_generate = IPCSemaphore("/picamera_grabber_generate")
        sem_generate.bringup()

        sem_notifier = IPCSemaphore("/picamera_grabber_notifier")
        sem_notifier.bringup()

        while True:
            if self.can_run == False:
                break

            data = None
            now_timestamp = None
            fps = 0
            if sem_notifier.acquire(1):
                now_timestamp = time.time()
                diff = now_timestamp - last_timestamp
                last_timestamp = now_timestamp
                fps = 1 / diff

                data = self.read_frame()
                print " | FPS: {0:.2f}".format(fps)
                sem_generate.release()

            if data != None:
                try:
                    self.frame_queue.put(Frame(data, "str_lz4", now_timestamp, fps, fps, xres, yres, True), block=True, timeout=0.001)
                except Exception, e:
                    pass

        print "Grabber stopping"
        self.stopped.set()
