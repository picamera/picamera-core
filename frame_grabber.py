#!/usr/bin/env python

import time
import threading
from picamera.array import PiRGBArray
from picamera import PiCamera
from frame import Frame

class FrameGrabber(object):
    def __init__(self, frame_queue, video_rate, xres, yres):
        self.frame_queue = frame_queue
        self.video_rate = video_rate
        self.xres = xres
        self.yres = yres

    def start(self):
        self.can_run = True
        self.stopped = threading.Event()
        t_cap = threading.Thread(target=self.on_capture_frames)
        t_cap.daemon = True
        t_cap.start()

    def stop(self, timeout=1):
        self.can_run = False
        self.stopped.wait(timeout)

    def on_capture_frames(self):
        print "Grabber starting"
        camera = PiCamera()
        camera.resolution = (self.xres, self.yres)
        camera.framerate = self.video_rate
        raw_capture = PiRGBArray(camera, size=(self.xres, self.yres))
        last_timestamp = time.time()
        time.sleep(0.1)
        stream = camera.capture_continuous(raw_capture, format="bgr", use_video_port=True)

        for frame in stream:
            if self.can_run == False:
                break

            image = frame.array
            now_timestamp = time.time()
            diff = now_timestamp - last_timestamp
            last_timestamp = now_timestamp
            fps = 1 / diff

            try:
                self.frame_queue.put(Frame(image, now_timestamp, self.video_rate, fps, self.xres, self.yres), block=True, timeout=0.001)
            except Exception, e:
                pass

            # clear the stream in preparation for the next frame
            raw_capture.truncate(0)
            print "Approx fps: {0:.2f}".format(fps)

        print "Grabber stopping"
        stream.close()
        self.stopped.set()
