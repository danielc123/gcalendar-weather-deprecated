The Original code written by Jim Kemp http://www.ph-elec.com/

Modified to get used with the Lichee Zero Pi

========================================
Google Calendar and Weather Station
========================================

Downloaded from:

http://www.instructables.com/id/Raspberry-Pi-Internet-Weather-Station/step4/Source-Code/


This README.rst contains instructions extracted from the above link: 


Installation
============
Install Pywapi:
The pywapi needs to be downloaded and installed. Again, this is not too hard with the following steps:

    Download the latest from here:
    https://launchpad.net/python-weather-api/trunk/0.3.8/+download/pywapi-0.3.8.tar.gz 
    Extract the archive into a new directory.
    Using File Manger, copy the directory to the Pi home directory.
    Using ssh, do the following on the Pi:
        $ cd pywapi-0.3.8
        
        $ sudo python setup.py build
        
        $ sudo python setup.py install
    Done.


Install Pygame:
Just install it from your repository using:
        $ sudo apt-get install python-pygame


Install and run:
To get my source code running just unzip the attachment and copy the whole directory onto the Pi using File Manage. Once copied, start the code use the following ssh commands:
        $ cd Weather  #if the code was downloaded from Instructables
        
        or
        
        $ cd weather-display-master   #if the code was downloaded from this repository
        
        $ sudo python weather.py


Autorun after boot:
Once everything gets working using ssh it's time to get weather to start automatically on a reboot. This is also really easy to do.

    Using ssh, run:
        $ sudo vi /etc/rc.local"

    Just before the last line, which says "exit 0", add the following to lines.
        $ cd /home/pi/Weather  #if the code was downloded from instructables 
        
        otherwise use $ cd /home/pi/weather-display-master #if the code was downloaded from this repository
        
        $ sudo python weather.py &> err.log

This will automatically start the weather application on the Pi after a reboot. If later you want to turn this off, just use ssh to edit the file and add the comment character "#" in front of both lines and reboot.


A couple of other things to note about my code. Buried down in there you'll notice some code to talk to an X10 device. This was my attempt to control my outside pole lights that are on address A3. I simply wanted the lamps on at dusk and off at dawn. Seems easy enough and I thought I had it working. Using a USB-to-RS232 dongle on the Pi I had connected a CM11A X10 module. The CM11A is an old X10 macro module. The CM11A also has a RS232 port that allows control over the X10 bus. Seems there are still some bugs because the lamp pole lights aren't getting the message!

Also of note, on the larger display there is a nice open gap along the right hand side of the display. My plan is add some status lamps in that area. I'm playing with some IEEE802.15.4 radios and their outputs will one day show up in that open spot.



Set your own settings
=====================
Edit weather.py and change the following as needed:

* Zip code in UpdateWeather function
* Display size depending on your display (see comments)



Keyboard Controls
=================
  * q or keypad Enter - quit program
  * c - switch to calendar display
  * w - switch to weather display
  * h - switch to site info display



