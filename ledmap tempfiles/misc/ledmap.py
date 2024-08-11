#!/usr/bin/env python3
#
# LED Map by Mark Harris
# Uses an LED Matrix to display the outline of a state (or US, or custom geography)
# along with the territory's airports METAR data.
#
# Define the size of the Matrix below at DISPLAY_X, DISPLAY_Y, CHAIN_LENGTH and PARALLEL.
# 64x32 and 64x64 Matrix display sizes have been tested singlely and chained.
# RPi Zero W works well, but slow to boot. RPi 3B works quite well and as
# imagined, RPi 4's work the best.
#
# FAA XML data is downloaded and each airport's Lon/Lat is then scaled to fit the display screen.
#   Format [lon,lat] = display's [x,y]
# Positive values of latitude are north of the equator, negative values to the south.
# For Longitude, most programs use negative values.
#   (from https://www.maptools.com/tutorials/lat_lon/formats)
#
# Use LED Matrix display available from Aliexpess and Adafruit.
# Prices seem to be all over the place. I found Aliexpress to be the least expensive.
# https://www.aliexpress.us/item/2251832840839037.html?spm=a2g0o.order_list.0.0.21ef1802T0SEXw&gatewayAdapt=glo2usa&_randl_shipto=US
# https://www.adafruit.com/product/3649
#
# This uses the awesome library rgbmatrix; https://github.com/hzeller/rpi-rgb-led-matrix
# Visit this site for details on connecting these displays using an adapter/hat.
# To install; (Taken from https://howchoo.com/pi/raspberry-pi-led-matrix-panel)
#   sudo apt-get update  && sudo apt-get install -y git python3-dev python3-pillow
#   git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
#   cd rpi-rgb-led-matrix
#   make build-python PYTHON=$(which python3)
#   sudo make install-python PYTHON=$(which python3)
#
# The script uses json files ('statelatlon.json.txt' & 'gz_2010_us_oulint_20m.json')
# that have each state's lon/lat values to create the outline of each state and USA.
# These files were found online at https://eric.clst.org/tech/usgeojson/ and
# https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_USA_0.json
#
# Another file; 'scalebystate.py' holds the State's scaling factors. This is needed to make
# the state look properly proportioned on the display depending on size of LED Matrix used.
# Values can be changed. There is a list for square displays and one for rectangular displays.
#
# The file 'state_ap_dict.py' holds all the airports that report metars organized by state.
# The file 'usa_ap_dict.py' holds various lists of airports to populate the US map. 
# The user can edit any of the airports if desired. 1 list has 1700+ airports,
# another has 3000+ airports and the the 3rd is user defined, currently setup for 183 airports.
#
# The file 'custom_layout.py' can be populated with a custom geographic area and airports, not bound
# by state borders. The outline can be a simple box or most any shape defined by lon/lats for points.
# This allows any geographic area such as one defined by a sectional, or even non-US territories to be used.
#
# Command line variables can be passed to tweak the behavior of the program.
# Example: 'sudo python3 ledmap.py interval=120 use_wipe=0 time_display=0'
# This command will run the software with 2 min intervals between updates with no wipes and no clock
# Do not add spaces around the '=' sign. Below is the list of available commands;
#    outline=1             # Show outline of state or not. 1=Yes, 0=No
#    point_or_line=1       # 0 = uses points, 1 = uses lines to draw outline of state.
#    metar_age="2.5"       # in hours, dictates how old the returned metars can be 2.5 hours is typical
#    delay=.0001           # .0001 = 1 microsecond, delay for painting pixels in wipes
#    interval=60           # 60 seconds, time states and going to FAA for updated metar data
#    use_wipe=1            # 1 = yes, 0 = no
#    show_title=1          # 1 = yes, 0 = no
#    ltng_brightness=100   # Lightning Brightness in percent (0% to 100%).
#    hiwind_brightness=10  # Hi Winds Brightness in percent (0% to 100%).
#    default_brightness=40 # Normal Brightness in percent (0% to 100%).
#    max_windspeedkt=10    # in Knots, used to determine when an airport should flash to show high windspeed
#    time_display=1        # 1 = yes, 0 = no
#    state_list_to_use=1   # Choose which list of states to display. See file scalebystate.py for lists
#    display_lightning=1   # 1 = yes, 0 = no
#    display_hiwinds=1     # 1 = yes, 0 = no
#    hiwinds_single=1      # 1 = draw high wind airports individually, 0 = draw them all at once.
#    clock_only = 0        # 1 = yes, 0 = no, this will only display the clock, and no metar data
#
# This software uses flask to create a web admin page that will control the behavior for the display.
# To access the admin page enter the IP address for the RPi and append ':5000' to it.
# For example, if the RPi is assigned the IP address, 192.168.0.32, then add ':5000' and enter;
# '192.168.0.32:5000' into a web browser that is on the same local network as the RPi.
# The file 'data.txt' holds the values for the variables that controls its behavior. 

#######################
# Import Dependencies #
#######################
import json
import time
from datetime import datetime
from datetime import time as time_
import string
import sys
import random
import socket
import flask                       # sudo apt install python3-flask
import xml.etree.ElementTree as ET
import urllib.request, urllib.error, urllib.parse
from state_ap_dict import *        # dict that lists each state and airport with metars
from scalebystate import *         # dict that allows custom scaling of each state into display window
from state_lists import *          # get the list of states to display
from custom_layout import *        # get custom area info
from usa_ap_dict import *          # get USA airports to display
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
from PIL import Image
from PIL import ImageDraw

##################
# Define Display #
##################
# Configuration of LED Matrix to be used.
# See https://github.com/hzeller/rpi-rgb-led-matrix/blob/master/img/coordinates.png
DISPLAY_X = 64   # Set display size. Using P3 RGB Pixel panel HD Display 64x32 dot Matrix SMD2121 Led Module
DISPLAY_Y = 64   # https://www.aliexpress.com/item/2251832542670680.html?spm=a2g0o.order_list.0.0.18751802bvLio7&gatewayAdapt=4itemAdapt 
CHAIN_LENGTH = 3 # Number of daisy-chained panels. (Default: 1).
PARALLEL = 2     # parallel chains. range=1..3, See https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/adapter

# Constants to define overall size of display(s). DON'T EDIT
# i.e. if 2 64x64 are connected together then chain length should be 2 and size would then be 64x128
# if 4 64x64 are setup in a big square then chain lenght is 2 and parallel is 2 for a 128x128 display
TOTAL_X = DISPLAY_X * CHAIN_LENGTH
TOTAL_Y = DISPLAY_Y * PARALLEL 
 
#####################
# Default Variables #
#####################
# Edit these to provide a default starting point. These are altered by the web interface 
outline = 1           # Show outline of state or not. 1=Yes, 0=No
point_or_line = 1     # 0 = uses points, 1 = uses lines to draw outline of state. See NUM_STEPS below
metar_age = "2.5"     # dictates how old the returned metars can be 2.5 hours is typical
delay = .0001          # delay for painting pixels in wipes
interval = 5 * 60     # 1 min * 60 seconds, how long before switching to next state and updating FAA metar data
use_wipe = 1          # 1 = yes, 0 = no
show_title = 1        # 1 = yes, 0 = no
ltng_brightness = 100 # Lightning Brightness in percent (0% to 100%).
hiwind_brightness = 10 # Hi Winds Brightness in percent (0% to 100%).
default_brightness = 50 # Normal Brightness in percent (0% to 100%).
clock_brightness = default_brightness #100 # Clock Numbers Brightness in percent (0% to 100%).
max_windspeedkt = 15  # kts. used to determine when an airport should flash to show high windspeed
state_list_to_use = 0 # position holder
time_display = 1      # 1 = yes, 0 = no
display_lightning = 1 # 1 = yes, 0 = no
display_hiwinds = 1   # 1 = yes, 0 = no
hiwinds_single = 0    # 1 = draw each high wind airport individually, 0 = draw them all at once.
clock_only = 0        # 1 = yes, 0 = no, this will only display the clock, and no metar data
toggle_sec = 1        # 1 = yes, 0 = no, this toggles border to signify seconds

big_flash = 1         # 1 use large lightning flash, 0 use single pixel

# Initiate Lists and Dictonaries
flat_lonlat = [] 
flat_lat = []
flat_lon = []
rand_list = []        # list to create random list of display pixels for wipe
info = []
ap_ltng_dict = {}     # capture airports reporting Tstorms and lightning in dictionary
ap_wind_dict = {}     # capture airports whose winds are higher than max_windspeedkt

#LED Cycle times - Controls blink rates. Can change if necessary.
cycle0_wait = .9      # These cycle times all added together will equal the total amount of time
cycle1_wait = .9      # for each cycle, depending on flight category, winds etc.
cycle2_wait = .08     # For instance, VFR with 20 kts winds will have the first 3 cycles assigned
cycle3_wait = .1      # the color Green, then the remaining cycles will be black. Causing a blink
cycle4_wait = .08     # Lightning effect uses the short intervals at cycle 2 and cycle 4.
cycle5_wait = .5
cycle_wait = [cycle0_wait, cycle1_wait, cycle2_wait, cycle3_wait, cycle4_wait, cycle5_wait] #Used to create weather designation effects.
cycles = [0,1,2,3,4,5] # Used as an index for the cycle loop.

# Setup RGBMatrix Options instantiate it as matrix. See https://github.com/hzeller/rpi-rgb-led-matrix 
options = RGBMatrixOptions()
options.rows = DISPLAY_Y 
options.cols = DISPLAY_X
options.chain_length = CHAIN_LENGTH  # Number of displays connected together
options.parallel = PARALLEL          # Number of parallel chains
options.hardware_mapping = 'regular' # If using Adafruit hat change this to 'adafruit-hat'
options.brightness = default_brightness
# Slowdown GPIO. Needed for faster RPi's and/or slower panels (Default: 1).
# 1 works for RPi Zero's, 2 works for RPi 3's and 3 works with RPi 4's
# If you add more displays and there is a 'tearing' effect, increase this number
options.gpio_slowdown = 4  
matrix = RGBMatrix(options=options)

#############
# Constants #
#############
PATH = '/home/pi/ledmap/'
MULT = 1          # Default=1. Increasing will increase size of image displayed.
X_OFFSET = []    
Y_OFFSET = []    
NUM_STEPS = 1     # Adjust the resolution of the outline of the state. 1 is best, but slowest
HIWINDS_BLINK = 1 # Seconds to blink the high winds airports

RED = (255, 0, 0)       # used to denote IFR flight category
GREEN = (0, 200, 0)     # used to denote VFR flight category
BLUE = (0, 0, 255)      # used to denote MVFR flight category
MAGENTA = (255, 0, 255) # used to denote LIFR flight category
WHITE = (255, 255, 255) # used to denote No WX flight category
YELLOW = (255,255,0)    # used to denote Lightning in vicinity of airport
BLACK = (0, 0, 0)       # Used to clear display to black
GREY = (50, 50, 50)     # Used as outline color
DKGREY = (10,10,10)     # Used as background for Clock display
CYAN = (0,255,255)      # Misc color

state_color = GREY      # Set color of state outline here.
title_text_color = WHITE # Set the color of the State Name Title lettering
clock_text_color = RED  # Set the color of the Clock Numbers
clock_border_color = (0,0,235) # dimmer blue used when clock only is displayed

# Thunderstorm and lightning METAR weather description codes that denote lightning in the area.
wx_lghtn_ck = ["TS", "TSRA", "TSGR", "+TSRA", "TSRG", "FC", "SQ", "VCTS", "VCTSRA", "VCTSDZ", "LTG"]

# Create as many lists of states to display and store them in 'state_lists.py' and add name to list
state_list = [state_single_0,state_misc_1,state_complete_2,state_northeast_3,state_southeast_4,\
              state_midwest_5,state_southwest_6,state_west_7,state_all50_8,state_lower48_9]
state_list_to_use = state_list[9] # change the index to match the lists of lists above to default to.

# Choose which group of airports to display when 'USA' is chosen. See file 'usa_ap_dict.py'
# 'ap_user_dict' holds airports that the user populates.
# 'ap_1700_dict' holds over 1700 airports in the lower 48 plus Alaska and Hawaii
# 'ap_3000_dict' holds over 3000 airports in the lower 48 plus Alaska and Hawaii
usa_ap_dict = ap_1700_dict # use 'ap_user_dict' or 'ap_1700_dict' or 'ap_3000_dict'

# Dimmer variables - To disable, set 'lights_out' and 'lights_on' to same time 
now = datetime.now()          # Get current time and compare to timer setting
lights_out = time_(21, 30, 0) # Use 24 hour time. Set hour to turn off display        
lights_on = time_(6, 30, 0)  # format (hours, minutes, seconds) No leading zeros
timeoff = lights_out
end_time = lights_on
dimmness = 4                 # this is a diviser to reduce default_brightness. ie. 40/4 = 10
tmp_default_brightness = default_brightness # used for dimming routine

# Process variables passed via command line, or web admin page
# If new variables are to be used from the cmd line, add it to this list
variables = ['outline','point_or_line','metar_age','delay','interval','use_wipe',\
             'show_title','ltng_brightness','hiwind_brightness','default_brightness',\
             'clock_brightness','max_windspeedkt','state_list_to_use','time_display',\
             'display_lightning','display_hiwinds','hiwinds_single','clock_only']

if len(sys.argv) > 1: # Grab cmdline variables and assign them properly
    for j in range(1,len(sys.argv)):
        info.append(sys.argv[j].split("="))

        for j in range(len(info)):
            var = info[j][0]
            val = info[j][1]

            if var in variables:
                if var == 'outline':
                    outline = int(val)
                elif var == 'point_or_line':
                    point_or_line = int(val)
                elif var == 'metar_age':
                    metar_age = val # keep this in string format
                elif var == 'delay':
                    delay = float(val)
                elif var == 'interval':
                    interval = int(val)
                elif var == 'use_wipe':
                    use_wipe = int(val)
                elif var == 'show_title':
                    show_title = int(val)
                elif var == 'ltng_brightness':
                    ltng_brightness = int(val)
                elif var == 'hiwind_brightness':
                    hiwind_brightness = int(val)
                elif var == 'default_brightness':
                    default_brightness = int(val)
                    clock_brightness = default_brightness
                    tmp_default_brightness = default_brightness
                elif var == 'clock_brightness':
                    clock_brightness = int(val)
                elif var == 'max_windspeedkt':
                    max_windspeedkt = int(val)
                elif var == 'state_list_to_use':
                    state_list_to_use = state_list[int(val)]
                elif var == 'time_display':
                    time_display = int(val)
                elif var == 'display_lightning':
                    display_lightning = int(val)
                elif var == 'display_hiwinds':
                    display_hiwinds = int(val)
                elif var == 'hiwinds_single':
                    hiwinds_single = int(val)
                elif var == 'clock_only':
                    clock_only = int(val)
                    
    print("\nDisplaying the Following List of States:\n",str(state_list_to_use))
else:
    print("No cmd line variables, using default values from ledmap.py")


#############
# Functions #
#############
def display_image(image=PATH+'static/us_sectional.jpg'):
    print("In Display Image")
    image = Image.open(image).convert('RGB')
    image = image.resize((matrix.width, matrix.height), Image.ANTIALIAS)
    matrix.SetImage(image, 0, 0)
     
    
def time_in_range(start, end, x): # See if a time falls within a range
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
    
    
def get_ip_address(): # Get RPi IP address to display on start-up.
    ip_address = ''
    counter = 10
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while counter >= 0:
        try:
            s.connect(("8.8.8.8",80))
            ip_address = s.getsockname()[0]
            s.close()
        #    print("Admin IP:",ip_address) # debug
            return ip_address
        except:
            counter -= 1
            time.sleep(10) # if internet not available, wait 10 secs and try again up to 10 times.


def clock():
    toggle = 1
    matrix.brightness = clock_brightness
    
    while clock_only: # True:
        r,g,b = clock_border_color
        b1 = b - 30 # This color adjustment is for blue. If another primary color is used, this must be changed.
        if toggle:
            # (upper left, lower right, color, line thickness, fill, fill color)
            draw_square([0,0],[TOTAL_X-1,TOTAL_Y-1],(r,g,b),5,1,GREY)
        else:
            draw_square([0,0],[TOTAL_X-1,TOTAL_Y-1],(r,g,b1),5,1,GREY)

        now = datetime.now() # current date and time
        strtime = now.strftime("%I:%M") #:%S %p
        r,g,b = clock_text_color
        textColor = graphics.Color(r,g,b)
        r1,g1,b1 = BLACK
        textColor1 = graphics.Color(r1,g1,b1)
        text_len = graphics.DrawText(matrix, font0, text_width, font_height, textColor, strtime)
        
        start_pos1 = ((text_width - text_len)/2)+1
        graphics.DrawText(matrix, font0, start_pos1, (TOTAL_Y/2)+(font_height/2)-3, textColor1, strtime) # (matrix, font, pos, 10, textColor, STATE)                

        matrix.brightness = clock_brightness
        start_pos = (text_width - text_len)/2
        graphics.DrawText(matrix, font0, start_pos, (TOTAL_Y/2)+(font_height/2)-4, textColor, strtime) # (matrix, font, pos, 10, textColor, STATE)
        time.sleep(1)
        
        if toggle_sec:
            toggle = not toggle
    

def draw_square(up_left=[0,0],low_right=[TOTAL_X-1,TOTAL_Y-1],color=(0,0,255),thick=5,fill=1,fill_color=GREY):
    # pass the following or use defaults
    #   upper left and lower right pixels in list format
    #   line color and line thickness in rows
    #   fill 1 or 0, yes or no and color to fill in tuple
    r,g,b = color
    squ_color = graphics.Color(r,g,b)
    matrix.brightness = default_brightness

    if fill:
        r,g,b = fill_color
        x1,y1 = up_left
        x2,y2 = low_right
        for y in range(y1,y2):
            for x in range(x1,x2):
                matrix.SetPixel(x,y,r,g,b)
     
#    if fill:
#        clear(fill_color)
        
    for j in range(thick):               
        # upper left to upper right [0]=x, [1]=y
        graphics.DrawLine(matrix, up_left[0], up_left[1], low_right[0], up_left[1], squ_color)
        # upper right to lower right [0]=x, [1]=y
        graphics.DrawLine(matrix, low_right[0], up_left[1], low_right[0], low_right[1], squ_color)
        # lower right to lower left [0]=x, [1]=y
        graphics.DrawLine(matrix, low_right[0], low_right[1], up_left[0], low_right[1], squ_color)
        # lower left to upper right [0]=x, [1]=y
        graphics.DrawLine(matrix, up_left[0], low_right[1], up_left[0], up_left[1], squ_color)

        up_left[0] = up_left[0] + 1 
        up_left[1] = up_left[1] + 1
        low_right[0] = low_right[0] - 1
        low_right[1] = low_right[1] - 1


def rand(range_low, range_high): # Generate random int between 2 values for wipes
    rand_num = random.randint(range_low, range_high)
    return(rand_num)


def create_rand(x,y): # Create list of rand (x,y) tuples for wipes
    for i in range(1,y):
        for j in range(1,x):
            rand_list.append((random.randint(0,x),random.randint(0,y)))
    return(rand_list)


def clear(color=(0,0,0)): # Display pixels 1 at a time for LED Matrix only
    r,g,b = color
    matrix.Fill(r, g, b)
#    matrix.Clear() # alternate way to clear to black


# Time Display between updates from FAA
def display_time(display_length=5):
    r,g,b = clock_border_color
    draw_square([0,0],[TOTAL_X-1,TOTAL_Y-1],(r,g,b),5,1,GREY)
    matrix.brightness = default_brightness

    now = datetime.now() # current date and time
    strtime = now.strftime("%I:%M") #:%S %p
    r,g,b = clock_text_color
    textColor = graphics.Color(r,g,b)
    r1,g1,b1 = BLACK
    textColor1 = graphics.Color(r1,g1,b1)
    text_len = graphics.DrawText(matrix, font0, text_width, font_height, textColor, strtime)
    
    start_pos1 = ((text_width - text_len)/2)+1
    graphics.DrawText(matrix, font0, start_pos1, (TOTAL_Y/2)+(font_height/2)-4, textColor1, strtime) # (matrix, font, pos, 10, textColor, STATE)                

    start_pos = (text_width - text_len)/2
    graphics.DrawText(matrix, font0, start_pos, (TOTAL_Y/2)+(font_height/2)-5, textColor, strtime) # (matrix, font, pos, 10, textColor, STATE)

    matrix.brightness = default_brightness
    time.sleep(display_length)


# Display Title between updates
def display_title():
    matrix.brightness = default_brightness
    if STATE == "CUSTOM":
        num_words = len(custom_layout_dict['custom_name'].split())
        tmp_state = custom_layout_dict['custom_name']
    else:
        num_words = len(STATE.split())
        tmp_state = STATE
        
    draw_square([0,0],[TOTAL_X-1,TOTAL_Y-1],(0,0,250),1,1,BLACK)

    text_len = graphics.DrawText(matrix, font, text_width, font_height, textColor, tmp_state)
    if num_words == 1: #text_len < matrix.width:
        if text_len < matrix.width:
            start_pos = ((text_width - text_len)/2)+1
            graphics.DrawText(matrix, font, start_pos, (TOTAL_Y/2)+4, textColor, tmp_state) # (matrix, font, pos, 10, textColor, STATE)
        else:
            text_len = graphics.DrawText(matrix, font2, text_width, (TOTAL_Y/2)-6, textColor, tmp_state)
            start_pos = ((text_width - text_len)/2)+1
            graphics.DrawText(matrix, font2, start_pos, (TOTAL_Y/2)+6, textColor, tmp_state) # (matrix, font, pos, 10, textColor, STATE)
 
    else:
        word1, word2 = tmp_state.split()
        text_len = graphics.DrawText(matrix, font, text_width, 10, textColor, word1)
        start_pos = (text_width - text_len)/2
        graphics.DrawText(matrix, font, start_pos, (TOTAL_Y/2)-6, textColor, word1) # (matrix, font, pos, 10, textColor, STATE)

        text_len = graphics.DrawText(matrix, font, text_width, 25, textColor, word2)
        start_pos = (text_width - text_len)/2
        graphics.DrawText(matrix, font, start_pos, (TOTAL_Y/2)+8, textColor, word2) # (matrix, font, pos, 10, textColor, STATE)

    time.sleep(3)


def wipe1(iteration=1): # Display pixels 1 at a time in ordered pattern
    matrix.brightness = default_brightness
    for j in range(iteration):
        for y in range(0,TOTAL_Y):
            for x in range(0,TOTAL_X):
                matrix.SetPixel(x,y,rand(0,255),rand(0,255),rand(0,255)) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                time.sleep(delay)


def wipe2(iteration=1): # Display pixels in a random pattern
    matrix.brightness = default_brightness
    for j in range(iteration):
        for x,y in create_rand(TOTAL_X,TOTAL_Y):
            matrix.SetPixel(x,y,rand(10,255),rand(10,255),rand(10,255)) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            time.sleep(delay)
    

def wipe3(iteration=1): # left to right to left
    matrix.brightness = default_brightness
    delay =.02
    r,g,b = BLUE
    color = graphics.Color(r,g,b)
    r1,g1,b1 = BLACK
    blcolor = graphics.Color(r1,g1,b1)

    for j in range(iteration):
        for j in range(TOTAL_X):
            graphics.DrawLine(matrix, j, 0, j, TOTAL_Y, color)
            graphics.DrawLine(matrix, j-1, 0, j-1, TOTAL_Y, blcolor)
            time.sleep(delay)

        for k in range(TOTAL_X,-2,-1):
            graphics.DrawLine(matrix, k, 0, k, TOTAL_Y, color)
            graphics.DrawLine(matrix, k+1, 0, k+1, TOTAL_Y, blcolor)
            time.sleep(delay)


def wipe4(iteration=1): # up to down to up
    matrix.brightness = default_brightness
    delay =.02
    r,g,b = BLUE
    color = graphics.Color(r,g,b)
    r1,g1,b1 = BLACK
    blcolor = graphics.Color(r1,g1,b1)

    for j in range(iteration):
        for j in range(0,TOTAL_Y):
            graphics.DrawLine(matrix, 0, j, TOTAL_X, j, color)
            graphics.DrawLine(matrix, 0, j-1, TOTAL_X, j-1,  blcolor)
            time.sleep(delay)

        for k in range(TOTAL_Y,-2,-1):
            graphics.DrawLine(matrix, 0, k, TOTAL_X, k, color)
            graphics.DrawLine(matrix, 0, k+1, TOTAL_X, k+1, blcolor)
            time.sleep(delay)


#Rainbow Animation functions - altered from https://github.com/JJSilva/NeoSectional/blob/master/metar.py
def wipe5(iteration, animate=1):
    matrix.brightness = default_brightness
    def wheel(pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return (pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return (0, pos * 3, 255 - pos * 3)

    if animate:
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256*iteration,-1,-1):
            for x in range(TOTAL_X):
                for y in range(TOTAL_Y):
                    r,g,b = wheel((int((x*y) * 256 / (TOTAL_X*TOTAL_Y)) + j) & 255)
                    matrix.SetPixel(x,y,r,g,b)

#            time.sleep(.01)
    else: # Static image
        for j in range(1):
            for x in range(TOTAL_X):
                for y in range(TOTAL_Y):
                    r,g,b = wheel((int((x*y) * 256 / (TOTAL_X*TOTAL_Y)) + j) & 255)
                    matrix.SetPixel(x,y,r,g,b)
        

def convert_latlon(lat,lon): # Convert lat/lon into screen coordinates
    # https://stackoverflow.com/questions/59554125/how-to-convert-lat-lon-coordinates-to-coordinates-of-tkinter-canvas
    global maxlat, minlat, maxlon, minlon
    adj_maxlat = maxlat + Y_OFFSET 
    adj_minlat = minlat - Y_OFFSET
    adj_maxlon = maxlon + X_OFFSET
    adj_minlon = minlon - X_OFFSET
    x = int((lon - adj_minlon) * TOTAL_X / (adj_maxlon - adj_minlon))
    y = int(TOTAL_Y-(lat - adj_minlat) * TOTAL_Y / (adj_maxlat - adj_minlat)) # remove 'DISPLAY_Y-(' to invert Y axis
    return(x,y)

     
def read_file(state):
    # Opening JSON file
    # List found at https://web.archive.org/web/20130615162524/http://eric.clst.org/wupl/Stuff/gz_2010_us_040_00_500k.json
    f = open(PATH+'statelatlon.json.txt') # statelatlon.json.txt list stored locally
    data = json.load(f) # returns JSON object as a dictionary
    f.close() # Closing file
    return(data)


def draw_outline(state,use_cache=0): # 0 = read file to data, 1 = use cached data
    global coords, group
    global NUM_STEPS
    global maxlat, minlat, maxlon, minlon
    k = 0
    data = read_file("state") # Read Json file

    if STATE != "ALL50":
        if use_wipe:
            wipe4(1)

    if use_cache == 0:
        for i in data['features']:
            name = i['properties']['NAME'] # State name

            if name == state: # or state == "Usa": # name Choose which state to grab
                print("\nDisplaying:",name)
                coords = i['geometry']['coordinates'] # grab all the groups of coordinates
                
                for j in range(len(coords)): # iterate through each group                
                    # Flaten groups into 1 level to get min and max lat/lon
                    if len(coords) != 1:
                        for group in coords[j]: # iterate through each coord in the group
                            for coord in group: # flatten list of coords to get min and max values
                                flat_lonlat.append(coord)
                                flat_lon.append(coord[0])
                                flat_lat.append(coord[1])
                    else:
                        for group in coords[j]: # iterate through each coord in the group
                            flat_lonlat.append(group)
                            flat_lon.append(group[0])
                            flat_lat.append(group[1])
                            
                # Create imaginary box/display using the max and mins of the state's coordinates
                maxlat = max(flat_lat)
                minlat = min(flat_lat)
                maxlon = max(flat_lon)
                minlon = min(flat_lon)
                upper_left = [maxlat,minlon]
                lower_right = [minlat,maxlon]

    # Plot outline of STATE - Using groups of lists
    if outline == 1:
        if STATE != "ALL50":
            clear(BLACK)
            
#        print("---> Number of Lat/Lon Groups:",len(coords))
        if len(coords) > 1: # For states with multiple discontiguous areas
            for l in range(len(coords)):
                group = coords[l][0]
                
                for k in range(0,len(group), NUM_STEPS): # Skipping every 10 coords
                    item = group[k]
                    x_unit,y_unit = convert_latlon(item[1], item[0]) # item[0]=lon, item[1]=lat
                    pos = (x_unit*MULT, y_unit*MULT) # *MULT
                    pos1 = pos
                    
                    if k == 0:
                        pos2 = pos
                        pos0 = pos
                    
                    r,g,b = state_color
                    stcolor = graphics.Color(r,g,b)
                    
                    if point_or_line == 0: # draw state using points or lines
                        matrix.SetPixel(pos[0],pos[1],r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                    else:
                        if use_cache == 0:
                            graphics.DrawLine(matrix, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)
                        graphics.DrawLine(offscreen_canvas, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)
                        if k > len(group) - NUM_STEPS:
                            if use_cache == 0:
                                graphics.DrawLine(matrix, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                            graphics.DrawLine(offscreen_canvas, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                        pos2 = pos1
                        
        else: # For states with one contiguous area
            for j in range(0,len(flat_lonlat), NUM_STEPS): # Skipping every 10 coords
                item = flat_lonlat[j]
                x_unit,y_unit = convert_latlon(item[1], item[0]) # item[0]=lon, item[1]=lat
                pos = (x_unit*MULT, y_unit*MULT)
                pos1 = pos
                
                if j == 0:
                    pos2 = pos
                    pos0 = pos

                r,g,b = state_color
                stcolor = graphics.Color(r,g,b)
                
                if point_or_line == 0:
                    matrix.SetPixel(pos[0],pos[1],r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                else:
                    if use_cache == 0:
                        graphics.DrawLine(matrix, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)
                    graphics.DrawLine(offscreen_canvas, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)
                    if k > len(group) - NUM_STEPS:
                        if use_cache == 0:
                            graphics.DrawLine(matrix, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                        graphics.DrawLine(offscreen_canvas, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                    pos2 = pos1
                        

# Routine to draw outline of USA
def draw_usa(use_cache=0): # 0 = read file to data, 1 = use cached data.
    global NUM_STEPS, data
    global maxlat, minlat, maxlon, minlon
    lat, lon = 0,0
    name = "USA"
    
    if STATE != "ALL50":
        if use_wipe:
            wipe4(1)
    
    if use_cache == 0:
        f = open(PATH+'gz_2010_us_outline_20m.json') # usa.json.txt list stored locally
        data = json.load(f) # returns JSON object as a dictionary
        f.close() # Closing file

        print("\nDisplaying:",name)
        for i in range(len(data['features'])):

            coords = data['features'][i]['geometry']['coordinates'] # grab all the groups of coordinates
            
            for j in range(len(coords)): # iterate through each group
                lon,lat = coords[j] # iterate through each coord in the group
                if lon > 0 or lon < -125 or lat < 20: # Isolate just the continental US.
                    break
                flat_lonlat.append(coords[j])
                flat_lon.append(lon)
                flat_lat.append(lat)
                        
            # Create imaginary box/display using the max and mins of the state's coordinates
            maxlat = max(flat_lat)
            minlat = min(flat_lat)
            maxlon = max(flat_lon)
            minlon = min(flat_lon)
            upper_left = [maxlat,minlon]
            lower_right = [minlat,maxlon]
        print("---> Max Lat:",maxlat,"Min Lat:",minlat,"Max Lon:",maxlon,"Min Lon:",minlon)

    # Plot outline of USA - Using groups of lists
    if outline == 1:
        if STATE != "ALL50":
            clear(BLACK)
        
        for i in range(len(data['features'])):
            coords = data['features'][i]['geometry']['coordinates'] # grab all the groups of coordinates

            for j in range(len(coords)): # iterate through each group
                lon,lat = coords[j]
#                print(type(lat),lon) # debug

                x_unit,y_unit = convert_latlon(lat, lon) # lat, lon
                pos = (x_unit*MULT, y_unit*MULT) # *MULT
                pos1 = pos
                
                if j == 0:
                    pos2 = pos
                    pos0 = pos
                    
                r,g,b = state_color
                stcolor = graphics.Color(r,g,b)
                
                if point_or_line == 0: # draw state using points or lines
                    matrix.SetPixel(pos[0],pos[1],r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                else:
                    if use_cache == 0:
                        graphics.DrawLine(matrix, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)
                    graphics.DrawLine(offscreen_canvas, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)


                    if j > len(coords) - NUM_STEPS:
                        if use_cache == 0:
                            graphics.DrawLine(matrix, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                        graphics.DrawLine(offscreen_canvas, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                    pos2 = pos1


# Routine to draw outline of custom area, data located in custom_layout.py
def draw_custom(use_cache=0): # 0 = read file to data, 1 = use cached data.
    global NUM_STEPS
    global maxlat, minlat, maxlon, minlon
    lat, lon = 0,0
    name = custom_layout_dict['custom_name']
    
    if STATE != "ALL50":
        if use_wipe:
            wipe4(1)
    
    print("\nDisplaying:",name)    
    coords = custom_layout_dict['custom_outline'] # grab all the groups of coordinates
#    print(coords) # debug
        
    for j in range(len(coords)): # iterate through each group
        lon,lat = coords[j] # iterate through each coord in the group
        flat_lonlat.append(coords[j])
        flat_lon.append(lon)
        flat_lat.append(lat)
                    
        # Create imaginary box/display using the max and mins of the state's coordinates
        maxlat = max(flat_lat)
        minlat = min(flat_lat)
        maxlon = max(flat_lon)
        minlon = min(flat_lon)
        upper_left = [maxlat,minlon]
        lower_right = [minlat,maxlon]
#    print("---> Max Lat:",maxlat,"Min Lat:",minlat,"Max Lon:",maxlon,"Min Lon:",minlon)

    # Plot outline of custom layout
    if outline == 1:
        if STATE != "ALL50":
            clear(BLACK)
            
        for j in range(len(coords)): # iterate through each group
            lon,lat = coords[j]
#            print(type(lat),lon) # debug

            x_unit,y_unit = convert_latlon(lat, lon) # lat, lon
            pos = (x_unit*MULT, y_unit*MULT) # *MULT
            pos1 = pos
            
            if j == 0:
                pos2 = pos
                pos0 = pos
                
            r,g,b = state_color
            stcolor = graphics.Color(r,g,b)
            
            if point_or_line == 0: # draw state using points or lines
                matrix.SetPixel(pos[0],pos[1],r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            else:
                if use_cache == 0:
                    graphics.DrawLine(matrix, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)
                graphics.DrawLine(offscreen_canvas, pos1[0], pos1[1], pos2[0], pos2[1], stcolor)

                if j > len(coords) - NUM_STEPS:
                    if use_cache == 0:
                        graphics.DrawLine(matrix, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                    graphics.DrawLine(offscreen_canvas, pos2[0], pos2[1], pos0[0], pos0[1], stcolor)
                pos2 = pos1


def get_fc_color(flightcategory):
    if flightcategory == "VFR":
        color = GREEN
    elif flightcategory == "MVFR":
        color = BLUE
    elif flightcategory == "IFR":
        color = RED
    elif flightcategory == "LIFR":
        color = MAGENTA
    else:
        color = GREY                
    return(color)


def draw_apwx(STATE, use_cache=0): # draw airport weather flight category, 0 = get new data online
    global root # temp test
    if use_cache == 0:
        # Define URL to get weather METARS. If no METAR reported withing the last 2.5 hours, Airport LED will be white (nowx).
        url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
        print("---> Loading METAR Data")
        
        if STATE == "CUSTOM":
            airports = custom_layout_dict['airports']
        elif STATE == "USA":
            airports = usa_ap_dict['USA']
        else:
            airports = state_ap_dict[STATE.upper()]

        # Build url with over 300 airports if needed. More flexible and less limiting.
        # Thank you Daniel from pilotmap.co for the change to this routine that handles maps with more than 300 airports.
        contentStart = ['<response xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.2" xsi:noNamespaceSchemaLocation="http://www.aviationweather.gov/static/adds/schema/metar1_2.xsd">']
        content = []
        chunk = 0;
        stationList = ''
        
        for airportcode in airports:
            stationList += airportcode + ','
            chunk += 1
            if(chunk >= 300):
                stationList = stationList[:-1] #strip trailing comma from string

                while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ipadd = s.getsockname()[0] #get IP Address
                    print('RPI IP Address = ' + ipadd) #log IP address when ever FAA weather update is retreived.

                    result = ''
                    try:
                        result = urllib.request.urlopen(url + stationList).read()
                        r = result.decode('UTF-8').splitlines()
                        xmlStr = r[8:len(r)-2]
                        content.extend(xmlStr)
                        c = ['<x>']
                        c.extend(content)
                        root = ET.fromstringlist(c + ['</x>'])
                        print('Internet Available')
                        break
                    
                    except Exception as e:
                        print(str(e))
                        print('FAA Data is Not Available')
                        print(url + stationList)
                        print(result)
                        time.sleep(5)
                        pass

                stationList = ''
                chunk = 0

        stationList = stationList[:-1] #strip trailing comma from string
        url = url + stationList         
            
        while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ipadd = s.getsockname()[0] #get IP Address
            print('RPI IP Address = ' + ipadd) #log IP address when ever FAA weather update is retreived.

            try:
                result = urllib.request.urlopen(url).read()
                print('Internet Available')
                print(url) # Debug
                r = result.decode('UTF-8').splitlines()
                xmlStr = r[8:len(r)-2]
                content.extend(xmlStr)
                c = ['<x>']
                c.extend(content)
                root = ET.fromstringlist(c + ['</x>'])
                break
            except:
                print('FAA Data is Not Available')
                print(url) # debug
                time.sleep(5)
                pass

        c = ['<x>']
        c.extend(content)
        root = ET.fromstringlist(c + ['</x>'])


    # Grab the airport category, wind speed and various weather from the results given from FAA.
    # Start of METAR decode routine if 'metar_taf' equals 1. Script will default to this routine without a rotary switch installed.
    for metar in root.iter('METAR'):
        stationId = metar.find('station_id').text
        
        # Grab flight category from returned FAA data
        if metar.find('flight_category') is None: # if category is blank, then bypass
            flightcategory = "NONE"
        else:
            flightcategory = metar.find('flight_category').text
            
        # Grab lat/lon of airport
        if metar.find('latitude') is None: # if category is blank, then bypass
            lat = "0.000"
        else:
            lat = metar.find('latitude').text           
        if metar.find('longitude') is None: # if category is blank, then bypass
            lon = "0.000"
        else:
            lon = metar.find('longitude').text
            
        # Grab wind speeds from returned FAA data
        if metar.find('wind_speed_kt') is None: # if wind speed is blank, then bypass
            windspeedkt = 0
        else:
            windspeedkt = int(metar.find('wind_speed_kt').text)
            
        # Grab wind gust from returned FAA data - Lance Blank
        if metar.find('wind_gust_kt') is None: #if wind speed is blank, then bypass
            windgustkt = 0
        else:
            windgustkt = int(metar.find('wind_gust_kt').text)
            
        # Grab wind direction from returned FAA data
        if metar.find('wind_dir_degrees') is None: # if wind speed is blank, then bypass
            winddirdegree = 0
        else:
            winddirdegree = int(metar.find('wind_dir_degrees').text)
            
        # Grab Weather info from returned FAA data
        if metar.find('wx_string') is None: # if weather string is blank, then bypass
            wxstring = "NONE"
        else:
            wxstring = metar.find('wx_string').text
#            print(wxstring) # debug
        
        # Build list of airports that report tstorms and lightning in the area
        if wxstring in wx_lghtn_ck:
#            print(stationId, wxstring) # debug
            ap_ltng_dict[stationId] = [lat,lon,flightcategory,windspeedkt]

        # Build list of airports whose winds are higher than max_windspeedkt
        if windspeedkt >= max_windspeedkt:
            ap_wind_dict[stationId] = [lat,lon,flightcategory,windspeedkt]
            
        # Convert lat/lon into screen coordinates
        x_unit,y_unit = convert_latlon(float(lat),float(lon))

        # Draw Outline of State on Map
        pos = (x_unit*MULT,y_unit*MULT)
        
        pos1, pos2 = pos
        r,g,b = get_fc_color(flightcategory)
        matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
        offscreen_canvas.SetPixel(pos1,pos2,r,g,b) # copy display to offscreen fr


def reset_scale(state):
    global scale_list,X_OFFSET,Y_OFFSET
    global flat_lonlat,flat_lat,flat_lon,rand_list,ap_ltng_list
    if TOTAL_X != TOTAL_Y: # Rectangular Display Scaling
        scale_list = scalebystate_rect.get(state) # Scale states for Rectangular displays, 64x32 LED Matrix
    elif TOTAL_X == TOTAL_Y: # Square Display Scaling
        scale_list = scalebystate_square.get(state) # Scale states for Square displays, 64x64 LED Matrix
    else:
        scale_list = scalebystate_square.get(state) # Create a new scalebystate file with custom scaling    

    X_OFFSET = scale_list[0] # Offsets used to adjust image on screen in the X axis
    Y_OFFSET = scale_list[1] # Offsets used to adjust image on screen in the Y axis

    if state_list_to_use == state_all50_8: # No need to clear lists for all 50 states
        return

    # Clear previous state's coordinates before displaying the next state.
    flat_lonlat = [] 
    flat_lat = []
    flat_lon = []
    rand_list = []
    ap_ltng_dict.clear()
    ap_wind_dict.clear()


def big_flash(x,y,iter=1,size=5,numflash=3):
    global offscreen_canvas
    r,g,b = YELLOW
    for l in range(iter):    
        # Display lightning flash to create animation
        offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
        time.sleep(1)

        for j in range(size): # Size of flash
            k = j-int(j/3)
#            graphics.DrawCircle(offscreen_canvas, X, Y, j, Color)
            # Draw diagonal lines of flash
            offscreen_canvas.SetPixel(x+k,y+k,r,g,b)
            offscreen_canvas.SetPixel(x-k,y-k,r,g,b)
            offscreen_canvas.SetPixel(x-k,y+k,r,g,b)
            offscreen_canvas.SetPixel(x+k,y-k,r,g,b)
            # Draw horizontal and vertical lines of flash
            offscreen_canvas.SetPixel(x+j,y,r,g,b)
            offscreen_canvas.SetPixel(x-j,y,r,g,b)
            offscreen_canvas.SetPixel(x,y+j,r,g,b)
            offscreen_canvas.SetPixel(x,y-j,r,g,b)

        for j in range(numflash): # of flashes NOTE: Must be an Odd Number
            offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
            time.sleep(.1)              

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas) # return original screen
    time.sleep(.3)


def draw_lightning(state):
    if display_lightning == 0:
        return
    
#    print(ap_ltng_dict) # debug 
    lat = 0
    lon = 0
    coords = []
    if STATE == "CUSTOM":
        airports = custom_layout_dict['airports']
    elif STATE == "USA":
        airports = usa_ap_dict['USA']
    else:
        airports = state_ap_dict[state.upper()] 
        
    for airport in ap_ltng_dict:
#        print(airport) # debug
        coords = ap_ltng_dict.get(airport)
        lat,lon,flightcategory,windspeedkt = coords
        x_unit,y_unit = convert_latlon(float(lat),float(lon))

        # Draw on Map
        pos = (x_unit*MULT,y_unit*MULT)
        pos1, pos2 = pos

        if big_flash:
            big_flash(pos1,pos2)
        else:
            for j in range(2): # number of times to repeat the lightning flash
                matrix.brightness=ltng_brightness-20
                r,g,b = WHITE
                matrix.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                time.sleep(.1)
                
                matrix.brightness=ltng_brightness-10
                r,g,b = YELLOW
                matrix.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                time.sleep(.1)
                
                matrix.brightness=ltng_brightness
                r,g,b = YELLOW 
                matrix.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                time.sleep(.2)
            
                matrix.brightness=default_brightness
                r,g,b = get_fc_color(flightcategory)
                matrix.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
                time.sleep(.2)
    else:
        time.sleep(.01)


def draw_hiwinds(state): # draw high winds airport individually. This takes much longer.
    if display_hiwinds == 0:
        return
    
    lat = 0
    lon = 0
    coords = []
    if STATE == "CUSTOM":
        airports = custom_layout_dict['airports']
    elif STATE == "USA":
        airports = usa_ap_dict['USA']
    else:
        airports = state_ap_dict[state.upper()]
        
    for airport in ap_wind_dict:
        coords = ap_wind_dict.get(airport)
        lat,lon,flightcategory,windspeedkt = coords
        x_unit,y_unit = convert_latlon(float(lat),float(lon))

        # Draw on Map
        pos = (x_unit*MULT,y_unit*MULT)
        pos1, pos2 = pos
        
        matrix.brightness = hiwind_brightness
        r,g,b = get_fc_color(flightcategory)
        matrix.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
        time.sleep(HIWINDS_BLINK/2)
        
        matrix.brightness=default_brightness
        r,g,b = get_fc_color(flightcategory)
        matrix.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)

    else:
        time.sleep(.01)
 
 
def draw_hiwinds1(state): # Draw all high wind airports together, this is much better  
    if display_hiwinds == 0:
        return

    global offscreen_canvas
    lat = 0
    lon = 0
    coords = []
    if state == "CUSTOM":
        airports = custom_layout_dict['airports']
    elif STATE == "USA":
        airports = usa_ap_dict['USA']
    else:
        airports = state_ap_dict[state.upper()]
    
    draw_apwx(state,1)

    for airport in ap_wind_dict:
        coords = ap_wind_dict.get(airport)
        lat,lon,flightcategory,windspeedkt = coords
        x_unit,y_unit = convert_latlon(float(lat),float(lon))

        # Draw on Map
        pos = (x_unit*MULT,y_unit*MULT)
        pos1, pos2 = pos

        matrix.brightness = hiwind_brightness
        r,g,b = get_fc_color(flightcategory)
        offscreen_canvas.SetPixel(pos1,pos2,r,g,b) # KEY: matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    time.sleep(HIWINDS_BLINK)

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    time.sleep(HIWINDS_BLINK)
    matrix.brightness = default_brightness


def set_brightness():
    global tmp_default_brightness, default_brightness
    if time_in_range(timeoff, end_time, datetime.now().time()):
        default_brightness = tmp_default_brightness / dimmness
        print("Dimmed Brightness",datetime.now().time())
    else:
        default_brightness = tmp_default_brightness
        print("Default Brightness",datetime.now().time())


################
# Execute code #
################
if __name__ == "__main__":
    try:
        # Load different size fonts
        # See https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/fonts
        # To create your own fonts see https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/fonts
        # Example command to create 80 point font;
        #  sudo otf2bdf -v -o myfont80.bdf -r 72 -p 80 /usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf
        font = graphics.Font()
        font.LoadFont(PATH+"fonts/7x13.bdf")
        
        # Load font used for Clock and size it depending on total display size.
        font0 = graphics.Font()
        # 64x32, 64x64, 64x128
        if (TOTAL_X == 64 and TOTAL_Y == 32) or (TOTAL_X == 64 and TOTAL_Y == 64) or (TOTAL_X == 64 and TOTAL_Y == 128):
            font0.LoadFont(PATH+"fonts/10x20.bdf")
            font_height = 20
        # 128x64, 192x64, 128x128
        elif (TOTAL_X == 128 and TOTAL_Y == 64)  or (TOTAL_X == 128 and TOTAL_Y == 128):
            font0.LoadFont(PATH+"fonts/myfont30.bdf")
            font.LoadFont(PATH+"fonts/10x20.bdf")
            font_height = 28
        # 128x128, 192x128
        elif (TOTAL_X == 192 and TOTAL_Y == 64) or (TOTAL_X == 192 and TOTAL_Y == 128):
            font0.LoadFont(PATH+"fonts/myfont50.bdf")
            font_height = 43
            font.LoadFont(PATH+"fonts/10x20.bdf")
        # 192x192
        elif (TOTAL_X == 192 and TOTAL_Y == 192):
            font0.LoadFont(PATH+"fonts/myfont80.bdf")
            font.LoadFont(PATH+"fonts/myfont30.bdf")
            font_height = 75
        else:
            font0.LoadFont(PATH+"fonts/10x20.bdf")
            font_height = 20
            
        font1 = graphics.Font()
        font1.LoadFont(PATH+"fonts/6x10.bdf")
        font2 = graphics.Font()
        font2.LoadFont(PATH+"fonts/5x8.bdf")
        font3 = graphics.Font()
        font3.LoadFont(PATH+"fonts/4x6.bdf")
        
        text_width = matrix.width        
        offscreen_canvas = matrix.CreateFrameCanvas()

        if use_wipe:
            # Display image of US Sectional
            display_image()
            time.sleep(2)

            # Create box for text overlay on picture
            matrix.brightness = default_brightness
            r,g,b = YELLOW
            textColor = graphics.Color(r,g,b)
            
            # get length and height of line of text
            text_len1 = graphics.DrawText(matrix, font3, text_width, 12, textColor, get_ip_address())           
            text_ht1 = font3.height #30 # font3
            
            box_x = int((TOTAL_X - text_len1)/2)-2
            box_y = int((TOTAL_Y - (text_ht1*3)-6)/2)
            # (upper left, lower right, color, line thickness, fill, fill color)
            draw_square([box_x,box_y],[TOTAL_X-box_x,TOTAL_Y-box_y],(0,0,0),1,1,BLACK)

            # Display admin IP address in box
            text_len = graphics.DrawText(matrix, font3, text_width, 12, textColor, "Admin IP:")
            start_pos = (text_width - text_len)/2
            graphics.DrawText(matrix, font3, start_pos, (TOTAL_Y/2)-6, textColor, "Admin IP:") # (matrix, font, pos, 10, textColor, STATE)

            r,g,b = title_text_color
            textColor = graphics.Color(r,g,b)
            text_len = graphics.DrawText(matrix, font3, text_width, 12, textColor, get_ip_address())
            start_pos = (text_width - text_len)/2
            graphics.DrawText(matrix, font3, start_pos, (TOTAL_Y/2)+2, textColor, get_ip_address()) # (matrix, font, pos, 10, textColor, STATE)

            text_len = graphics.DrawText(matrix, font3, text_width, 12, textColor, ":5000")
            start_pos = (text_width - text_len)/2
            graphics.DrawText(matrix, font3, start_pos, (TOTAL_Y/2)+10, textColor, ":5000") # (matrix, font, pos, 10, textColor, STATE)
            time.sleep(7)   # display IP for X seconds
        
        clock() # 'clock_only' dictates if clock is shown or not

        if use_wipe:
            wipe5(1,1) # Rainbow wipe - iterations, animate-1=yes,0=no
            clear(BLACK)
            
        r,g,b = title_text_color
        textColor = graphics.Color(r,g,b)
        
        print("Press CTRL+C to stop.")
             
        while True: # Will continue indefinetly until ctrl-c is pressed.
            set_brightness()
            
            for STATE in state_list_to_use:
                offscreen_canvas.Clear()
                if time_display:
                    display_time() 

                if use_wipe:
                    wipe3(1)
                else:
                    clear(BLACK)
                    
                reset_scale(STATE) # get next state's scale information
                
                if STATE == "WASHINGTON D.C.": # force Maryland as state since washington d.c. does not have an outline available via database
                    STATE = "MARYLAND"

                if show_title == 1:
                    display_title()
                    
                # use appropriate outline draw routine, USA, State, or Custom.
                if STATE == "USA":
                    draw_usa()
                    draw_apwx(STATE) # Draw each state's airport flight category
                elif STATE == "CUSTOM":
                    draw_custom()
                    draw_apwx(STATE) # Draw each state's airport flight category
                elif STATE == "ALL50":
                    # Setup the screen to accommodate all 50 states
                    outline = 0 # turn off drawing the outline
                    draw_usa()
                    draw_outline(string.capwords("ALASKA"))
                    draw_outline(string.capwords("HAWAII"))
                    clear(BLACK)
                    # Now draw the outline of all 50 states  
                    outline = 1
                    draw_usa()
                    draw_outline(string.capwords("ALASKA"))
                    draw_outline(string.capwords("HAWAII"))
                       
                    # Draw the airport weather   
                    draw_apwx("USA")
                                                                                                   
                else:
                    draw_outline(string.capwords(STATE)) # Draw outline of state
                    draw_apwx(STATE) # Draw each state's airport flight category
 
                #Setup timed loop for updating FAA Weather that will run based on the value of 'interval' which is a user setting
                timeout_start = time.time() #Start the timer. When timer hits user-defined value, go back to outer loop to update FAA Weather.
                while time.time() < timeout_start + interval:
                    set_brightness()
                    
                    for cycle_num in cycles:
                        if (cycle_num in [2,4]): # Check for Thunderstorms
                            if STATE == "ALL50":
                                STATE = "USA"
                                draw_lightning(STATE) # Draw lightning for appropriate airports
                                STATE = "ALASKA"
                                draw_lightning(STATE) # Draw lightning for appropriate airports
                                STATE = "HAWAII"
                                draw_lightning(STATE) # Draw lightning for appropriate airports
                                STATE = "ALL50"
                            else:  
                                draw_lightning(STATE) # Draw lightning for appropriate airports
                            
                        if (cycle_num in [3,4,5]): # Check for High Winds
                            if hiwinds_single == 1:
                                if STATE == "ALL50":
                                    STATE = "USA"
                                    draw_hiwinds(STATE) # Draw lightning for appropriate airports
                                    STATE = "ALASKA"
                                    draw_hiwinds(STATE) # Draw lightning for appropriate airports
                                    STATE = "HAWAII"
                                    draw_hiwinds(STATE) # Draw lightning for appropriate airports
                                    STATE = "ALL50"
                                else:  
                                    draw_hiwinds(STATE) # Draw high wind airports 1 at a time
                            else:
                                if STATE == "ALL50":
                                    STATE = "USA"
                                    draw_hiwinds1(STATE) # Draw lightning for appropriate airports
                                    STATE = "ALASKA"
                                    draw_hiwinds1(STATE) # Draw lightning for appropriate airports
                                    STATE = "HAWAII"
                                    draw_hiwinds1(STATE) # Draw lightning for appropriate airports
                                    STATE = "ALL50"
                                else:  
                                    draw_hiwinds1(STATE) # Draw high wind airports all together

                        wait_time = cycle_wait[cycle_num] #cycle_wait time is a user defined value
                        time.sleep(wait_time/2) #pause between cycles. pauses are setup in user definitions.

                    time.sleep(.1) 

    except KeyboardInterrupt:
        print("\n\nLED Map has been quit\n")
        sys.exit(0)

