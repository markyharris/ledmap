# ledmap
LED Map by Mark Harris

Uses an LED Matrix to display the outline of a state (or US, or custom geography)
along with the territory's airports METAR data.

Define the size of the Matrix below at DISPLAY_X, DISPLAY_Y, CHAIN_LENGTH and PARALLEL.
64x32 and 64x64 Matrix display sizes have been tested singlely and chained.
RPi Zero W works well, but slow to boot. RPi 3B works quite well and as
imagined, RPi 4's work the best.

FAA XML data is downloaded and each airport's Lon/Lat is then scaled to fit the display screen.
  Format [lon,lat] = display's [x,y]
Positive values of latitude are north of the equator, negative values to the south.
For Longitude, most programs use negative values.
  (from https://www.maptools.com/tutorials/lat_lon/formats)

Use LED Matrix display available from Aliexpess and Adafruit.
Prices seem to be all over the place. I found Aliexpress to be the least expensive.
https://www.aliexpress.us/item/2251832840839037.html?spm=a2g0o.order_list.0.0.21ef1802T0SEXw&gatewayAdapt=glo2usa&_randl_shipto=US
https://www.adafruit.com/product/3649

This uses the awesome library rgbmatrix; https://github.com/hzeller/rpi-rgb-led-matrix
Visit this site for details on connecting these displays using an adapter/hat.
To install; (Taken from https://howchoo.com/pi/raspberry-pi-led-matrix-panel)<br>
  sudo apt-get update  && sudo apt-get install -y git python3-dev python3-pillow<br>
  git clone https://github.com/hzeller/rpi-rgb-led-matrix.git<br>
  cd rpi-rgb-led-matrix<br>
  make build-python PYTHON=$(which python3)<br>
  sudo make install-python PYTHON=$(which python3)<br>

The script uses json files ('statelatlon.json.txt' & 'gz_2010_us_oulint_20m.json')
that have each state's lon/lat values to create the outline of each state and USA.
These files were found online at https://eric.clst.org/tech/usgeojson/ and
https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_USA_0.json

Another file; 'scalebystate.py' holds the State's scaling factors. This is needed to make
the state look properly proportioned on the display depending on size of LED Matrix used.
Values can be changed. There is a list for square displays and one for rectangular displays.

The file 'state_ap_dict.py' holds all the airports that report metars organized by state.
The file 'usa_ap_dict.py' holds various lists of airports to populate the US map. 
The user can edit any of the airports if desired. 1 list has 1700+ airports,
another has 3000+ airports and the the 3rd is user defined, currently setup for 183 airports.

The file 'custom_layout.py' can be populated with a custom geographic area and airports, not bound
by state borders. The outline can be a simple box or most any shape defined by lon/lats for points.
This allows any geographic area such as one defined by a sectional, or even non-US territories to be used.

Command line variables can be passed to tweak the behavior of the program.
Example: 'sudo python3 ledmap.py interval=120 use_wipe=0 time_display=0'
This command will run the software with 2 min intervals between updates with no wipes and no clock
Do not add spaces around the '=' sign. Below is the list of available commands;<br><ul>
   <li>outline=1             Show outline of state or not. 1=Yes, 0=No<br>
   <li>point_or_line=1       0 = uses points, 1 = uses lines to draw outline of state.<br>
   <li>metar_age="2.5"       in hours, dictates how old the returned metars can be 2.5 hours is typical<br>
   <li>delay=.0001           .0001 = 1 microsecond, delay for painting pixels in wipes<br>
   <li>interval=60           60 seconds, time states and going to FAA for updated metar data<br>
   <li>use_wipe=1            1 = yes, 0 = no<br>
   <li>show_title=1          1 = yes, 0 = no<br>
   <li>ltng_brightness=100   Lightning Brightness in percent (0% to 100%).<br>
   <li>hiwind_brightness=10  Hi Winds Brightness in percent (0% to 100%).<br>
   <li>default_brightness=40 Normal Brightness in percent (0% to 100%).<br>
   <li>max_windspeedkt=10    in Knots, used to determine when an airport should flash to show high windspeed<br>
   <li>time_display=1        1 = yes, 0 = no<br>
   <li>state_list_to_use=1   Choose which list of states to display. See file scalebystate.py for lists<br>
   <li>display_lightning=1   1 = yes, 0 = no<br>
   <li>display_hiwinds=1     1 = yes, 0 = no<br>
   <li>hiwinds_single=1      1 = draw high wind airports individually, 0 = draw them all at once.<br>
   <li>clock_only = 0        1 = yes, 0 = no, this will only display the clock, and no metar data<br>
</ul><br>
This software uses flask to create a web admin page that will control the behavior for the display.
To access the admin page enter the IP address for the RPi and append ':5000' to it.
For example, if the RPi is assigned the IP address, 192.168.0.32, then add ':5000' and enter;
'192.168.0.32:5000' into a web browser that is on the same local network as the RPi.
The file 'data.txt' holds the values for the variables that controls its behavior. 
