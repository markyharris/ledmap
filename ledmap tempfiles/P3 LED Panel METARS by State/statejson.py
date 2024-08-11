# Format [lon,lat]
# Positive values of latitude are north of the equator, negative values to the south.
# Longitude, most programs use negative values (from https://www.maptools.com/tutorials/lat_lon/formats)

# Imports
import json
import time
from turtle import *
import pygame
from pygame import gfxdraw
import xml.etree.ElementTree as ET
import urllib.request, urllib.error, urllib.parse

# Set variables
outline = 1 # Show outline of state or not. 1=Yes, 0=No
metar_age = "2.5"
airports = ["KSAD","KOLS","KFHU","KALK","KDMA","KRYN","KFHU","KP08","KAVQ","KCGZ","KIWA","KA39","KTUS","KRQE","KCHD","KGXF"\
,"KFFZ","KSDL","KGEU","KDVT","KPHX","KLUF","KLGF","KGYR","KNYL","KHII","KBVU","KPRC","KBLH","KIFP","KEED","KIGM"\
,"KGCN","KPGA","KKNB","KCMR","KINW","KFLG","KTYL","KSEZ","KSJN"]
flat_lonlat = []
flat_lat = []
flat_lon = []

# Constants
# Use P3 LED display. See https://www.instructables.com/Morphing-Digital-Clock/ for info
DISPLAY_X = 64 # Set display size. Using P3 RGB Pixel panel HD Display 64x32 dot Matrix SMD2121 Led Module
DISPLAY_Y = 64 # https://www.aliexpress.com/item/2251832542670680.html?spm=a2g0o.order_list.0.0.18751802bvLio7&gatewayAdapt=4itemAdapt
MULT = 10 # Changes the overall size of the drawing screen
X_OFFSET = 1 # Offsets used to adjust image on screen in the X axis
Y_OFFSET = .4 # Offsets used to adjust image on screen in the Y axis
SIZE = (DISPLAY_X*MULT, DISPLAY_Y*MULT)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (180, 180, 180)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 255)

NUM_STEPS = 10
LINE_WIDTH = 2
AP_SIZE = 8
STATE = "Arizona" #"gadm41_USA_0"

# Setup Pygame
pygame.init()
screen = pygame.display.set_mode(SIZE)
screen.fill(WHITE)

# Functions
def convert_latlon(lat,lon): # Convert lat/lon into screen coordinates
    # https://stackoverflow.com/questions/59554125/how-to-convert-lat-lon-coordinates-to-coordinates-of-tkinter-canvas
    global maxlat, minlat, maxlon, minlon
    adj_maxlat = maxlat + Y_OFFSET 
    adj_minlat = minlat - Y_OFFSET
    adj_maxlon = maxlon + X_OFFSET
    adj_minlon = minlon - X_OFFSET
    x = int((lon - adj_minlon) * DISPLAY_X / (adj_maxlon - adj_minlon))
    y = int(DISPLAY_Y-(lat - adj_minlat) * DISPLAY_Y / (adj_maxlat - adj_minlat)) # remove 'DISPLAY_Y-(' to invert Y axis
    return(x,y)


def print_coords(): # for debug purposes
    for j in range(0,len(flat_lonlat),10): # Skipping every 10 coords
        item = flat_lonlat[j]
        formatted_item = str(item[0])+", "+str(item[1])
        print(formatted_item) # debug
        
        
def read_file(stateorusa):
    # Opening JSON file
    # List found at https://web.archive.org/web/20130615162524/http://eric.clst.org/wupl/Stuff/gz_2010_us_040_00_500k.json
    if stateorusa == "usa":
        f = open('usa.json.txt') # usa.json.txt list stored locally
    else:
        f = open('statelatlon.json.txt') # statelatlon.json.txt list stored locally
    data = json.load(f) # returns JSON object as a dictionary
    f.close() # Closing file
    return(data)


def draw_outline(): # Draw outline of State
    global NUM_STEPS
    global maxlat, minlat, maxlon, minlon
    # Iterating through the json list
    data = read_file("state")
    for i in data['features']:
        if "USA" in STATE:
            name = i['geometry']['coordinates'] # USA name
            NUM_STEPS = 5000
        else:
            name = i['properties']['NAME'] # State name

        if name == STATE: #name Choose which state to grab
            print(name) # debug
            coords = i['geometry']['coordinates'] # grab all the groups of coordinates
     
            for j in range(len(coords)): # iterate through each group
#                print("Num of Groups:",len(coords)) # debug
#                print("J:",j)
#                print("Coords[j]:",coords[j])
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
        
            maxlat = max(flat_lat)
            minlat = min(flat_lat)
            maxlon = max(flat_lon)
            minlon = min(flat_lon)
            upper_left = [maxlat,minlon]
            lower_right = [minlat,maxlon]
#            print("Max Lat:",maxlat,"Min Lat:",minlat,"Max Lon:",maxlon,"Min Lon:",minlon) # debug

    # Plot outline of STATE
    if outline == 1:
        for j in range(0,len(flat_lonlat), NUM_STEPS): # Skipping every 10 coords
            item = flat_lonlat[j]
            x_unit,y_unit = convert_latlon(item[1], item[0]) # item[0]=lon, item[1]=lat
            pos = (x_unit*MULT, y_unit*MULT)
            pos1 = pos
            
            if j == 0:
                pos2 = pos
                pos0 = pos
        #    pygame.draw.circle(screen, BLACK, pos, 5)
            pygame.draw.line(screen, BLACK, pos1, pos2, width=LINE_WIDTH)
            if j > len(flat_lonlat) - NUM_STEPS:
                pygame.draw.line(screen, BLACK, pos2, pos0, width=LINE_WIDTH)       
            pos2 = pos1
        pygame.display.flip() # Update Screen
        #pygame.quit()


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


# Execute code
if __name__ == "__main__":
    draw_outline()
    
    #Define URL to get weather METARS. If no METAR reported withing the last 2.5 hours, Airport LED will be white (nowx).
    url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
    print("METAR Data Loading")
    
    for airportcode in airports:
        url = url + airportcode + ","
    url = url[:-1]                          #strip trailing comma from string
#    print(url) # debug

    while True:                             #check internet availability and retry if necessary. Power outage, map may boot quicker than router.
        try:
            content = urllib.request.urlopen(url)
            print('Internet Available')
            break
        except:
            print('FAA Data is Not Available')
            time.sleep(10)
            pass

    root = ET.fromstring(content.read())    #Process XML data returned from FAA

    #grab the airport category, wind speed and various weather from the results given from FAA.
    #start of METAR decode routine if 'metar_taf' equals 1. Script will default to this routine without a rotary switch installed.
    for metar in root.iter('METAR'):
        stationId = metar.find('station_id').text
        #grab flight category from returned FAA data
        if metar.find('flight_category') is None: #if category is blank, then bypass
            flightcategory = "NONE"
        else:
            flightcategory = metar.find('flight_category').text
        # grab lat/lon of airport
        if metar.find('latitude') is None: #if category is blank, then bypass
            lat = "NONE"
        else:
            lat = metar.find('latitude').text           
        if metar.find('longitude') is None: #if category is blank, then bypass
            lon = "NONE"
        else:
            lon = metar.find('longitude').text
        #grab wind speeds from returned FAA data
        if metar.find('wind_speed_kt') is None: #if wind speed is blank, then bypass
            windspeedkt = 0
        else:
            windspeedkt = int(metar.find('wind_speed_kt').text)
        #grab wind gust from returned FAA data - Lance Blank
        if metar.find('wind_gust_kt') is None: #if wind speed is blank, then bypass
            windgustkt = 0
        else:
            windgustkt = int(metar.find('wind_gust_kt').text)
        #grab wind direction from returned FAA data
        if metar.find('wind_dir_degrees') is None: #if wind speed is blank, then bypass
            winddirdegree = 0
        else:
            winddirdegree = int(metar.find('wind_dir_degrees').text)
        #grab Weather info from returned FAA data
        if metar.find('wx_string') is None: #if weather string is blank, then bypass
            wxstring = "NONE"
        else:
            wxstring = metar.find('wx_string').text
                       
        # Convert lat/lon into screen coordinates
        x_unit,y_unit = convert_latlon(float(lat),float(lon))
#        print(stationId,": ",flightcategory," - ",lat,lon,x_unit,y_unit) # debug       
        # Draw on Map
        pos = (x_unit*MULT,y_unit*MULT)
        pygame.draw.circle(screen, get_fc_color(flightcategory), pos, AP_SIZE)
        pygame.display.flip()

