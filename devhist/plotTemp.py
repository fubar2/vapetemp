#!/usr/bin/python
# mods ross lazarus jan 2015
# might need to use pigpio for non sudo running
# see http://abyz.co.uk/rpi/pigpio/download.html
# MUST start with
# sudo pigpiod
# developing a vaporizer temperature probe system
#
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Can enable debug output by uncommenting:
#import logging
#logging.basicConfig(level=logging.DEBUG)
from __future__ import print_function

import sys
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855

import sys
import numpy as np
import matplotlib.pyplot as plt

PLOTSEC = 10#720 # 12 minute sessions for x axis
QUITS = ("q","Q")
STARTIN = ('I','i')
ENDIN = ('E','e')

# Define a function to convert celsius to fahrenheit.
def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0

def press(event):
    print('press', event.key)
    sys.stdout.flush()
    if event.key in QUITS:
        go = False
    elif event.key in STARTIN:
        inhale = True
    elif event.key in ENDIN:
        inhale = False

def getTempStream(maxx = 5000,maxsec=PLOTSEC):
    # generator for a stream of mean temps every second or so
    for k in range(PLOTSEC):
        x = [0 for y in range(maxx)]
        i = 0
        started = time.time()
        while ((time.time() - started) < 1.0):
            temp = sensor.readTempC()
            internal = sensor.readInternalC()
            diff = temp - internal
            x[i] = diff
            i += 1
        lasti = i-1
        xmean = sum(x[0:(lasti)])/float(lasti)
        yield(xmean)

# Uncomment one of the blocks of code below to configure your Pi or BBB to use
# software or hardware SPI.

# Raspberry Pi software SPI configuration.
#CLK = 25
#CS  = 24
#DO  = 18
#sensor = MAX31855.MAX31855(CLK, CS, DO)

# Raspberry Pi hardware SPI configuration.
SPI_PORT   = 0
SPI_DEVICE = 0
sensor = MAX31855.MAX31855(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# BeagleBone Black software SPI configuration.
#CLK = 'P9_12'
#CS  = 'P9_15'
#DO  = 'P9_23'
#sensor = MAX31855.MAX31855(CLK, CS, DO)

# BeagleBone Black hardware SPI configuration.
#SPI_PORT   = 1
#SPI_DEVICE = 0
#sensor = MAX31855.MAX31855(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

# Loop printing measurements every second.

r = range(PLOTSEC)
x = [0 for i in r]
y = [0 for i in r]
t = [1 for i in r]
nowSec = 0

started = time.time()
go = True
ts = getTempStream()
nowSec = 0
fig, ax = plt.subplots()
fig.canvas.mpl_connect('key_press_event', press)
while go:
    mT = ts.next()
    x[nowSec] = mT
    print(nowSec,mT)
    nowSec += 1
    plotlab = 'Temperature strip chart at %d seconds' % nowSec
    ax.plot(x[0:nowSec],range(0,nowSec))
    plt.show(block=False)
    time.sleep(0.01)

