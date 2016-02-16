#!/usr/bin/python
# mods ross lazarus jan 2015
# jan 8 no graphics from matplotlib?
# update to jessie and beware that if you use apt-get install python-matplotlib,
# mathplotlib may (still) be defaulting to the wrong
# device - if matplotlib.get_backend() doesn't return u'TkAgg' then you
# might need to update to the git matplotlib repo - worked for me
# 
# using wheezy, access to gpio was via /dev/mem so required root
# I noted:
# jan 6 might need to use pigpio for non sudo running
# see http://abyz.co.uk/rpi/pigpio/download.html
# MUST start with
# sudo pigpiod
#
# jan 5 developing a vaporizer temperature probe system
# started out with the adafruit sample for my max31855
# added a stripchart and changed to spi
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

from __future__ import division, print_function
import sys
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_MAX31855.MAX31855 as MAX31855
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import RPi.GPIO as GPIO
PDio = 4 ## adjust to suit wherever you've set up your
             ## photodetector. Using a photoresistor on gpio 4
             ## with a capacitor

def photoDet(PDio=4):
    # make a generator for photocell status
    while True:
        GPIO.setmode(GPIO.BCM) # broadcom
        reading = 0
        GPIO.setup(PDio, GPIO.OUT) # d/c capacitor
        GPIO.output(PDio, GPIO.LOW)
        time.sleep(0.1)
        GPIO.setup(PDio, GPIO.IN)
        # This takes about 1 millisecond per loop cycle
        while (GPIO.input(PDio) == GPIO.LOW):
                reading += 1
        yield reading
 


class stripTemp():
    # class to encapsulate the strip plotter matlab code
    
    def __init__(self,PLOTSEC=600,outfname='stripchartTemp'):
        self.PLOTSEC = 10 #PLOTSEC #720 # 12 minute sessions for x axis
        self.QUITS = ("q","Q")
        self.STARTIN = ('I','i')
        self.ENDIN = ('E','e')
        # Uncomment one of the blocks of code below to configure your Pi or BBB to use
        # software or hardware SPI.
        # Raspberry Pi software SPI configuration.
        #CLK = 25
        #CS  = 24
        #DO  = 18
        #sensor = MAX31855.MAX31855(CLK, CS, DO)
        # Raspberry Pi hardware SPI configuration.
        self.SPI_PORT   = 0
        self.SPI_DEVICE = 0
        self.sensor = MAX31855.MAX31855(spi=SPI.SpiDev(self.SPI_PORT, self.SPI_DEVICE))
        # BeagleBone Black software SPI configuration.
        #CLK = 'P9_12'
        #CS  = 'P9_15'
        #DO  = 'P9_23'
        #sensor = MAX31855.MAX31855(CLK, CS, DO)
        # BeagleBone Black hardware SPI configuration.
        #SPI_PORT   = 1
        #SPI_DEVICE = 0
        #sensor = MAX31855.MAX31855(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
            
        self.ts = self.getTempStream()
        self.outf = open('%s.xls' % outfname,'w')
        self.savepng = '%s.png' % outfname
        self.outf.write('Second\tTemperature\n')
        # set up a generator for PLOTSEC seconds of sampling
        style.use('ggplot')
        # prepopulate arrays to make updates quicker
        self.t = range(self.PLOTSEC+2)
        self.y = [None for i in self.t]
        self.fig, self.ax = plt.subplots()
        #self.ax.set_xlim(auto=True)
        #self.ax.set_ylim(auto=True)

        # fig.canvas.mpl_connect('key_press_event', press)
        self.line, = self.ax.plot(0,0,lw=1)
        self.text_template = 'Last temperature = %3.2f'
        self.title_template = 'Temperature strip chart at %d seconds'
        self.t_temp = self.ax.text(0.15,0.15,self.text_template%(0),
                                   transform=self.ax.transAxes, family='monospace',fontsize=10)
        #self.t_title = self.ax.text(0.5,1.0,self.title_template%(0),
        #                            transform=self.ax.transAxes, family='monospace',fontsize=20)
        self.started = time.time()
        

    # Define a function to convert celsius to fahrenheit.
    def c_to_f(self,c):
        return c * 9.0 / 5.0 + 32.0

    def press(self,event):
        print('press', event.key)
        sys.stdout.flush()
        if event.key in self.QUITS:
            go = False
        elif event.key in self.STARTIN:
            inhale = True
        elif event.key in self.ENDIN:
            inhale = False

    def getTempStream(self,maxx = 10000):
        # generator for a stream of mean temps averaged every second or so
        # for (eg) 720 maxsec seconds
        # samples per sec will vary, so allow a lot
        # in practice, taking about 4.5k samples/sec with hardware SPI a/d conversion
        # on a pi 2 b january 2015
        while True:
            x = [0 for n in range(maxx)]
            loop = 0
            started = time.time()
            while ((time.time() - started) < 1.0):
                temp = self.sensor.readTempC()
                internal = self.sensor.readInternalC()
                diff = temp - internal
                x[loop] = temp
                loop += 1
            lasti = loop-1
            # print('# took',lasti+1,'samples')
            xmean = sum(x[0:(lasti)])/float(lasti)
            yield(xmean)
            

    def animate(self,i):
        # add new point to y-value arrays
        try:
            mT = self.ts.next()
        except StopIteration:
            print('# stop!')
            self.outf.close()
            return self.line, self.t_temp, self.t_title, self.fig.suptitle
        self.y[i+1] = mT
        self.outf.write('%d\t%g\n' % (i,mT))
        self.outf.flush()
        print(mT,i+1)
        
        if (i > 0):
            useme = self.y[0:(i+1)]
            avg = sum(useme)/float(i)
            
            self.line.set_xdata( self.t[0:(i+1)] )
            self.line.set_ydata( useme )
            plt.axis([0,i+1,min(useme)-1,max(useme)+1])
        else:           
            avg = mT
            variation = 1
            #self.ax.set_xlim(0,1)
            self.line.set_xdata([0,] )
            self.line.set_ydata( [mT,] )
            plt.axis([0,1,mT-1,mT+1])
        #self.ax.figure.canvas.draw() # this is necessary, to redraw the axes
        self.t_temp.set_text( self.text_template % (mT) )
        self.fig.suptitle(self.title_template % (i) )
        #plt.draw()
        return self.line, self.t_temp, self.fig.suptitle

    def initFunc(self): #Init only required for blitting to give a clean slate.
        y1 = self.ts.next()
        print(y1,'0')
        self.y[0] = y1
        self.line.set_ydata([y1,])
        self.t_temp.set_text("Starting up")
        self.fig.suptitle(self.title_template % (0) )
        self.ax.set_ylim(y1-1,y1+1)
        return  self.t_temp,self.line,self.fig.suptitle,self.ax

    def startup(self):
        self.ani = animation.FuncAnimation(self.fig, self.animate,
            init_func=self.initFunc, frames=self.PLOTSEC+1,
            repeat=False, blit=False)       # blit has to be False, to avoid ugly artefacts on the text

blink = photoDet()
for b in blink:
    print(b)
    


##nowSec = 0
##strip = stripTemp()
##strip.startup()
##plt.show()

      
##while go:
##    mT = ts.next()
##    y[nowSec] = mT
##    print(nowSec,mT)
##    nowSec += 1
##    plotlab = 'Temperature strip chart at %d seconds' % nowSec
##    ax.plot(y[0:nowSec],range(0,nowSec))
##    plt.show(block=False)
##    time.sleep(0.01)

