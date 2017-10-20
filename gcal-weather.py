#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
#Copyright (c) 2014 Jim Kemp <kemp.jim@gmail.com>

#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:

#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.
### END LICENSE

""" Fetches weather reports Weather.com for display on small screens."""

__version__ = "0.0.8"

###############################################################################
#   Lichee Zero Pi Google Calendar & Weather Display
#    Created by: Jim Kemp    		11/15/2014
#	 Modified by: Daniel Correas	10/10/2017
#
###############################################################################
import os
import pygame
import time
import datetime
import random
from pygame.locals import *
import calendar
import pywapi
import string
from icon_defs import *

## dependencies added
import locale
from strings_defs import *      # Strings file to store other languages translated strings


# Setup GPIO pin BCM GPIO04
# import RPi.GPIO as GPIO
# GPIO.setmode( GPIO.BCM )
# GPIO.setup( 4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN )    # Next 
# GPIO.setup( 17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN )    # Shutdown

mouseX, mouseY = 0, 0
mode = 'w'        # Default to weather mode.

disp_units = "metric"
#disp_units = "imperial"
zip_code = 'SPXX0819'
lang = 'es'         #'en': English (default), 'es': Spanish

# Show degree F symbol using magic unicode char in a smaller font size.
# The variable uniTmp holds a unicode character that is either DegreeC or DegreeF.
# Yep, one unicode character is has both the letter and the degree symbol.
if disp_units == 'metric':
    if lang=='es':
        locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')    # Added locale to set time in local format
    uniTmp = unichr(0x2103)        # Unicode for DegreeC
    windSpeed = 'km/h'
    windScale = 1.0        # To convert kmh to m/s.
    baroUnits = 'hPa'
    visiUnits = 'km'
else:
    uniTmp = unichr(0x2109)        # Unicode for DegreeF
    windSpeed = 'mph'
    windScale = 1.0
    baroUnits = '"Hg'
    visiUnits = 'Mi'


###############################################################################
def getIcon( w, i ):
    try:
        return int(w['forecasts'][i]['day']['icon'])
    except:
        return 29

# Small LCD Display.
class SmDisplay:
    screen = None;
    
    ####################################################################
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "X Display = {0}".format(disp_no)
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer Size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.mouse.set_visible(0)
        pygame.display.update()
        #for fontname in pygame.font.get_fonts():
        #        print fontname
        self.temp = ''
        self.feels_like = 0
        self.wind_speed = '0'
        self.baro = '29.95'
        self.wind_dir = 'S'
        self.humid = '50.0'
        self.wLastUpdate = ''
        self.day = [ '', '', '', '' ]
        self.icon = [ 0, 0, 0, 0 ]
        self.rain = [ '', '', '', '' ]
        self.temps = [ ['',''], ['',''], ['',''], ['',''] ]
        self.sunrise = '7:00 AM'
        self.sunset = '8:00 PM'

        """
        # Larger Display
        self.xmax = 800 - 35
        self.ymax = 600 - 5
        self.scaleIcon = True        # Weather icons need scaling.
        self.iconScale = 1.5        # Icon scale amount.
        self.subwinTh = 0.05        # Sub window text height
        self.tmdateTh = 0.100        # Time & Date Text Height
        self.tmdateSmTh = 0.06
        self.tmdateYPos = 10        # Time & Date Y Position
        self.tmdateYPosSm = 18        # Time & Date Y Position Small
        self.errCount = 0        # Count number of failed updates.
		"""
        
        # Small Display
        self.xmax = 800
        self.ymax = 480
        self.scaleIcon = False      # No icon scaling needed.
        self.iconScale = 1.0
        self.subwinTh = 0.065       # Sub window text height
        self.tmdateTh = 0.30        # Time HH:MM Text Height
        self.tmdateSmTh = 0.15      # Time ss seconds Text Height
        self.tmdateDtTh = 0.075     # Date Text Height
        self.tmdateYPos = -3        # Time Y Position
        self.tmdateYPosSm = 12      # Date Y Position 
        




    ####################################################################
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    ####################################################################
    def UpdateWeather( self ):
        # Use Weather.com for source data.
        cc = 'current_conditions'
        f = 'forecasts'
        w = { cc:{ f:1 }}  # Init to something.

        # This is where the magic happens. 
        try:
            self.w = pywapi.get_weather_from_weather_com( zip_code, units=disp_units )
            w = self.w
        except:
            print "Error getting update from weather.com"
            self.errCount += 1
            return

        try:
            if ( w[cc]['last_updated'] != self.wLastUpdate ):
                self.wLastUpdate = w[cc]['last_updated']
                print "New Weather Update: " + self.wLastUpdate
                self.temp = string.lower( w[cc]['temperature'] )
                self.feels_like = string.lower( w[cc]['feels_like'] )
                self.wind_speed = string.lower( w[cc]['wind']['speed'] )
                self.baro = string.lower( w[cc]['barometer']['reading'] )
                self.wind_dir = string.upper( w[cc]['wind']['text'] )
                self.humid = string.upper( w[cc]['humidity'] )
                self.vis = string.upper( w[cc]['visibility'] )
                self.gust = string.upper( w[cc]['wind']['gust'] )
                self.wind_direction = string.upper( w[cc]['wind']['direction'] )
                self.day[0] = w[f][0]['day_of_week']
                self.day[1] = w[f][1]['day_of_week']
                self.day[2] = w[f][2]['day_of_week']
                self.day[3] = w[f][3]['day_of_week']
                self.sunrise = w[f][0]['sunrise']
                self.sunset = w[f][0]['sunset']
                self.icon[0] = getIcon( w, 0 )
                self.icon[1] = getIcon( w, 1 )
                self.icon[2] = getIcon( w, 2 )
                self.icon[3] = getIcon( w, 3 )
                print 'Icon Index: ', self.icon[0], self.icon[1], self.icon[2], self.icon[3]
                #print 'File: ', sd+icons[self.icon[0]]
                self.rain[0] = w[f][0]['day']['chance_precip']
                self.rain[1] = w[f][1]['day']['chance_precip']
                self.rain[2] = w[f][2]['day']['chance_precip']
                self.rain[3] = w[f][3]['day']['chance_precip']
                if ( w[f][0]['high'] == 'N/A' ):
                    self.temps[0][0] = '--'
                else:    
                    self.temps[0][0] = w[f][0]['high']
                self.temps[0][1] = w[f][0]['low']
                self.temps[1][0] = w[f][1]['high']
                self.temps[1][1] = w[f][1]['low']
                self.temps[2][0] = w[f][2]['high']
                self.temps[2][1] = w[f][2]['low']
                self.temps[3][0] = w[f][3]['high']
                self.temps[3][1] = w[f][3]['low']
            self.errCount = 0

        except KeyError:
            print "KeyError -> Weather Error"
            if self.errCount >= 15:
                self.temp = '??'
            self.wLastUpdate = ''
            return False
        except ValueError:
            print "ValueError -> Weather Error"
        
        return True



    ####################################################################
    def disp_weather(self):
    # New design of the screen: It is divided in 2 fractions by a vertical imaginary line at wx*100%
    # The left side shows Current Time and Date at the Top and below of that a list of 3 Google events 
    # The reight side the Current Temp at the top 25% height and below 4 windows with the Weather Forecast
        # Fill the screen with black
        self.screen.fill( (0,0,0) )
        xmin = 10
        xmax = self.xmax
        ymax = self.ymax
        lines = 2
        lc = (255,255,255) 
        fn = "freesans"
        wx = 0.72   # wx determine the screen vertical division from left

        # Draw Weather Forecast Sub divisions: height 25% | 75%/4 | 75%/4 | 75%/4 | 75%/4
        pygame.draw.line( self.screen, lc, (xmax*wx,ymax*0.25),(xmax,ymax*0.25), lines )        # Temp Window 25% height
        pygame.draw.line( self.screen, lc, (xmax*wx,ymax*0.4375),(xmax,ymax*0.4375), lines )    # 1st W Forecast
        pygame.draw.line( self.screen, lc, (xmax*wx,ymax*0.6250),(xmax,ymax*0.6250), lines )    # 2nd W Forecast
        pygame.draw.line( self.screen, lc, (xmax*wx,ymax*0.8125),(xmax,ymax*0.8125), lines )    # 3rd W Forecast

        # Time & Date on the left side
        th = self.tmdateTh
        sh = self.tmdateSmTh
        dh = self.tmdateDtTh
        font = pygame.font.SysFont( fn, int(ymax*th), bold=0 )      # Regular Font
        sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=0 )     # Small Font for Seconds
        dfont = pygame.font.SysFont( fn, int(ymax*dh), bold=0 )     # Date Font 

        tm1 = time.strftime( "%H:%M", time.localtime() )                    # 1st part: Time HH:MM
        tm2 = time.strftime( "%S", time.localtime() )                       # 2nd part: ss seconds
        tm3 = time.strftime( "%A, %d %B", time.localtime() ).decode('utf-8').title()   # Below Full Date

        rtm1 = font.render( tm1, True, lc )
        (tx1,ty1) = rtm1.get_size()
        rtm2 = sfont.render( tm2, True, lc )
        (tx2,ty2) = rtm2.get_size()
        rtm3 = dfont.render( tm3, True, lc )
        (tx3,ty3) = rtm3.get_size()

        tp = xmax*wx / 2 - (tx1 + tx2 ) / 2     # Centered on the left side of the screen
        self.screen.blit( rtm1, (tp,self.tmdateYPos) )
        self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )
        tp = xmax*wx / 2 - tx3 / 2              # Date below time, centered on the left side
        self.screen.blit( rtm3, (tp,ty1-15) )


        # Outside Temp and Weather Forecast on the right side 25% height
        font = pygame.font.SysFont( fn, int(ymax*(0.2125)), bold=0 )
        txt = font.render( self.temp, True, lc )
        (tx,ty) = txt.get_size()
        # Show degree F or C symbol using magic unicode char in a smaller font size.
        dfont = pygame.font.SysFont( fn, int(ymax*(0.2125)*0.5), bold=0 )
        dtxt = dfont.render( uniTmp, True, lc )
        (tx2,ty2) = dtxt.get_size()
        x = xmax*( wx +1 ) / 2 - (tx*1.02 + tx2) / 2    # Centered on the right side
        self.screen.blit( txt, (x,0) )
        x = x + (tx*1.02)
        self.screen.blit( dtxt, (x,12) )                # Temp degree symbol aside the temperature

        wy =     0.250 + 0.1875/2   # Sub Windows Yaxis Center
        gp =     0.1875             # Vertical Spacing between Windows
        th =     self.subwinTh      # Text Height

        font = pygame.font.SysFont( fn, int(ymax*th*1), bold=0 )          # Weekday 
        mfont = pygame.font.SysFont( fn, int(ymax*th*1.3), bold=0 )     # Max and Min Temp
        dfont = pygame.font.SysFont( fn, int(ymax*th*1.3*0.5), bold=0 ) # Degree symbol

        dtxt = dfont.render( uniTmp, True, lc)                          # Degree symbol rendered
        (dtx, dty) = dtxt.get_size()                                    # Degree dimensions

        # Sub Window 1
        txt = font.render( gettext('Today', lang), True, lc )           # Label today rendered
        (tx1,ty1) = txt.get_size()                                      # Label dimensions
        self.screen.blit( txt, (xmax*wx,ymax*(wy+gp*0)-ty1/2) )         # 
        txt = mfont.render( self.temps[0][0], True, lc )                 # Max temp rendered
        (tx2,ty2) = txt.get_size()                                      # Max temp dimensions
        self.screen.blit( txt, (xmax-tx2-dtx-4,ymax*(wy+gp*0)-ty2+4) )  # Max temp located on right edge of screen
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*0)-ty2+9) )     # Degree symbol next to max temp
        txt = mfont.render( self.temps[0][1], True, lc )                # Min temp rendered
        (tx3,ty3) = txt.get_size()                                      # Min temp dimensions
        self.screen.blit( txt, (xmax-tx3-dtx-4,ymax*(wy+gp*0)-3) )      # Min temp located on right edge of screen
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*0)+2) )         # Degree symbol next to min temp

        icon = pygame.image.load(sd + icons[self.icon[0]]).convert_alpha()
        (ix,iy) = icon.get_size()
        if self.scaleIcon:
            icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
            (ix,iy) = icon2.get_size()
            icon = icon2
        if ( iy < 90 ):
            yo = (90 - iy) / 2 
        else: 
            yo = 0
        self.screen.blit( icon, ((xmax*(wx+1)+tx1-max(tx2,tx3)-dtx)/2-ix/2-2,ymax*(wy+gp*0)-iy/2) )     # Icon located in the Window middle

        # Sub Window 2
        txt = font.render( gettext(self.day[1], lang), True, lc )       # Label Weekday today+1
        (tx1,ty1) = txt.get_size()                                      # Weekday dimensions
        self.screen.blit( txt, (xmax*wx,ymax*(wy+gp*1)-ty1/2) )         # 
        txt = mfont.render( self.temps[1][0], True, lc )                # Max temp rendered
        (tx2,ty2) = txt.get_size()                                      # Max temp dimensiones
        self.screen.blit( txt, (xmax-tx2-dtx-4,ymax*(wy+gp*1)-ty2+4) )  # Max temp located on right edge
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*1)-ty2+9) )     # Degree symbol next to it
        txt = mfont.render( self.temps[1][1], True, lc )                # Min temp rendered
        (tx3,ty3) = txt.get_size()                                      # Min temp dimensions
        self.screen.blit( txt, (xmax-tx3-dtx-4,ymax*(wy+gp*1)-3) )      # Min temp located on right edge
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*1)+2) )         # Degree symbol next to it
        
        icon = pygame.image.load(sd + icons[self.icon[1]]).convert_alpha()
        (ix,iy) = icon.get_size()
        if self.scaleIcon:
            icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
            (ix,iy) = icon2.get_size()
            icon = icon2
        if ( iy < 90 ):
            yo = (90 - iy) / 2 
        else: 
            yo = 0
        self.screen.blit( icon, ((xmax*(wx+1)+tx1-max(tx2,tx3)-dtx)/2-ix/2-2,ymax*(wy+gp*1)-iy/2)  )    # Icon located in the Window middle

        # Sub Window 3
        txt = font.render( gettext(self.day[2], lang), True, lc )       # Label Weekday today+2
        (tx1,ty1) = txt.get_size()                                      # Weekday dimensions
        self.screen.blit( txt, (xmax*wx,ymax*(wy+gp*2)-ty1/2) )         # 
        txt = mfont.render( self.temps[2][0], True, lc )                # Max temp rendered
        (tx2,ty2) = txt.get_size()                                      # Max temp dimensions
        self.screen.blit( txt, (xmax-tx2-dtx-4,ymax*(wy+gp*2)-ty2+4) )  # Max temp located on right edge
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*2)-ty2+9) )     # Degree symbol next
        txt = mfont.render( self.temps[2][1], True, lc )                # Min temp rendered
        (tx3,ty3) = txt.get_size()                                      # Min temp dimensions
        self.screen.blit( txt, (xmax-tx3-dtx-4,ymax*(wy+gp*2)-3) )      # Min temp located on right edge
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*2)+2) )         # Degree symbol next

        icon = pygame.image.load(sd + icons[self.icon[2]]).convert_alpha()
        (ix,iy) = icon.get_size()
        if self.scaleIcon:
            icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
            (ix,iy) = icon2.get_size()
            icon = icon2
        if ( iy < 90 ):
            yo = (90 - iy) / 2 
        else: 
            yo = 0
        self.screen.blit( icon, ((xmax*(wx+1)+tx1-max(tx2,tx3)-dtx)/2-ix/2-2,ymax*(wy+gp*2)-iy/2)  )    # Icon located in the Window middle

        # Sub Window 4
        txt = font.render( gettext(self.day[3], lang), True, lc )       # Label Weekday today+3
        (tx1,ty1) = txt.get_size()                                      # Weekday dimensions
        self.screen.blit( txt, (xmax*wx,ymax*(wy+gp*3)-ty1/2) )         # 
        txt = mfont.render( self.temps[3][0], True, lc )                # Max temp rendered
        (tx2,ty2) = txt.get_size()                                      # Max temp dimensions
        self.screen.blit( txt, (xmax-tx2-dtx-4,ymax*(wy+gp*3)-ty2+4) )  # Max temp located on right edge
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*3)-ty2+9) )     # Degree symbol next
        txt = mfont.render( self.temps[3][1], True, lc )                # Min temp rendered
        (tx3,ty3) = txt.get_size()                                      # Min temp dimensions
        self.screen.blit( txt, (xmax-tx3-dtx-4,ymax*(wy+gp*3)-3) )      # Min temp located on right edge
        self.screen.blit( dtxt, (xmax-dtx-4,ymax*(wy+gp*3)+2) )         # Degree symbol next
        
        icon = pygame.image.load(sd + icons[self.icon[3]]).convert_alpha()
        (ix,iy) = icon.get_size()
        if self.scaleIcon:
            icon2 = pygame.transform.scale( icon, (int(ix*1.5),int(iy*1.5)) )
            (ix,iy) = icon2.get_size()
            icon = icon2
        if ( iy < 90 ):
            yo = (90 - iy) / 2 
        else: 
            yo = 0
        self.screen.blit( icon, ((xmax*(wx+1)+tx1-max(tx2,tx3)-dtx)/2-ix/2-2,ymax*(wy+gp*3)-iy/2)  )    # Icon located in the Window middle

        # Update the display
        pygame.display.update()

    ####################################################################
    def disp_calendar(self):
        # Fill the screen with black
        self.screen.fill( (0,0,0) )
        xmin = 10
        xmax = self.xmax
        ymax = self.ymax
        lines = 5
        lc = (255,255,255) 
        sfn = "freemono"
        fn = "freesans"

        # Draw Screen Border
        pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )
        pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )

        # Time & Date
        th = self.tmdateTh
        sh = self.tmdateSmTh
        font = pygame.font.SysFont( fn, int(ymax*th), bold=1 )        # Regular Font
        sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=1 )        # Small Font for Seconds

        tm1 = time.strftime( "%a, %b %d   %H:%M", time.localtime() ).decode('utf-8').title()    # 1st part
        tm2 = time.strftime( "%S", time.localtime() )            # 2nd
        tm3 = "" #time.strftime( " %P", time.localtime() )            # 

        rtm1 = font.render( tm1, True, lc )
        (tx1,ty1) = rtm1.get_size()
        rtm2 = sfont.render( tm2, True, lc )
        (tx2,ty2) = rtm2.get_size()
        rtm3 = font.render( tm3, True, lc )
        (tx3,ty3) = rtm3.get_size()

        tp = xmax / 2 - (tx1 + tx2 + tx3) / 2
        self.screen.blit( rtm1, (tp,self.tmdateYPos) )
        self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )
        self.screen.blit( rtm3, (tp+tx1+tx2,self.tmdateYPos) )

        # Conditions
        ys = 0.20        # Yaxis Start Pos
        xs = 0.20        # Xaxis Start Pos
        gp = 0.075    # Line Spacing Gap
        th = 0.05        # Text Height

        cfont = pygame.font.SysFont( sfn, int(ymax*sh), bold=1 )
        #cal = calendar.TextCalendar()
        yr = int( time.strftime( "%Y", time.localtime() ) )    # Get Year
        mn = int( time.strftime( "%m", time.localtime() ) )    # Get Month
        cal = calendar.month( yr, mn ).splitlines()
        i = 0
        for cal_line in cal:
            if i==1:
                cal_line = string.replace(cal_line, '\xc3', 'a')
            txt = cfont.render( cal_line, True, lc )
            self.screen.blit( txt, (xmax*xs,ymax*(ys+gp*i)) )
            i = i + 1

        # Update the display
        pygame.display.update()

    ####################################################################
    def sPrint( self, s, font, x, l, lc ):
        f = font.render( s, True, lc )
        self.screen.blit( f, (x,self.ymax*0.075*l) )

    ####################################################################
    def disp_help( self, inDaylight, dayHrs, dayMins, tDaylight, tDarkness ):
        # Fill the screen with black
        self.screen.fill( (0,0,0) )
        xmax = self.xmax
        ymax = self.ymax
        xmin = 10
        lines = 5
        lc = (255,255,255) 
        sfn = "freemono"
        fn = "freesans"

        # Draw Screen Border
        pygame.draw.line( self.screen, lc, (xmin,0),(xmax,0), lines )
        pygame.draw.line( self.screen, lc, (xmin,0),(xmin,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmin,ymax),(xmax,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmax,0),(xmax,ymax), lines )
        pygame.draw.line( self.screen, lc, (xmin,ymax*0.15),(xmax,ymax*0.15), lines )

        thl = self.tmdateTh    # Large Text Height
        sh = self.tmdateSmTh    # Small Text Height

        # Time & Date
        font = pygame.font.SysFont( fn, int(ymax*thl), bold=1 )        # Regular Font
        sfont = pygame.font.SysFont( fn, int(ymax*sh), bold=1 )        # Small Font

        tm1 = time.strftime( "%a, %b %d   %H:%M", time.localtime() ).decode('utf-8').title()    # 1st part
        tm2 = time.strftime( "%S", time.localtime() )            # 2nd
        tm3 = ""    #time.strftime( " %P", time.localtime() )            # 

        rtm1 = font.render( tm1, True, lc )
        (tx1,ty1) = rtm1.get_size()
        rtm2 = sfont.render( tm2, True, lc )
        (tx2,ty2) = rtm2.get_size()
        rtm3 = font.render( tm3, True, lc )
        (tx3,ty3) = rtm3.get_size()

        tp = xmax / 2 - (tx1 + tx2 + tx3) / 2
        self.screen.blit( rtm1, (tp,self.tmdateYPos) )
        self.screen.blit( rtm2, (tp+tx1+3,self.tmdateYPosSm) )
        self.screen.blit( rtm3, (tp+tx1+tx2,self.tmdateYPos) )

        self.sPrint( gettext("Sunrise", lang) + ": %s" % self.sunrise, sfont, xmax*0.05, 3, lc )
        self.sPrint( gettext("Sunset",lang) + ": %s" % self.sunset, sfont, xmax*0.05, 4, lc )

        s = gettext("Daylight (Hrs:Min)",lang)+": %d:%02d" % (dayHrs, dayMins)
        self.sPrint( s, sfont, xmax*0.05, 5, lc )

        if inDaylight: s = gettext("Sunset in (Hrs:Min)",lang) + ": %d:%02d" % stot( tDarkness )
        else:          s = gettext("Sunrise in (Hrs:Min)",lang) + ": %d:%02d" % stot( tDaylight )
        self.sPrint( s, sfont, xmax*0.05, 6, lc )

        s = gettext("Update",lang)+": %s" % self.wLastUpdate
        self.sPrint( s, sfont, xmax*0.05, 7, lc )

        cc = 'current_conditions'
        s = gettext("Current Cond",lang)+": %s" % gettext(self.w[cc]['text'], lang)
        self.sPrint( s, sfont, xmax*0.05, 8, lc )
        
        # Outside Temperature
        s = gettext("Outside Temp", lang)+": %s" % self.temp + uniTmp
        self.sPrint( s, sfont, xmax*0.05, 9, lc )

        s = gettext("Barometer", lang) + ": %s %s" % (self.baro, baroUnits)
        self.sPrint( s, sfont, xmax*0.05, 10, lc )

        s = gettext("Windspeed", lang)+  ": %.0f %s" % (float(self.wind_speed) * windScale, windSpeed)
        if self.gust != 'N/A': 
            s = s + '/' + self.gust
        if self.wind_speed != 'calm':
            s = s + ' @' + self.wind_direction + unichr(176)
        self.sPrint( s, sfont, xmax*0.05, 11, lc )

        s = gettext("Visibility", lang) + " %s %s" % (self.vis, visiUnits) 
        self.sPrint( s, sfont, xmax*0.05, 12, lc )

        # Update the display
        pygame.display.update()

    

    # Save a jpg image of the screen.
    ####################################################################
    def screen_cap( self ):
        pygame.image.save( self.screen, "screenshot.jpeg" )
        print "Screen capture complete."


# Helper function to which takes seconds and returns (hours, minutes).
############################################################################
def stot( sec ):
    min = sec.seconds // 60
    hrs = min // 60
    return ( hrs, min % 60 )


# Given a sunrise and sunset time string (sunrise example format '7:00 AM'),
# return true if current local time is between sunrise and sunset. In other
# words, return true if it's daytime and the sun is up. Also, return the 
# number of hours:minutes of daylight in this day. Lastly, return the number
# of seconds until daybreak and sunset. If it's dark, daybreak is set to the 
# number of seconds until sunrise. If it daytime, sunset is set to the number 
# of seconds until the sun sets.
# 
# So, five things are returned as:
#  ( InDaylight, Hours, Minutes, secToSun, secToDark).
############################################################################
def Daylight( sr, st ):
    inDaylight = False    # Default return code.

    # Get current datetime with tz's local day and time.
    tNow = datetime.datetime.now()

    # From a string like '7:00 AM', build a datetime variable for
    # today with the hour and minute set to sunrise.
    t = time.strptime( "07:00", '%H:%M' )       #t = time.strptime( sr, '%H:%M' ) # Temp Var
    tSunrise = tNow                    # Copy time now.
    # Overwrite hour and minute with sunrise hour and minute.
    tSunrise = tSunrise.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )
    
    # From a string like '8:00 PM', build a datetime variable for
    # today with the hour and minute set to sunset.
    t = time.strptime( "20:00", '%H:%M' ) #t = time.strptime( myDisp.sunset, '%H:%M' )
    tSunset = tNow                    # Copy time now.
    # Overwrite hour and minute with sunset hour and minute.
    tSunset = tSunset.replace( hour=t.tm_hour, minute=t.tm_min, second=0 )

    # Test if current time is between sunrise and sunset.
    if (tNow > tSunrise) and (tNow < tSunset):
        inDaylight = True        # We're in Daytime
        tDarkness = tSunset - tNow    # Delta seconds until dark.
        tDaylight = 0            # Seconds until daylight
    else:
        inDaylight = False        # We're in Nighttime
        tDarkness = 0            # Seconds until dark.
        # Delta seconds until daybreak.
        if tNow > tSunset:
            # Must be evening - compute sunrise as time left today
            # plus time from midnight tomorrow.
            tMidnight = tNow.replace( hour=23, minute=59, second=59 )
            tNext = tNow.replace( hour=0, minute=0, second=0 )
            tDaylight = (tMidnight - tNow) + (tSunrise - tNext)
        else:
            # Else, must be early morning hours. Time to sunrise is 
            # just the delta between sunrise and now.
            tDaylight = tSunrise - tNow

    # Compute the delta time (in seconds) between sunrise and set.
    dDaySec = tSunset - tSunrise        # timedelta in seconds
    (dayHrs, dayMin) = stot( dDaySec )    # split into hours and minutes.
    
    return ( inDaylight, dayHrs, dayMin, tDaylight, tDarkness )


############################################################################
def btnNext( channel ):
    global mode, dispTO

    if ( mode == 'c' ): mode = 'w'
    elif (mode == 'w' ): mode ='h'
    elif (mode == 'h' ): mode ='c'

    dispTO = 0

    print "Button Event!"


#==============================================================
#==============================================================



# Display all the available fonts.
#print "Fonts: ", pygame.font.get_fonts()

mode = 'w'        # Default to weather mode.

# Create an instance of the lcd display class.
myDisp = SmDisplay()

running = True        # Stay running while True
s = 0            # Seconds Placeholder to pace display.
dispTO = 0        # Display timeout to automatically switch back to weather dispaly.

# Loads data from Weather.com into class variables.
if myDisp.UpdateWeather() == False:
    print 'Startup Error: no data from Weather.com.'
    #running = False

# Attach GPIO callback to our new button input on pin #4.
#GPIO.add_event_detect( 4, GPIO.RISING, callback=btnNext, bouncetime=400)
#GPIO.add_event_detect( 17, GPIO.RISING, callback=btnShutdown, bouncetime=100)
btnShutdownCnt = 0

if 0: #GPIO.input( 17 ):
    print "Warning: Shutdown Switch is Active!"
    myDisp.screen.fill( (0,0,0) )
    icon = pygame.image.load(sd + 'shutdown.jpg')
    (ix,iy) = icon.get_size()
    myDisp.screen.blit( icon, (800/2-ix/2,400/2-iy/2) )
    font = pygame.font.SysFont( "freesans", 40, bold=1 )
    rf = font.render( "Please toggle shutdown siwtch.", True, (255,255,255) )
    (tx1,ty1) = rf.get_size()
    myDisp.screen.blit( rf, (800/2-tx1/2,iy+20) )
    pygame.display.update()
    pygame.time.wait( 1000 )
    #while GPIO.input( 17 ): pygame.time.wait(100)



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
while running:

    # Debounce the shutdown switch. The main loop rnus at 100ms. So, if the 
    # button (well, a switch really) counter "btnShutdownCnt" counts above
    # 25 then the switch must have been on continuously for 2.5 seconds.
    if 0: #GPIO.input( 17 ):
        btnShutdownCnt += 1
        if btnShutdownCnt > 25:
            print "Shutdown!"
            myDisp.screen.fill( (0,0,0) )
            icon = pygame.image.load(sd + 'shutdown.jpg')
            (ix,iy) = icon.get_size()
            myDisp.screen.blit( icon, (800/2-ix/2,400/2-iy/2) )
            font = pygame.font.SysFont( "freesans", 60, bold=1 )
            rtm1 = font.render( "Shuting Down!", True, (255,255,255) )
            (tx1,ty1) = rtm1.get_size()
            myDisp.screen.blit( rtm1, (800/2-tx1/2,iy+20) )
            pygame.display.update()
            pygame.time.wait( 1000 )
            #os.system("sudo shutdown -h now")
            #while GPIO.input( 17 ): pygame.time.wait(100)
    else:
        btnShutdownCnt = 0

    # Look for and process keyboard events to change modes.
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            # On 'q' or keypad enter key, quit the program.
            if (( event.key == K_KP_ENTER ) or (event.key == K_q)):
                running = False

            # On 'c' key, set mode to 'calendar'.
            elif ( event.key == K_c ):
                mode = 'c'
                dispTO = 0

            # On 'w' key, set mode to 'weather'.
            elif ( event.key == K_w ):
                mode = 'w'
                dispTO = 0

            # On 's' key, save a screen shot.
            elif ( event.key == K_s ):
                myDisp.screen_cap()

            # On 'h' key, set mode to 'help'.
            elif ( event.key == K_h ):
                mode = 'h'
                dispTO = 0

    # Automatically switch back to weather display after a couple minutes.
    if mode != 'w':
        dispTO += 1
        if dispTO > 3000:    # Five minute timeout at 100ms loop rate.
            mode = 'w'
    else:
        dispTO = 0

    # Calendar Display Mode
    if ( mode == 'c' ):
        # Update / Refresh the display after each second.
        if ( s != time.localtime().tm_sec ):
            s = time.localtime().tm_sec
            myDisp.disp_calendar()
        
    # Weather Display Mode
    if ( mode == 'w' ):
        # Update / Refresh the display after each second.
        if ( s != time.localtime().tm_sec ):
            s = time.localtime().tm_sec
            myDisp.disp_weather()    
            #ser.write( "Weather\r\n" )
        # Once the screen is updated, we have a full second to get the weather.
        # Once per minute, update the weather from the net.
        if ( s == 0 ):
            try:
                myDisp.UpdateWeather()
            except:
                print "Unhandled Error in UndateWeather."

    if ( mode == 'h'):
        # Pace the screen updates to once per second.
        if s != time.localtime().tm_sec:
            s = time.localtime().tm_sec        

            ( inDaylight, dayHrs, dayMins, tDaylight, tDarkness) = Daylight( myDisp.sunrise, myDisp.sunset )

            #if inDaylight:
            #    print "Time until dark (Hr:Min) -> %d:%d" % stot( tDarkness )
            #else:
            #    #print 'tDaylight ->', tDaylight
            #    print "Time until daybreak (Hr:Min) -> %d:%d" % stot( tDaylight )

            try:
                # Stat Screen Display.
                myDisp.disp_help( inDaylight, dayHrs, dayMins, tDaylight, tDarkness )
            except KeyError:
                print "Disp_Help key error."

        # Refresh the weather data once per minute.
        if ( int(s) == 0 ): myDisp.UpdateWeather()

    ( inDaylight, dayHrs, dayMins, tDaylight, tDarkness) = Daylight( myDisp.sunrise, myDisp.sunset )

    
    # Loop timer.
    pygame.time.wait( 100 )


pygame.quit()

