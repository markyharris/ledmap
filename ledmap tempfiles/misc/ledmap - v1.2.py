#!/usr/bin/env python3
#
# LED Map by Mark Harris
# Uses an LED Matrix to display outline of a state (or US) along with the state's airport's METAR data.
# Define the size of the Matrix below at DISPLAY_X and DISPLAY_Y. 64x32 and 64x64 sizes have been tested.
#
# FAA XML data is downloaded and each airport's Lon/Lat is then scaled to fit the display screen.
# Format [lon,lat] = display's [x,y]
# Positive values of latitude are north of the equator, negative values to the south.
# Longitude, most programs use negative values (from https://www.maptools.com/tutorials/lat_lon/formats)
#
# Use LED Matrix display. See https://www.instructables.com/Morphing-Digital-Clock/ for info
# along with the awesome library rgbmatrix; https://github.com/hzeller/rpi-rgb-led-matrix
#
# The script uses json files ('statelatlon.json.txt' & 'gz_2010_us_oulint_20m.json')
# that have each state's lon/lat values to create the outline of each state and USA.
#
# Another file; 'scalebystate.py' holds the State's scaling factors. This is needed to make the state look
# properly proportioned on the display depending on size of LED Matrix used. Values can be changed.
#
# The file 'usairportswithmetars.py' holds all the airports that report metars organized by state.
# The last entry of this file is for the airports to display when the Continental US is displayed.
# The user can edit any of the airports from the other states to the USA entry in this file.
#
# The file 'custom_layout.py' can be populated with a custom geographic area and airports, not bound
# by state borders. The outline can be a simple box or most any shape defined by lon/lats for points.
#
# Command line variables can be passed to tweak the behavior of the program.
# Example: 'sudo python3 ledmap.py interval=120 use_wipe=0 time_display=0'
# This command will run the software with 2 min intervals between updates with no wipes and no clock
# Do not add spaces around the '=' sign. Below is the list;
#    outline=1             # Show outline of state or not. 1=Yes, 0=No
#    point_or_line=1       # 0 = uses points, 1 = uses lines to draw outline of state.
#    metar_age="2.5"       # in hours, dictates how old the returned metars can be 2.5 hours is typical
#    delay=.001            # .001 = 1 microsecond, delay for painting pixels in wipes
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


# Import Dependencies
import json
import time
from datetime import datetime
import string
import sys
import random
import socket
import flask                       # sudo apt install python3-flask
import xml.etree.ElementTree as ET
import urllib.request, urllib.error, urllib.parse
from usairportswithmetars import * # dict that lists each state and airport with metars
from scalebystate import *         # dict that allows custom scaling of each state into display window
from state_lists import *          # get the list of states to display
from custom_layout import *        # get custom area info
from usa_ap_dict import *          # get USA airports to display
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Define Display Configuration of LED Matrix to be used.
DISPLAY_X = 64   # Set display size. Using P3 RGB Pixel panel HD Display 64x32 dot Matrix SMD2121 Led Module
DISPLAY_Y = 64   # https://www.aliexpress.com/item/2251832542670680.html?spm=a2g0o.order_list.0.0.18751802bvLio7&gatewayAdapt=4itemAdapt 
CHAIN_LENGTH = 2 # Number of daisy-chained panels. (Default: 1).
PARALLEL = 1     # parallel chains. range=1..3, See https://github.com/hzeller/rpi-rgb-led-matrix/tree/master/adapter

# Constants to define overall size of display(s)
# i.e. if 2 64x64 are connected together then chain length should be 2 and size would then be 64x128
# if 4 64x64 are setup in a big square then chain lenght is 2 and parallel is 2 for a 128x128 display
TOTAL_X = DISPLAY_X * CHAIN_LENGTH
TOTAL_Y = DISPLAY_Y * PARALLEL 
 

# Default Variables
outline = 1           # Show outline of state or not. 1=Yes, 0=No
point_or_line = 1     # 0 = uses points, 1 = uses lines to draw outline of state. See NUM_STEPS below
metar_age = "2.5"     # dictates how old the returned metars can be 2.5 hours is typical
delay = .0001          # delay for painting pixels in wipes
interval = 3 * 60     # 1 min * 60 seconds, how long before switching to next state and updating FAA metar data
use_wipe = 1          # 1 = yes, 0 = no
show_title = 1        # 1 = yes, 0 = no
ltng_brightness = 100 # Lightning Brightness in percent (0% to 100%).
hiwind_brightness = 10 # Hi Winds Brightness in percent (0% to 100%).
default_brightness = 50 # Normal Brightness in percent (0% to 100%).
clock_brightness = default_brightness #100 # Clock Numbers Brightness in percent (0% to 100%).
max_windspeedkt = 10  # kts. used to determine when an airport should flash to show high windspeed
state_list_to_use = 0 # position holder
time_display = 1      # 1 = yes, 0 = no
display_lightning = 1 # 1 = yes, 0 = no
display_hiwinds = 1   # 1 = yes, 0 = no
hiwinds_single = 0    # 1 = draw each high wind airport individually, 0 = draw them all at once.
clock_only = 0        # 1 = yes, 0 = no, this will only display the clock, and no metar data

toggle_sec = 1        # 1 = yes, 0 = no, this toggles border to signify seconds

# Initiate Lists and Dictonaries
flat_lonlat = [] 
flat_lat = []
flat_lon = []
rand_list = []        # list to create random list of display pixels for wipe
info = []
ap_ltng_dict = {}     # capture airports reporting Tstorms and lightning in dictionary
ap_wind_dict = {}     # capture airports whose winds are higher than max_windspeedkt

#LED Cycle times - Can change if necessary.
cycle0_wait = .9      # These cycle times all added together will equal the total amount of time$
cycle1_wait = .9      # Each  cycle, depending on flight category, winds and weather reported wi$
cycle2_wait = .08     # For instance, VFR with 20 kts winds will have the first 3 cycles assigne$
cycle3_wait = .1      # The cycle times then reflect how long each color cycle will stay on, pro$
cycle4_wait = .08     # Lightning effect uses the short intervals at cycle 2 and cycle 4 to crea$
cycle5_wait = .5
cycle_wait = [cycle0_wait, cycle1_wait, cycle2_wait, cycle3_wait, cycle4_wait, cycle5_wait] #Used to create weather designation effects.
cycles = [0,1,2,3,4,5] # Used as a index for the cycle loop.

# Setup RGBMatrix Options instantiate it as matrix. See https://github.com/hzeller/rpi-rgb-led-matrix 
options = RGBMatrixOptions()
options.rows = DISPLAY_Y 
options.cols = DISPLAY_X
options.chain_length = CHAIN_LENGTH  # 1 default, Number of displays connected together
options.parallel = PARALLEL
options.hardware_mapping = 'regular' # If using Adafruit hat change this to 'adafruit-hat'
options.brightness = default_brightness
options.gpio_slowdown = 2 # Slowdown GPIO. Needed for faster Pis and/or slower panels (Default: 1).
matrix = RGBMatrix(options=options)

# Constants
PATH = '/home/pi/ledmap/'
MULT = 1         # For LED Matrix use 1, mostly unused but here for future use as necessary.
X_OFFSET = []    #scale_list[0] #1 # Offsets used to adjust image on screen in the X axis
Y_OFFSET = []    #scale_list[1] #.4 # Offsets used to adjust image on screen in the Y axis
NUM_STEPS = 1    # Adjust the resolution of the outline of the state. 1 is best, but slowest
HIWINDS_BLINK = 1 # Seconds to blink the high winds airports

RED = (255, 0, 0)       # used to denote IFR flight category
GREEN = (0, 255, 0)     # used to denote VFR flight category
BLUE = (0, 0, 255)      # used to denote MVFR flight category
MAGENTA = (255, 0, 255) # used to denote LIFR flight category
WHITE = (255, 255, 255) # used to denote No WX flight category
YELLOW = (255,255,0)    # used to denote Lightning in vicinity of airport
BLACK = (0, 0, 0)       # Used to clear display to black
GREY = (50, 50, 50)     # Used as background for Clock display
DKGREY = (10,10,10)     # Used as background for Clock display
CYAN = (0,255,255)      # Used for State Name display

state_color = GREY      # Set color of state outline here.
title_text_color = WHITE # Set the color of the State Name Title lettering
clock_text_color = RED  # Set the color of the Clock Numbers
clock_border_color = (0,0,235) # brighter blue

# Thunderstorm and lightning METAR weather codes
wx_lghtn_ck = ["TS", "TSRA", "TSGR", "+TSRA", "TSRG", "FC", "SQ", "VCTS", "VCTSRA", "VCTSDZ", "LTG"]

# Create as many lists of states to display and store them in 'scalebystate.py' and add name to list
state_list = [state_single_0,state_misc_1,state_complete_2,state_northeast_3,state_southeast_4,\
              state_midwest_5,state_southwest_6,state_west_7]
state_list_to_use = state_list[2] # change the index to match the lists of lists above to default to.

# Process variables passed via command line, or web admin page
variables = ['outline','point_or_line','metar_age','delay','interval','use_wipe',\
             'show_title','ltng_brightness','hiwind_brightness','default_brightness',\
             'clock_brightness','max_windspeedkt','state_list_to_use','time_display',\
             'display_lightning','display_hiwinds','hiwinds_single','clock_only']

if len(sys.argv) > 1:
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
    print("Using Default Values for Variables")


# Functions
def get_ip_address(): # Get RPi IP address to display on Boot up.
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
#    print("Displaying Digital Clock") 
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
        text_len = graphics.DrawText(matrix, font0, text_width, 12, textColor, strtime)
        
        start_pos1 = ((text_width - text_len)/2)+1
        graphics.DrawText(matrix, font0, start_pos1, (TOTAL_Y/2)+7, textColor1, strtime) # (matrix, font, pos, 10, textColor, STATE)                

        matrix.brightness = clock_brightness
        start_pos = (text_width - text_len)/2
        graphics.DrawText(matrix, font0, start_pos, (TOTAL_Y/2)+6, textColor, strtime) # (matrix, font, pos, 10, textColor, STATE)
        time.sleep(1)
        
        if toggle_sec:
            toggle = not toggle
#        matrix.brightness = default_brightness
    

def draw_square(up_left=[0,0],low_right=[TOTAL_X-1,TOTAL_Y-1],color=(0,0,255),thick=5,fill=1,fill_color=GREY):
    #pass the following or use defaults
    #  upper left and lower right pixels in list format
    #  line color and line thickness in rows
    #  fill 1 or 0, yes or no and color to fill in tuple
    r,g,b = color
    squ_color = graphics.Color(r,g,b)
    matrix.brightness = default_brightness
    
    if fill:
        clear(fill_color)
        
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


# Time Display
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
    text_len = graphics.DrawText(matrix, font0, text_width, 12, textColor, strtime)
    
    start_pos1 = ((text_width - text_len)/2)+1
    graphics.DrawText(matrix, font0, start_pos1, (TOTAL_Y/2)+7, textColor1, strtime) # (matrix, font, pos, 10, textColor, STATE)                

#    matrix.brightness = clock_brightness
    start_pos = (text_width - text_len)/2
    graphics.DrawText(matrix, font0, start_pos, (TOTAL_Y/2)+6, textColor, strtime) # (matrix, font, pos, 10, textColor, STATE)

    matrix.brightness = default_brightness
    time.sleep(display_length)


# Display Title
def display_title():
    matrix.brightness = default_brightness
    if STATE == "CUSTOM":
        num_words = len(custom_layout_dict['custom_name'].split())
        tmp_state = custom_layout_dict['custom_name']
    else:
        num_words = len(STATE.split())
        tmp_state = STATE
        
    draw_square([0,0],[TOTAL_X-1,TOTAL_Y-1],(0,0,250),1,1,BLACK)

    text_len = graphics.DrawText(matrix, font, text_width, 10, textColor, tmp_state)
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
        graphics.DrawText(matrix, font, start_pos, (TOTAL_Y/2)-4, textColor, word1) # (matrix, font, pos, 10, textColor, STATE)

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
    #                display_time()
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


def draw_apwx(STATE, use_cache=0): # draw airport weather flight category, 0 = get new data
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
            
        # build url with up to 300 airports    
        for airportcode in airports:
            url = url + airportcode + ","
        url = url[:-1] # strip trailing comma from string
        

        while True: # check internet availability and retry if necessary. Power outage, map may boot quicker than router.
            try:
                content = urllib.request.urlopen(url)
                print('---> Internet Available')
                break
            except:
                print('---> FAA Data is Not Available')
                time.sleep(10)
                pass

        root = ET.fromstring(content.read())    #Process XML data returned from FAA

    # grab the airport category, wind speed and various weather from the results given from FAA.
    # start of METAR decode routine if 'metar_taf' equals 1. Script will default to this routine without a rotary switch installed.
    for metar in root.iter('METAR'):
        stationId = metar.find('station_id').text
        
        # grab flight category from returned FAA data
        if metar.find('flight_category') is None: # if category is blank, then bypass
            flightcategory = "NONE"
        else:
            flightcategory = metar.find('flight_category').text
            
        # grab lat/lon of airport
        if metar.find('latitude') is None: # if category is blank, then bypass
            lat = "NONE"
        else:
            lat = metar.find('latitude').text           
        if metar.find('longitude') is None: # if category is blank, then bypass
            lon = "NONE"
        else:
            lon = metar.find('longitude').text
            
        # grab wind speeds from returned FAA data
        if metar.find('wind_speed_kt') is None: # if wind speed is blank, then bypass
            windspeedkt = 0
        else:
            windspeedkt = int(metar.find('wind_speed_kt').text)
            
        # grab wind gust from returned FAA data - Lance Blank
        if metar.find('wind_gust_kt') is None: #if wind speed is blank, then bypass
            windgustkt = 0
        else:
            windgustkt = int(metar.find('wind_gust_kt').text)
            
        # grab wind direction from returned FAA data
        if metar.find('wind_dir_degrees') is None: # if wind speed is blank, then bypass
            winddirdegree = 0
        else:
            winddirdegree = int(metar.find('wind_dir_degrees').text)
            
        # grab Weather info from returned FAA data
        if metar.find('wx_string') is None: # if weather string is blank, then bypass
            wxstring = "NONE"
        else:
            wxstring = metar.find('wx_string').text
        
        # Build list of airports that report tstorms and lightning in the area
        if wxstring in wx_lghtn_ck:
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
    if TOTAL_X != TOTAL_Y: # Rectangular Display Scaling #DISPLAY_Y == 32:
        scale_list = scalebystate_rect.get(state) # Scale states for Rectangular displays, 64x32 LED Matrix
    elif TOTAL_X == TOTAL_Y: # Square Display Scaling #DISPLAY_Y == 64:
        scale_list = scalebystate_square.get(state) # Scale states for Square displays, 64x64 LED Matrix
    else:
        scale_list = scalebystate_square.get(state) # Create a new scalebystate file with custom scaling    

    X_OFFSET = scale_list[0] #1 # Offsets used to adjust image on screen in the X axis
    Y_OFFSET = scale_list[1] #.4 # Offsets used to adjust image on screen in the Y axis

    flat_lonlat = [] 
    flat_lat = []
    flat_lon = []
    rand_list = []
    ap_ltng_dict = {}


def draw_lightning(state):
    if display_lightning == 0:
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
        
    for airport in airports:
        if airport in ap_ltng_dict:
            coords = ap_ltng_dict.get(airport)
            lat,lon,flightcategory,windspeedkt = coords
            x_unit,y_unit = convert_latlon(float(lat),float(lon))

            # Draw on Map
            pos = (x_unit*MULT,y_unit*MULT)
            pos1, pos2 = pos

            matrix.brightness=ltng_brightness-20
            r,g,b = WHITE
            matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            time.sleep(.1)
            
            matrix.brightness=ltng_brightness-10
            r,g,b = YELLOW
            matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            time.sleep(.2)
            
            matrix.brightness=ltng_brightness
            r,g,b = YELLOW #WHITE
            matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            time.sleep(.1)
            
            matrix.brightness=default_brightness
            r,g,b = get_fc_color(flightcategory)
            matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
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
        
    for airport in airports:
        if airport in ap_wind_dict:
            coords = ap_wind_dict.get(airport)
            lat,lon,flightcategory,windspeedkt = coords
            x_unit,y_unit = convert_latlon(float(lat),float(lon))

            # Draw on Map
            pos = (x_unit*MULT,y_unit*MULT)
            pos1, pos2 = pos
            
            matrix.brightness = hiwind_brightness
            r,g,b = get_fc_color(flightcategory)
            matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            time.sleep(HIWINDS_BLINK/2)
            
            matrix.brightness=default_brightness
            r,g,b = get_fc_color(flightcategory)
            matrix.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)

        else:
            time.sleep(.01)
 
 
def draw_hiwinds1(state): # Draw all high wind airports together, this is quicker  
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
    
#    if state == 'USA':
#        draw_usa(1)
#    elif state == "CUSTOM":
#        draw_custom()
#    else:
#        draw_outline(state,1) # state name and use_cache, 1 bypasses re-reading all the data

    draw_apwx(state,1)

    for airport in airports:
        if airport in ap_wind_dict:
            coords = ap_wind_dict.get(airport)
            lat,lon,flightcategory,windspeedkt = coords
            x_unit,y_unit = convert_latlon(float(lat),float(lon))

            # Draw on Map
            pos = (x_unit*MULT,y_unit*MULT)
            pos1, pos2 = pos
  
            matrix.brightness = hiwind_brightness
            r,g,b = get_fc_color(flightcategory)
            offscreen_canvas.SetPixel(pos1,pos2,r,g,b) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    time.sleep(HIWINDS_BLINK)

    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)
    time.sleep(HIWINDS_BLINK)
    matrix.brightness = default_brightness


# Execute code
if __name__ == "__main__":
    try:        
        # Load different size fonts
        font = graphics.Font()
        font.LoadFont(PATH+"fonts/7x13.bdf")
        font0 = graphics.Font()
        font0.LoadFont(PATH+"fonts/10x20.bdf")
        font1 = graphics.Font()
        font1.LoadFont(PATH+"fonts/6x10.bdf")
        font2 = graphics.Font()
        font2.LoadFont(PATH+"fonts/5x8.bdf")
        font3 = graphics.Font()
        font3.LoadFont(PATH+"fonts/4x6.bdf")
        
        text_width = matrix.width        
        offscreen_canvas = matrix.CreateFrameCanvas()

        # Display admin IP address
        draw_square([0,0],[TOTAL_X-1,TOTAL_Y-1],(0,0,255),1,1,BLACK)
        matrix.brightness = default_brightness
        r,g,b = YELLOW
        textColor = graphics.Color(r,g,b)

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
        time.sleep(10)   
        
        clock() # 'clock_only' dictates if clock is shown or not

        if use_wipe:
            wipe5(1,1) # Rainbow wipe - iterations, animate-1=yes,0=no
            clear(BLACK)
            
        r,g,b = title_text_color
        textColor = graphics.Color(r,g,b)
        
        print("Press CTRL+C to stop.")
            
        while True: # Will continue indefinetly until ctrl-c is pressed.

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
                    
                    if use_wipe:
                        wipe4(1)
                    else:
                        clear(BLACK)
                    
                # use appropriate outline draw routine, USA, State, or Custom.
                if STATE == "USA":
                    draw_usa()
                elif STATE == "CUSTOM":
                    draw_custom()
                else:
                    draw_outline(string.capwords(STATE)) # Draw outline of state
                    
                draw_apwx(STATE) # Draw each state's airport flight category
 
                #Setup timed loop for updating FAA Weather that will run based on the value of 'interval' which is a user setting
                timeout_start = time.time() #Start the timer. When timer hits user-defined value, go back to outer loop to update FAA Weather.
                while time.time() < timeout_start + interval:                                           
 
                    for cycle_num in cycles:
                        if (cycle_num in [2,4]): # Check for Thunderstorms 
                            draw_lightning(STATE) # Draw lightning for appropriate airports
                            
                        if (cycle_num in [3,4,5]): # Check for High Winds
                            if hiwinds_single == 1:
                                draw_hiwinds(STATE) # Draw high wind airports 1 at a time
                            else:
                                draw_hiwinds1(STATE) # Draw high wind airports all together

                        wait_time = cycle_wait[cycle_num] #cycle_wait time is a user defined value
                        time.sleep(wait_time) #pause between cycles. pauses are setup in user definitions.

                    time.sleep(1) # delay before moving to the next state

    except KeyboardInterrupt:
        print("\n\nLED Map has been quit\n")
        sys.exit(0)

