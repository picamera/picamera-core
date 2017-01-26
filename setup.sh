#!/bin/bash

echo "Installing OpenCV"
apt-get install python-opencv || exit 1

echo "Installing Pip"
apt-get install python-pip || exit 1

echo "Installing Python-ipc"
apt-get install python-ipc || exit 1

echo "Installing Pyron4"
pip install Pyro4 || exit 1

echo "Installing RPi.GPIO"
pip install RPi.GPIO || exit 1

