#!/usr/bin/env python

import time
import threading
import Pyro4
from frame_grabber import Frame

@Pyro4.behavior(instance_mode="single")
class CoreClient(object):
    def __init__(self):
        self.latest_frame = None
        self.pir_state = False

    @Pyro4.expose
    def get_frame(self):
        return self.latest_frame

    def set_frame(self, frame):
        self.latest_frame = frame

    @Pyro4.expose
    def get_pir_state(self):
        return self.pir_state

    def set_pir_state(self, state):
        self.pir_state = state


class CoreClientRunner(object):
    def __init__(self, client, bind_addr, bind_port, debug):
        self.client = client
        self.bind_addr = bind_addr
        self.bind_port = bind_port
        self.debug = debug

    def start(self):
        self.can_run = True
        self.stopped = threading.Event()
        t = threading.Thread(target=self.on_run)
        t.daemon = True
        t.start()

    def stop(self, timeout=5):
        self.can_run = False
        self.stopped.wait(timeout)

    def running(self):
        return self.can_run

    def on_run(self):
        print "CoreClient runner starting"
        daemon = Pyro4.Daemon(host=self.bind_addr, port=self.bind_port)
        uri = daemon.register(self.client)
        print "CoreClient registered: {0}".format(uri)

        daemon.requestLoop(loopCondition=self.running)

        print "CoreClient runner stopping"
        daemon.close()
        self.stopped.set()

