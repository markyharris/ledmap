# custom_layout.py
# Support file for ledmap.py - Mark Harris
# This allows for airports within a specific lat/lon boundary to be displayed.
# Geography outside the US can be setup as long as the FAA provides METAR data for the airports.
# Use a site like https://skyvector.com/ to find airports that report METARs
#
# Using Google maps, right click on a point and copy the lat/lon and paste into dictionary.
# ***Remember, the format is lON/lAT so you will need to reverse them in the dictionary.
#
# Format for 'custom_outline' is [lon, lat]
# Add as many lon/lat points as desired, but at least 5 to build a box.
# 5th should equal the first to close box. 
#
# Add the airports that fall within (or around) the boundaries set in 'custom_outline'.
# Be sure that 'custom_name' and 'airports' are surrounded by quotes but the lon/lats are not.
#
# The user can create as many of these custom areas as desired, but only the one named
# 'custom_layout_dict' will be used. So append a number to the other ones. See below for an example.

custom_layout_dict = {
    'custom_name': 'BELGIUM',
    'custom_outline': [[2.56225262343636, 51.075992555699244],[3.365943889357357, 51.36527096235415],\
                       [4.789487620906511, 51.4805916908242],[5.796966636040099, 51.154710964886284],\
                       [5.673199348587248, 50.77782913294189],[6.176500488867818, 50.67975034515648],
                       [6.339047740506623, 50.3305820632857],[5.865746929104925, 49.596689471792956],
                       [5.477952048163465, 49.51934666194392],[4.860843059764152, 49.93352079023177],
                       [4.813780567488973, 50.17154668765057],[4.2588205009266655, 49.9669388571095],
                       [3.3608775054447904, 50.4954559071349],[2.56225262343636, 51.075992555699244]],
    'airports': ['EHFS','EBOS','EBFN','LFQQ','EBCV','EBBR','EBAW','EBDT','EBBE','EBCI',\
               'EBFS','EBLB','ELLX','ETNN','EHBK','EBBL','EHWO']
    }


custom_layout_dict1 = {
    'custom_name': 'Northern Arizona',
    'custom_outline': [[-114.7683, 37.0103],[-109.1227, 37.0103],[-109.1227, 34.0493], \
                       [-114.7683, 34.0493],[-114.7683, 37.0103]],
    'airports': ['KFLG','KSEZ','KINW','KPGA','KGCN','KPRC','KSOW','KTYL','KIGM','KCMR',\
               'KIFP','KHII','KEED','KPAN','KRQE']
    }

