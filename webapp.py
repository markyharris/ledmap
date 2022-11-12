# webapp.py - Mark Harris
# for LED Map display
# This will provide a web interface to control the LED Map display. 

from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response
import os
import sys
from ledmap_poweroff import *
from admin import *

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

# variables
PATH = '/home/pi/ledmap/'

# Routes for flask
@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@app.route("/ledmap", methods=["GET", "POST"])
def ledmap():
    global fl_outline,fl_point_or_line,fl_metar_age,fl_delay,fl_interval,fl_use_wipe,fl_show_title,fl_ltng_brightness,fl_hiwind_brightness,\
        fl_default_brightness,fl_clock_brightness,fl_max_windspeedkt,fl_state_list_to_use,fl_time_display,fl_display_lightning,fl_display_hiwinds,\
        fl_hiwinds_single,fl_clock_only,fl_big_ltng_flash,fl_ltng_flash_size,fl_single_state,display 
     
    templateData = {
        'fl_outline': fl_outline,
        'fl_point_or_line': fl_point_or_line,
        'fl_metar_age': fl_metar_age,
        'fl_delay': fl_delay,
        'fl_interval': fl_interval,
        'fl_use_wipe': fl_use_wipe,
        'fl_show_title': fl_show_title,
        'fl_ltng_brightness': fl_ltng_brightness,
        'fl_hiwind_brightness': fl_hiwind_brightness,
        'fl_default_brightness': fl_default_brightness,
        'fl_clock_brightness': fl_clock_brightness,
        'fl_max_windspeedkt': fl_max_windspeedkt,
        'fl_state_list_to_use': fl_state_list_to_use,
        'fl_time_display': fl_time_display,
        'fl_display_lightning': fl_display_lightning,
        'fl_display_hiwinds': fl_display_hiwinds,
        'fl_hiwinds_single': fl_hiwinds_single,
        'fl_clock_only': fl_clock_only,
        'fl_big_ltng_flash': fl_big_ltng_flash,
        'fl_ltng_flash_size': fl_ltng_flash_size,
        'fl_single_state': fl_single_state,
        'name': name,
        'version': version
        }

# These are not used in the ledmap.html file
#        fl_point_or_line = request.form['fl_point_or_line']
#        fl_delay = request.form['fl_delay']
#        fl_clock_only = request.form['fl_clock_only']

    if request.method == "POST":
        display = request.form['display']

        try:
            fl_outline = request.form['fl_outline'] # Checkbox
            fl_outline = 1
        except:
            fl_outline = 0 
        
        fl_metar_age = request.form['fl_metar_age']
        fl_interval = request.form['fl_interval']
        
        try:
            fl_use_wipe = request.form['fl_use_wipe'] # Checkbox
            fl_use_wipe = 1
        except:
            fl_use_wipe = 0
        
        try:
            fl_show_title = request.form['fl_show_title'] # Checkbox
            fl_show_title = 1
        except:
            fl_show_title = 0
        
        fl_ltng_brightness = request.form['fl_ltng_brightness']  # Range
        fl_hiwind_brightness = request.form['fl_hiwind_brightness']  # Range
        fl_default_brightness = request.form['fl_default_brightness']  # Range
        fl_clock_brightness = request.form['fl_clock_brightness']  # Range
        fl_max_windspeedkt = request.form['fl_max_windspeedkt'] # Option List   
        fl_state_list_to_use = request.form['fl_state_list_to_use'] # Option List
        
        try:
            fl_time_display = request.form['fl_time_display'] # Checkbox
            fl_time_display = 1
        except:
            fl_time_display = 0
        
        try:
            fl_display_lightning = request.form['fl_display_lightning'] # Checkbox
            fl_display_lightning = 1
        except:
            fl_display_lightning = 0
        
        try:
            fl_display_hiwinds = request.form['fl_display_hiwinds'] # Checkbox
            fl_display_hiwinds = 1
        except:
            fl_display_hiwinds = 0
        
        try:
            fl_hiwinds_single = request.form['fl_hiwinds_single'] # Checkbox
            fl_hiwinds_single = 1
        except:
            fl_hiwinds_single = 0

        try:
            fl_big_ltng_flash = request.form['fl_big_ltng_flash'] # Checkbox
            fl_big_ltng_flash = 1
        except:
            fl_big_ltng_flash = 0
        
        fl_ltng_flash_size = request.form['fl_ltng_flash_size'] # range
        fl_single_state = request.form['fl_single_state'] # Option List
#        print('fl_single_state', fl_single_state) # debug
        fl_single_state = '"'+fl_single_state+'"'
                
        variables1 = 'outline='+str(fl_outline) +' '+'point_or_line='+str(fl_point_or_line) +' '+'metar_age='+str(fl_metar_age) +' '+'delay='+str(fl_delay) +' '+'interval='+str(fl_interval) +' '+ \
                    'use_wipe='+str(fl_use_wipe) +' '+'show_title='+str(fl_show_title) +' '+'ltng_brightness='+str(fl_ltng_brightness) +' '+'hiwind_brightness='+str(fl_hiwind_brightness) +' '+ \
                    'default_brightness='+str(fl_default_brightness) +' '+'fl_clock_brightness='+str(fl_clock_brightness) +' '+'max_windspeedkt='+str(fl_max_windspeedkt) +' '+'state_list_to_use='+str(fl_state_list_to_use) +' '+ \
                    'time_display='+str(fl_time_display) +' '+'display_lightning='+str(fl_display_lightning) +' '+'display_hiwinds='+str(fl_display_hiwinds) +' '+ \
                    'hiwinds_single='+str(fl_hiwinds_single) + ' ' + 'clock_only='+str(fl_clock_only) + ' ' + 'big_ltng_flash='+str(fl_big_ltng_flash) + ' ' + \
                    'ltng_flash_size='+str(fl_ltng_flash_size) + ' ' + 'single_state='+fl_single_state
        print("From HTML:",variables1) # debug

        if display == "powerdown":
            shutdown() 
            print("Powering Off RPi")
            os.system('sudo shutdown -h now')

        elif display == "reboot":
            os.system("ps -ef | grep 'ledmap.py' | awk '{print $2}' | xargs sudo kill")
            os.system('sudo reboot now')
            flash("Rebooting RPi - One Moment...")

        elif display == "off":
            os.system("ps -ef | grep 'ledmap.py' | awk '{print $2}' | xargs sudo kill")
            os.system('sudo python3 ' + PATH + 'ledmap_poweroff.py &')
            flash("Turning Off LED Map Display - One Moment...")

        elif display == "clock":
            os.system("ps -ef | grep 'ledmap.py' | awk '{print $2}' | xargs sudo kill")
            os.system('sudo python3 ' + PATH + 'ledmap.py clock_only=1 &')
            flash("Turning On LED Map In Clock Only Mode - One Moment...") 

        else:
            os.system("ps -ef | grep 'ledmap.py' | awk '{print $2}' | xargs sudo kill")
            os.system('sudo python3 ' + PATH + 'ledmap.py '+ variables1+' &')
            flash("Running LED Map") 
        
        # Write data to file
        write_data(fl_outline,fl_point_or_line,fl_metar_age,fl_delay,fl_interval,fl_use_wipe,fl_show_title,fl_ltng_brightness,fl_hiwind_brightness,\
        fl_default_brightness,fl_clock_brightness,fl_max_windspeedkt,fl_state_list_to_use,fl_time_display,fl_display_lightning,fl_display_hiwinds,\
        fl_hiwinds_single,fl_clock_only,fl_big_ltng_flash,fl_ltng_flash_size,fl_single_state)
        print("Writing Data to File")
        
        def convert_chkbox(name):
            if name == 1:
                name = '1'
            else:
                name = '0'
            return(name)
        
        fl_outline = convert_chkbox(fl_outline)
        fl_use_wipe = convert_chkbox(fl_use_wipe)
        fl_show_title = convert_chkbox(fl_show_title)
        fl_time_display = convert_chkbox(fl_time_display)
        fl_display_lightning = convert_chkbox(fl_display_lightning)
        fl_hiwinds_single = convert_chkbox(fl_hiwinds_single)
        fl_display_hiwinds = convert_chkbox(fl_display_hiwinds)
        fl_big_ltng_flash = convert_chkbox(fl_big_ltng_flash)
#        print(fl_display_hiwinds) # debug
      
        templateData = {
            'display': display,
            'fl_outline': fl_outline,
            'fl_point_or_line': fl_point_or_line,
            'fl_metar_age': fl_metar_age,
            'fl_delay': fl_delay,
            'fl_interval': fl_interval,
            'fl_use_wipe': fl_use_wipe,
            'fl_show_title': fl_show_title,
            'fl_ltng_brightness': fl_ltng_brightness,
            'fl_hiwind_brightness': fl_hiwind_brightness,
            'fl_default_brightness': fl_default_brightness,
            'fl_clock_brightness': fl_clock_brightness,
            'fl_max_windspeedkt': fl_max_windspeedkt,
            'fl_state_list_to_use': fl_state_list_to_use,
            'fl_time_display': fl_time_display,
            'fl_display_lightning': fl_display_lightning,
            'fl_display_hiwinds': fl_display_hiwinds,
            'fl_hiwinds_single': fl_hiwinds_single,
            'fl_clock_only': fl_clock_only,
            'fl_big_ltng_flash': fl_big_ltng_flash,
            'fl_ltng_flash_size': fl_ltng_flash_size,
            'fl_single_state': fl_single_state,
            'name': name,
            'version': version
            }

        return render_template("ledmap.html", **templateData)
    else:
        return render_template("ledmap.html", **templateData)

 
# Functions
def write_data(fl_outline,fl_point_or_line,fl_metar_age,fl_delay,fl_interval,fl_use_wipe,fl_show_title,fl_ltng_brightness,fl_hiwind_brightness,\
        fl_default_brightness,fl_clock_brightness,fl_max_windspeedkt,fl_state_list_to_use,fl_time_display,fl_display_lightning,fl_display_hiwinds,\
        fl_hiwinds_single,fl_clock_only,fl_big_ltng_flash,fl_ltng_flash_size,fl_single_state):
 
    f= open(PATH + "data.txt","w+")
    f.write(str(fl_outline)+"\n")
    f.write(str(fl_point_or_line)+"\n")
    f.write('"'+fl_metar_age+'"\n')
    f.write(str(fl_delay)+"\n")
    f.write(str(fl_interval)+"\n")
    f.write(str(fl_use_wipe)+"\n")
    f.write(str(fl_show_title)+"\n")
    f.write(str(fl_ltng_brightness)+"\n")
    f.write(str(fl_hiwind_brightness)+"\n")
    f.write(str(fl_default_brightness)+"\n")
    f.write(str(fl_clock_brightness)+"\n")
    f.write(str(fl_max_windspeedkt)+"\n")
    f.write(str(fl_state_list_to_use)+"\n")
    f.write(str(fl_time_display)+"\n")
    f.write(str(fl_display_lightning)+"\n")
    f.write(str(fl_display_hiwinds)+"\n")
    f.write(str(fl_hiwinds_single)+"\n")
    f.write(str(fl_clock_only)+"\n") 
    f.write(str(fl_big_ltng_flash)+"\n") 
    f.write(str(fl_ltng_flash_size)+"\n")
    f.write('"'+fl_single_state+'"\n')
    f.close()
    return (True)
    
def get_data():
    f=open(PATH + "data.txt", "r")
    Lines = f.readlines()
    fl_outline = Lines[0].strip()
    fl_point_or_line = Lines[1].strip()
    fl_metar_age = Lines[2].strip()
    fl_metar_age = fl_metar_age.strip('"')
    
    fl_delay = Lines[3].strip()
    fl_interval = Lines[4].strip()
    fl_use_wipe = Lines[5].strip()
    fl_show_title = Lines[6].strip()
    fl_ltng_brightness = Lines[7].strip()
    fl_hiwind_brightness = Lines[8].strip()
    fl_default_brightness = Lines[9].strip()
    fl_clock_brightness = Lines[10].strip()
    fl_max_windspeedkt = Lines[11].strip()
    fl_state_list_to_use = Lines[12].strip()
    fl_time_display = Lines[13].strip()
    fl_display_lightning = Lines[14].strip()
    fl_display_hiwinds = Lines[15].strip()
    fl_hiwinds_single = Lines[16].strip()
    fl_clock_only = Lines[17].strip()
    fl_big_ltng_flash = Lines[18].strip()
    fl_ltng_flash_size = Lines[19].strip()
    fl_single_state = Lines[20] #.strip()

    f.close()
    return (fl_outline,fl_point_or_line,fl_metar_age,fl_delay,fl_interval,fl_use_wipe,fl_show_title,fl_ltng_brightness,fl_hiwind_brightness,\
        fl_default_brightness,fl_clock_brightness,fl_max_windspeedkt,fl_state_list_to_use,fl_time_display,fl_display_lightning,fl_display_hiwinds,\
        fl_hiwinds_single,fl_clock_only,fl_big_ltng_flash,fl_ltng_flash_size,fl_single_state)


# Start of Flask
if __name__ == '__main__': 
#    error = 1/0 # Force webapp to stop executing for debug purposes
    fl_outline,fl_point_or_line,fl_metar_age,fl_delay,fl_interval,fl_use_wipe,fl_show_title,fl_ltng_brightness,fl_hiwind_brightness,\
        fl_default_brightness,fl_clock_brightness,fl_max_windspeedkt,fl_state_list_to_use,fl_time_display,fl_display_lightning,fl_display_hiwinds,\
        fl_hiwinds_single,fl_clock_only,fl_big_ltng_flash,fl_ltng_flash_size,fl_single_state = get_data()

    variables = 'outline='+fl_outline +' '+'point_or_line='+fl_point_or_line +' '+'metar_age='+fl_metar_age +' '+'delay='+fl_delay +' '+'interval='+fl_interval +' '+ \
                'use_wipe='+fl_use_wipe +' '+'show_title='+fl_show_title +' '+'ltng_brightness='+fl_ltng_brightness +' '+'hiwind_brightness='+fl_hiwind_brightness +' '+ \
                'default_brightness='+fl_default_brightness +' '+'fl_clock_brightness='+fl_clock_brightness +' '+'max_windspeedkt='+fl_max_windspeedkt +' '+'state_list_to_use='+fl_state_list_to_use +' '+ \
                'time_display='+fl_time_display +' '+'display_lightning='+fl_display_lightning +' '+'display_hiwinds='+fl_display_hiwinds +' '+ \
                'hiwinds_single='+fl_hiwinds_single + ' ' + 'clock_only='+fl_clock_only  + ' ' + 'big_ltng_flash='+fl_big_ltng_flash  + ' ' + \
                'ltng_flash_size='+fl_ltng_flash_size   + ' ' + 'single_state='+fl_single_state
    print("From GetData():",variables) # debug 

    os.system('sudo python3 ' + PATH + 'ledmap.py ' + variables + ' &')        
    app.run(debug=True, use_reloader=False, host='0.0.0.0') # use use_reloader=False to stop double loading  
    
             