# test_url.py

from usa_ap_dict import *
from lg_us_airports import *
import sys
import xml.etree.ElementTree as ET
import urllib.request, urllib.error, urllib.parse
import socket

def get_url():
    ap_num = 0
    delay_time = 10 
    metar_age = "2.5"
    url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
    airports = lg_us_airports #usa_ap_dict['USA']
    
    #Build URL to submit to FAA with the proper airports from the airports file for METARs and TAF's but not MOS data
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
                    time.sleep(delay_time)
                    pass

            stationList = ''
            chunk = 0


    stationList = stationList[:-1] #strip trailing comma from string

    url = url + stationList
#    print(url)
     
        
    while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ipadd = s.getsockname()[0] #get IP Address
        print('RPI IP Address = ' + ipadd) #log IP address when ever FAA weather update is retreived.

        try:
            result = urllib.request.urlopen(url).read()
            print('Internet Available')
            print(url)
            r = result.decode('UTF-8').splitlines()
            xmlStr = r[8:len(r)-2]
            content.extend(xmlStr)
            c = ['<x>']
            c.extend(content)
            root = ET.fromstringlist(c + ['</x>'])
            break
        except:
            print('FAA Data is Not Available')
            print(url)
            time.sleep(delay_time)
            pass

    c = ['<x>']
    c.extend(content)
    root = ET.fromstringlist(c + ['</x>'])
    
    print(root)
#    sys.exit()


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
#        if wxstring in wx_lghtn_ck:
#            ap_ltng_dict[stationId] = [lat,lon,flightcategory,windspeedkt]

        # Build list of airports whose winds are higher than max_windspeedkt
#        if windspeedkt >= max_windspeedkt:
#            ap_wind_dict[stationId] = [lat,lon,flightcategory,windspeedkt]
        ap_num += 1
        print(ap_num, stationId, flightcategory, windspeedkt, winddirdegree, wxstring)

if __name__ == "__main__":
    get_url()