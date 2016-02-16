#vapetemp

##What it does
Python code for raspberian jessie to record temperatures and heater light
flashes on a dry herb vaporizer

See the obs directory for some typical outputs from an Arizer Solo 
:)

Here's a typical run with two inhalations. Periods where the heater light blinked are identified by 
the lower blue waveform - they're not exactly when it blinked but it shows when the Solo
was heating up. Immediately each inhalation starts, the heater kicks in and cycles furiously
The temperature is recorded inside a packed stem held upside down so convection is minimised
unless an inhalation takes place.
 
![A typical run][example]


##Hardware
This is for the optional photoresistor sensor
https://www.adafruit.com/products/161 stuck using
blu-tac to monitor the "heating" red blinking light on the device
adjust to suit the gpio pin you've wired your
photoresistor to. I'm using a photoresistor on gpio 4
with a capacitor using a loop to count charge
which is inverse to photocell illumination level.
mine gives below 5000 when the red light blinks on
and 20000+ when off using blu-tac. Idea and design from
https://learn.adafruit.com/basic-resistor-sensor-reading-on-raspberry-pi/basic-photocell-reading


##Recommended
In order NOT to have to run the code as root, there's a problem with jessie raspbian as of now
that you need to fix. To do that you need to run something like this:

```
 #!/bin/bash
 # ross feb 15 2016 fix so pi can access /dev/mem for gpio and /dev/spi...
 # see  http://raspberrypi.stackexchange.com/questions/40105/access-gpio-pins-without-root-no-access-to-dev-mem-try-running-as-root
 sudo chown `id -u`.`id -g` /dev/spidev0.*
 sudo chown root.gpio /dev/gpiomem
 sudo chmod g+rw /dev/gpiomem
 sudo chown `id -u`.`id -g` /dev/spidev0.*
```


#Development History
Started early january 2016, developing a vaporizer temperature probe system
started out with the adafruit sample for my max31855
added a stripchart and changed to spi
Copyright (c) 2014 Adafruit Industries
Author: Tony DiCola

feb 15 2016 Bondi,
added a blinken light line - just faked as 20 or 25c
assumed off when reading is > 5000 - typically 30k if off and the
blu-tac holds. 
Also finally got it working without the horror of being root to get
gpio access via /dev/mem or dev/spidev..

jan 8 no graphics from matplotlib?
update to jessie and beware that if you use apt-get install python-matplotlib,
mathplotlib may (still) be defaulting to the wrong
device - if matplotlib.get_backend() doesn't return u'TkAgg' then you
might need to update to the git matplotlib repo - worked for me

using wheezy, access to gpio was via /dev/mem so required root
I noted:
jan 6 might need to use pigpio for non sudo running
see http://abyz.co.uk/rpi/pigpio/download.html
MUST start with
sudo pigpiod



[example]: https://github.com/fubar2/vapetemp/blob/master/obs/stem_deep_720_secs_2_inhalations_140.png "Example run"
