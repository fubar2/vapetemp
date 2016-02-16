#!/usr/bin/python
# mods ross lazarus jan 2015
# uses pigpio for non sudo running
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

import sys
import time
import pygame

import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855


# Define a function to convert celsius to fahrenheit.
def c_to_f(c):
        return c * 9.0 / 5.0 + 32.0


# Uncomment one of the blocks of code below to configure your Pi or BBB to use
# software or hardware SPI.

# Raspberry Pi software SPI configuration.
CLK = 25
CS  = 24
DO  = 18
sensor = MAX31855.MAX31855(CLK, CS, DO)

# Raspberry Pi hardware SPI configuration.
#SPI_PORT   = 0
#SPI_DEVICE = 0
#sensor = MAX31855.MAX31855(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

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
print 'Press Q to quit.'
pygame.init()
BLACK = (0,0,0)
WHITE = (255,255,255)
WIDTH = 100
HEIGHT = 100
windo = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
windo.fill(WHITE)
pygame.display.flip()
quits = (pygame.K_q,pygame.K_e)
reset = (pygame.K_r)
startin = (pygame.K_s)
endin = (pygame.K_e)
go=True
started = time.time()
while go:
    temp = sensor.readTempC()
    internal = sensor.readInternalC()
    diff = temp - internal
    elapsed = time.time() - started
    events = pygame.event.get()
    print 'at %f secs, probe: %f C, diff: %f C' % (elapsed,temp,diff)
    ## print 'Internal Temperature: {0:0.3F}*C / {1:0.3F}*F'.format(internal, c_to_f(events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
                if event.key in quits:
                        print "### got a q"
                        go = False
                elif event.key in reset:
                        started = time.time()
                else:
                        print "## %s" % event.key
    time.sleep(0.01)
pygame.quit()

