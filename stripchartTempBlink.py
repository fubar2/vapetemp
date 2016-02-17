#!/usr/bin/python
# mods ross lazarus feb 15 2016 Bondi,
# added a blinken light line - just faked as 20 or 25c level plots
# assumed off when reading is > 2500 - typically 30k if off and the
# blu-tac holds. No point counting beyond 2501 - saves a few cycles
#
# Also finally got it working without the horror of being root to get
# gpio access via /dev/mem or dev/spidev..
#
# run something like this:
#---------
#!/bin/bash
# ross feb 15 2016 fix so pi can access /dev/mem for gpio and /dev/spi...
# see  http://raspberrypi.stackexchange.com/questions/40105/access-gpio-pins-without-root-no-access-to-dev-mem-try-running-as-root
#sudo chown `id -u`.`id -g` /dev/spidev0.*
#sudo chown root.gpio /dev/gpiomem
#sudo chmod g+rw /dev/gpiomem
#sudo chown `id -u`.`id -g` /dev/spidev0.*
#---------
#
#
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
PDio = 4
## this is for the optional photoresistor sensor
## https://www.adafruit.com/products/161 
## stuck using
## blu-tac to monitor the "heating" red blinking light on the device
## adjust to suit the gpio pin you've wired your
## photoresistor to. I'm using a photoresistor on gpio 4
## with a capacitor using a loop to count charge
## which is inverse to photocell illumination level.
## mine gives below 5000 when the red light blinks on
## and 20000+ when off using blu-tac. Idea and design from
## https://learn.adafruit.com/basic-resistor-sensor-reading-on-raspberry-pi/basic-photocell-reading

class stripTemp():
    # class to encapsulate the strip plotter matplot code
    
    def __init__(self,PLOTSEC=600,outfname='stripchartTemp',PDio=4):
        self.PLOTSEC = PLOTSEC #PLOTSEC #720 # 12 minute sessions for x axis
        self.QUITS = ("q","Q")
        self.STARTIN = ('I','i')
        self.ENDIN = ('E','e')
        self.PDio = PDio
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
        self.blinkYlevel = 20 # where blink off will appear
        self.blinkYactive = 25
        self.blinkThresh = 2500
        # this works for me and my blu-tac. Your mileage may vary. Try raising it and seeing where
        # the hi and low readings tend to cluster - then choose a sensible threshold to reliably distinguish
        # them
        self.maxPhotoDetReads = self.blinkThresh + 1 # about 0.06 sec sampling truncating at 5k cycles
        # self.maxPhotoDetReads = 100000 # about 0.23 sec sampling at 30k cycles      
        self.ts = self.getTempStream()
        self.bs = self.photoDet()
        self.outf = open('%s.xls' % outfname,'w')
        self.savepng = '%s.png' % outfname
        self.outf.write('Second\tTemperature\n')
        # set up a generator for PLOTSEC seconds of sampling
        style.use('ggplot')
        # prepopulate arrays to make updates quicker
        self.t = range(self.PLOTSEC+2)
        self.y = [None for i in self.t]
        self.blinky = [None for i in self.t]
        self.blinkx = [None for i in self.t]
        self.fig, self.ax = plt.subplots()
        #self.ax.set_xlim(auto=True)
        #self.ax.set_ylim(auto=True)

        # fig.canvas.mpl_connect('key_press_event', press)
        self.line, = self.ax.plot(0,0,lw=1)
        self.blinkLine, = self.ax.plot(0,0,lw=1)
        self.text_template = 'Last temperature = %3.2f'
        self.title_template = 'Temperature strip chart at %d seconds'
        self.t_temp = self.ax.text(0.15,0.15,self.text_template%(0),
                                   transform=self.ax.transAxes, family='monospace',fontsize=10)
        #self.t_title = self.ax.text(0.5,1.0,self.title_template%(0),
        #                            transform=self.ax.transAxes, family='monospace',fontsize=20)
        self.started = time.time()

    def photoDet(self):
        # make a generator for photocell status
        while True:
            GPIO.setmode(GPIO.BCM) # broadcom
            reading = 0
            GPIO.setup(self.PDio, GPIO.OUT) # d/c capacitor
            GPIO.output(self.PDio, GPIO.LOW)
            time.sleep(0.05)
            GPIO.setup(self.PDio, GPIO.IN)
            # This takes about 1 millisecond per loop cycle
            while (GPIO.input(self.PDio) == GPIO.LOW and reading < self.maxPhotoDetReads):
                    reading += 1
            yield reading
     
        

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

    def getTempStream(self,sample=0.1,maxx = 10000):
        # generator for a stream of mean temps averaged every second or so
        # for (eg) 720 maxsec seconds
        # samples per sec will vary, so allow a lot
        # in practice, taking about 4.5k samples/sec with hardware SPI a/d conversion
        # on a pi 2 b january 2015
        while True:
            x = [0 for n in range(maxx)]
            loop = 0
            started = time.time()
            while ((time.time() - started) < sample):
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
            mT = self.ts.next() # sample in 0.1 second increments
        except StopIteration:
            print('# stop!')
            self.outf.close()
            return self.line, self.t_temp, self.t_title, self.fig.suptitle
        mark = time.time()
        bT = self.bs.next() # takes about 0.06 sec
        durat = time.time() - mark
        print('blink status duration:%f' % durat)
        if bT < self.blinkThresh:
            ubT = self.blinkYactive
        else:
            ubT = self.blinkYlevel
        self.blinky[i+1] = ubT
        self.y[i+1] = mT
        self.outf.write('%d\t%g\t%d\n' % (i,mT,bT))
        self.outf.flush()
        print(i+1,':',mT,bT,ubT)
        if (i > 0):
            useme = self.y[0:(i+1)]
            usemeBlink = self.blinky[0:(i+1)]
            avg = sum(useme)/float(i)
            self.blinkLine.set_xdata( self.t[0:(i+1)] )
            self.blinkLine.set_ydata( usemeBlink )
            self.line.set_xdata( self.t[0:(i+1)] )
            self.line.set_ydata( useme )
            plt.axis([0,i+1,min(min(useme)-1,self.blinkYlevel),max(useme)+1])
        else:           
            avg = mT
            variation = 1
            self.line.set_xdata([0,] )
            self.line.set_ydata( [mT,] )
            self.blinkLine.set_xdata([self.blinkYlevel for x in range(i+1)] )
            self.blinkLine.set_ydata( bT )
            plt.axis([0,1,mT-1,mT+1])

        self.t_temp.set_text( self.text_template % (mT) )
        self.fig.suptitle(self.title_template % (i) )

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
        self.initFunc()
        self.ani = animation.FuncAnimation(self.fig, self.animate,
            init_func=self.initFunc, frames=self.PLOTSEC+1,interval=10,
            repeat=False, blit=False)
        # blit has to be False, to avoid ugly artefacts on the text


    


nowSec = 0
strip = stripTemp(PLOTSEC=720,outfname='stripchartTemp',PDio=4)
strip.startup()
plt.show()

