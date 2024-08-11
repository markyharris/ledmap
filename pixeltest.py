#!/usr/bin/env python3
#
# LED Map by Mark Harris

import time
import sys
import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Constants
DISPLAY_X = 64 # cols
DISPLAY_Y = 64 # rows
CHAIN_LENGTH = 3
PARALLEL = 2

TOTAL_X = DISPLAY_X * CHAIN_LENGTH
TOTAL_Y = DISPLAY_Y * PARALLEL 

RED = (255, 0, 0)       # used to denote IFR flight category
GREEN = (0, 200, 0)     # used to denote VFR flight category
BLUE = (0, 0, 255)      # used to denote MVFR flight category
MAGENTA = (255, 0, 255) # used to denote LIFR flight category
WHITE = (255, 255, 255) # used to denote No WX flight category
YELLOW = (255,255,0)    # used to denote Lightning in vicinity of airport
BLACK = (0, 0, 0)       # Used to clear display to black
GREY = (100, 100, 100)     # Used as outline color
DKGREY = (10,10,10)     # Used as background for Clock display
CYAN = (0,255,255)      # Misc color

# Variables
rand_list = [] # create random list of display pixels
delay = 0
default_brightness = 50

# Setup RGB Matrix
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

# Bitmap Icons
# Create a grid of colors in a pictoral layout. 0 equals Black
# Set size for X and Y indexed from 1
Y = YELLOW
W = WHITE
B = BLUE
G = GREY

icon_lighttest_size = [20,20]
icon_lightningtest = [
    B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,
    B,0,Y,Y,Y,Y,Y,Y,Y,B,B,0,Y,Y,Y,Y,Y,Y,Y,B,
    B,Y,Y,Y,Y,Y,Y,Y,Y,B,B,Y,Y,Y,Y,Y,Y,Y,Y,B,
    B,Y,Y,Y,Y,Y,Y,Y,Y,B,B,Y,Y,Y,Y,Y,Y,Y,Y,B,
    B,0,0,Y,Y,Y,0,0,0,B,B,0,0,Y,Y,Y,0,0,0,B,
    B,0,Y,Y,Y,0,0,0,0,B,B,0,Y,Y,Y,0,0,0,0,B,
    B,Y,Y,0,0,0,0,0,0,B,B,Y,Y,0,0,0,0,0,0,B,
    B,Y,Y,0,0,0,0,0,0,B,B,Y,Y,0,0,0,0,0,0,B,
    B,Y,Y,0,0,0,0,0,0,B,B,Y,Y,0,0,0,0,0,0,B,
    B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,
    B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,
    B,0,Y,Y,Y,Y,Y,Y,Y,B,B,0,Y,Y,Y,Y,Y,Y,Y,B,
    B,Y,Y,Y,Y,Y,Y,Y,Y,B,B,Y,Y,Y,Y,Y,Y,Y,Y,B,
    B,Y,Y,Y,Y,Y,Y,Y,Y,B,B,Y,Y,Y,Y,Y,Y,Y,Y,B,
    B,0,0,Y,Y,Y,0,0,0,B,B,0,0,Y,Y,Y,0,0,0,B,
    B,0,Y,Y,Y,0,0,0,0,B,B,0,Y,Y,Y,0,0,0,0,B,
    B,Y,Y,0,0,0,0,0,0,B,B,Y,Y,0,0,0,0,0,0,B,
    B,Y,Y,0,0,0,0,0,0,B,B,Y,Y,0,0,0,0,0,0,B,
    B,Y,Y,0,0,0,0,0,0,B,B,Y,Y,0,0,0,0,0,0,B,
    B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,B,
    ]


icon_light_size = [7,7]
icon_lightning = [
    0,0,0,Y,Y,Y,0,
    0,0,Y,Y,Y,0,0,
    0,Y,Y,0,0,0,0,
    Y,Y,Y,Y,Y,Y,Y,
    0,0,0,Y,Y,Y,0,
    0,0,Y,Y,0,0,0,
    0,Y,0,0,0,0,0,
    ]


icon_snow_size = [7,7]
icon_snow = [
    0,W,0,W,0,W,0,
    W,W,0,W,0,W,W,
    0,0,W,0,W,0,0,
    W,W,0,W,0,W,W,
    0,0,W,0,W,0,0,
    W,W,0,W,0,W,W,
    0,W,0,W,0,W,0,
    ]


icon_rain_size = [7,7]
icon_rain = [
    0,0,0,G,G,G,0,
    0,G,G,G,G,G,G,
    G,G,G,G,G,G,G,
    G,G,G,G,G,G,G,
    0,0,B,0,B,0,B,
    0,B,0,B,0,B,0,
    B,0,B,0,B,0,0,
    ]


def disp_icon(x,y,icon,icon_size,iter=1,numflash=3):
    global offscreen_canvas1
    if numflash % 2 == 0: # force an odd number fo numflash
        numflash = numflash - 1

    i_width = icon_size[0]-1 # Set width of icon
    i_height = icon_size[1]-1 # Set height of icon
    i_x = 0
    i_y = 0
    offset_x = -int(i_width/2)-1 # Center the Icon over the airport
    offset_y = -int(i_height/2) # Center the Icon over the airport
    
    for l in range(iter):    
        offscreen_canvas1 = matrix.SwapOnVSync(offscreen_canvas1)
        time.sleep(1)
                
        for j in icon:
            if j == 0:
                if i_x > i_width:
                    i_x = 0
                    i_y += 1
                i_x += 1
                continue
            
            r,g,b = j # get color of pixel to draw            
            if i_x > i_width:
                i_x = 0
                i_y += 1
            i_x += 1
#            print(j,i_x,i_y) # debug
            offscreen_canvas1.SetPixel(x+i_x+offset_x,y+i_y+offset_y,r,g,b)

                
        for j in range(numflash): # of flashes NOTE: Must be an Odd Number
            offscreen_canvas1 = matrix.SwapOnVSync(offscreen_canvas1)
            time.sleep(.1)
            
        time.sleep(2)



def rand(range_low, range_high):
    rand_num = random.randint(range_low, range_high)
    return(rand_num)

def create_rand(x,y):
    for i in range(1,y):
        for j in range(1,x):
            rand_list.append((random.randint(0,x),random.randint(0,y)))
    return(rand_list)

# Display pixels 1 at a time
def clear(color=(0,0,0)):
    r,g,b = color
    matrix.Fill(r, g, b)
#    for y in range(0,DISPLAY_Y):
#        for x in range(0,DISPLAY_X):
#            matrix.SetPixel(x,y,color,color,color) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)

# Display pixels 1 at a time
def wipe1():
    for y in range(0,TOTAL_Y):
        for x in range(0,TOTAL_X):
            matrix.SetPixel(x,y,rand(0,255),rand(0,255),rand(0,255)) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
            time.sleep(delay)

# Display pixels in a random pattern
def wipe2():
    for x,y in create_rand(TOTAL_X,TOTAL_Y):
        matrix.SetPixel(x,y,rand(10,255),rand(10,255),rand(10,255)) # matrix.SetPixel(i,j,0,0,255) (x,y,R,G,B)
        time.sleep(delay)
    
def tempdraw(x,y):
    global offscreen_canvas, offscreen_canvas1
    # Draw Image on canvas
    offscreen_canvas.SetPixel(125,100,100,100,255) # test airport
    offscreen_canvas1.SetPixel(125,100,100,100,255) # test airport
    matrix.SetPixel(125,100,100,100,255) # directly to screen
    offscreen_canvas.SetPixel(x,y+1,255,100,255) # test airport
    offscreen_canvas1.SetPixel(x,y+1,255,100,255) # test airport
    matrix.SetPixel(x,y+1,255,100,255) # test airport
    offscreen_canvas.SetPixel(x,y,0,255,0) # directly to screen
    offscreen_canvas1.SetPixel(x,y,0,255,0) # directly to screen
    matrix.SetPixel(x,y,0,255,0) # directly to screen
#    offscreen_canvas = matrix.SwapOnVSync(offscreen_canvas)    
    pass

def big_flash(x,y,iter=1,size=5,numflash=3):
    global offscreen_canvas1
    r,g,b = YELLOW
    for l in range(iter):    
        # Display lightning flash to create animation
        offscreen_canvas1 = matrix.SwapOnVSync(offscreen_canvas1)
        time.sleep(1)

        for j in range(size): # Size of flash
            k = j-int(j/3)
#            graphics.DrawCircle(offscreen_canvas, X, Y, j, Color)
            # Draw diagonal lines of flash
            offscreen_canvas1.SetPixel(x+k,y+k,r,g,b)
            offscreen_canvas1.SetPixel(x-k,y-k,r,g,b)
            offscreen_canvas1.SetPixel(x-k,y+k,r,g,b)
            offscreen_canvas1.SetPixel(x+k,y-k,r,g,b)
            # Draw horizontal and vertical lines of flash
            offscreen_canvas1.SetPixel(x+j,y,r,g,b)
            offscreen_canvas1.SetPixel(x-j,y,r,g,b)
            offscreen_canvas1.SetPixel(x,y+j,r,g,b)
            offscreen_canvas1.SetPixel(x,y-j,r,g,b)


        for j in range(numflash): # of flashes NOTE: Must be an Odd Number
            offscreen_canvas1 = matrix.SwapOnVSync(offscreen_canvas1)
            time.sleep(.1)              

    offscreen_canvas1 = matrix.SwapOnVSync(offscreen_canvas1) # return original screen
    time.sleep(.3)


################
# Execute code #
################
if __name__ == "__main__":
    offscreen_canvas = matrix.CreateFrameCanvas()
    offscreen_canvas1 = matrix.CreateFrameCanvas()
#    offscreen_canvas2 = matrix.CreateFrameCanvas()
#    offscreen_canvas3 = matrix.CreateFrameCanvas()
    X = 74
    Y = 74
#    r,g,b = YELLOW
#    Color = graphics.Color(r,g,b)
    
    try:
        print("Press CTRL+C to stop.")
#        clear()
#        disp_icon(30,30,icon_lightning,icon_light_size,1)
#        clear()
#        disp_icon(30,30,icon_snow,icon_snow_size,1)
#        clear()
#        disp_icon(30,30,icon_rain,icon_rain_size,1)

#        sys.exit()

        for j in range(5):
            X = random.randint(0,TOTAL_X)
            Y = random.randint(0,TOTAL_Y)
            offscreen_canvas1.Clear()
#            offscreen_canvas.Clear()
            tempdraw(X,Y)

#            big_flash(X,Y,2,5) # (x,y,iterations, size)
            disp_icon(X,Y,icon_lightning,icon_light_size,1)
            clear()
            disp_icon(X,Y,icon_snow,icon_snow_size,1)
            clear()
            disp_icon(X,Y,icon_rain,icon_rain_size,1)


#            tempdraw(X,Y)
            time.sleep(2)


    except KeyboardInterrupt:
        sys.exit(0)
