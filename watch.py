#!/usr/bin/env python

import argparse
import time
import threading
import Queue
import RPi.GPIO as GPIO
import signal
import sys
import Pyro4
from frame import Frame
from frame_grabber import FrameGrabber
from core_server import CoreServer
from core_server import CoreServerRunner

can_run = True

def signal_handler(signal, frame):
    global can_run
    print "Ctrl+C caught, Quitting"
    can_run = False

def on_run(args):
    global can_run
    pir_active_state = (GPIO.HIGH if args.pir_active == True else GPIO.LOW)
    pir_active_px = (GPIO.PUD_DOWN if args.pir_active == True else GPIO.PUD_UP)
    frame_stack = []

    print "Initializing GPIO"
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(args.pir_gpio_num, GPIO.IN, pull_up_down=pir_active_px)

    print "Initializing OpenCV"
    grabber_frame_queue = Queue.Queue(10)
    grabber = FrameGrabber(grabber_frame_queue, args.framerate, args.xres, args.yres)
    grabber.start()

    Pyro4.config.COMMTIMEOUT = 1.0
    server = CoreServer()
    server_runner = CoreServerRunner(server, args.bind_addr, args.bind_port, args.debug)
    server_runner.start()
    signal.signal(signal.SIGINT, signal_handler)

    print "Running"
    while can_run:
        # Detected via gpio activation
        if GPIO.input(args.pir_gpio_num) == pir_active_state:
            server.set_pir_state(True)
        else:
            server.set_pir_state(False)

        try:
            frame = grabber_frame_queue.get(block=True, timeout=0.01)
            server.set_frame(frame)
        except:
            continue

    print "Cleaning up"
    server_runner.stop()
    grabber.stop()
    GPIO.cleanup()

parser = argparse.ArgumentParser(description="Captures frames from the RPI camera and sends them out a TCP stream.\n")
parser.add_argument('-framerate', help='Framerate to capture at.', type=int, default=20, required=False)
parser.add_argument('-xres', help='X resolution to capture at.', type=int, default=640, required=False)
parser.add_argument('-yres', help='Y resolution to capture at.', type=int, default=480, required=False)
parser.add_argument('-pir_gpio_num', help='GPIO channel (BCM mode) for PIR sensor to wait for.', type=int, required=True)
parser.add_argument('-pir_active_high', help='Active high for when the capture should begin.', dest='pir_active', required=False, action='store_true')
parser.add_argument('-pir_active_low', help='Active low for when the capture should begin.', dest='pir_active', required=False, action='store_false')
parser.add_argument('-bind_addr', help='Address to bind too for RPC connections, can be 0.0.0.0 or localhost or any other address', required=True)
parser.add_argument('-bind_port', help='Port to bind too for RPC connections, usually 8080.', type=int, required=True)
parser.add_argument('-debug', help='Enable debugging.', required=False, action='store_true')
parser.set_defaults(pir_active=False)
parser.set_defaults(func=on_run)
args = parser.parse_args()
args.func(args)
