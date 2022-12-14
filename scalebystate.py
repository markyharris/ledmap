# scalebystate.py
# Support file for ledmap.py - Mark Harris
# This file holds;
#  scalebystate_square, A dictionary setup by state with a list that holds scaling info for a Square displays
#  scalebystate_rect, A dictionary setup by state with a list that holds scaling info for a Rectangular displays
#      The dictionary list i.e. [1,.4], sets the aspect ratio of the state on the display.
#      Increasing the first number will cause the image to be squawshed in the X axis.
#      Increasing the second number will cause the image to be squawsed in the Y axis.
#      Play with these values till the state's aspect ratio looks correct.

#**********************************************************
# Change the state scaling for square displays, ie. 64x64.
#**********************************************************
scalebystate_square = {               
"ALASKA":[1,.4],
"ALABAMA":[1,.4],
"ARKANSAS":[1,.4],
"ARIZONA":[1,.4],
"CALIFORNIA":[1,.4],
"COLORADO":[1,.4],
"CONNECTICUT":[.1,.4],
"DELAWARE":[1,.4],
"FLORIDA":[1,.4],
"GEORGIA":[.8,.4],
"HAWAII":[1,.4],
"IOWA":[.2,1],
"IDAHO":[1,.4],
"ILLINOIS":[1.2,.2],
"INDIANA":[1,.4],
"KANSAS":[.2,1.2],
"KENTUCKY":[.2,1.3],
"LOUISIANA":[.4,1],
"MASSACHUSETTS":[.2,1],
"MARYLAND":[.2,.6],
"MAINE":[.8,.2],
"MICHIGAN":[.2,.4],
"MINNESOTA":[.5,.4],
"MISSOURI":[.4,.4],
"MISSISSIPPI":[1,.4],
"MONTANA":[.2,1.7],
"NORTH CAROLINA":[.2,1.8],
"NORTH DAKOTA":[.2,1.6],
"NEBRASKA":[.2,1.8],
"NEW HAMPSHIRE":[1.4,.2],
"NEW JERSEY":[1,.2],
"NEW MEXICO":[.6,.4],
"NEVADA":[1.2,.2],
"NEW YORK":[.4,1],
"OHIO":[.6,.6],
"OKLAHOMA":[.2,1.8],
"OREGON":[.4,1.2],
"PENNSYLVANIA":[.2,1.4],
"RHODE ISLAND":[.5,.1],
"SOUTH CAROLINA":[.2,.8],
"SOUTH DAKOTA":[.2,1.6],
"TENNESSEE":[.2,2],
"TEXAS":[.4,.8],
"UTAH":[1,.2],
"VIRGINIA":[.2,1.8],
"VERMONT":[1,.2],
"WASHINGTON":[.2,1.4],
"WISCONSIN":[1,.4],
"WEST VIRGINIA":[1,.4],
"WYOMING":[.4,1],
"WASHINGTON D.C.":[1,.4],
"USA":[2,8],
"CUSTOM":[.2,.4],
"ALL50":[2,.4]
}

#**********************************************************
# Change the state scaling for Rectangledisplays, ie. 64x32
#**********************************************************
scalebystate_rect = {               
"ALASKA":[3,.4],
"ALABAMA":[3,.4],
"ARKANSAS":[3,.4],
"ARIZONA":[2.5,.4],
"CALIFORNIA":[3,.4],
"COLORADO":[3,.4],
"CONNECTICUT":[.2,.2],
"DELAWARE":[1,.2],
"FLORIDA":[2,.4],
"GEORGIA":[3,.4],
"HAWAII":[3,.4],
"IOWA":[2,.4],
"IDAHO":[5,.4],
"ILLINOIS":[4,.2],
"INDIANA":[4,.4],
"KANSAS":[2.2,.8],
"KENTUCKY":[.2,.4],
"LOUISIANA":[2.4,1],
"MASSACHUSETTS":[1.2,.2],
"MARYLAND":[.4,.2],
"MAINE":[2.8,.2],
"MICHIGAN":[2,.4],
"MINNESOTA":[4,.4],
"MISSOURI":[3,.4],
"MISSISSIPPI":[3.2,.6],
"MONTANA":[1.2,.6],
"NORTH CAROLINA":[.2,.6],
"NORTH DAKOTA":[2,.6],
"NEBRASKA":[.6,.6],
"NEW HAMPSHIRE":[2.4,.2],
"NEW JERSEY":[2.4,.2],
"NEW MEXICO":[3,.4],
"NEVADA":[4.4,.2],
"NEW YORK":[2.4,.4],
"OHIO":[2.8,.4],
"OKLAHOMA":[1,.4],
"OREGON":[2.8,.6],
"PENNSYLVANIA":[1.2,.4],
"RHODE ISLAND":[1,.1],
"SOUTH CAROLINA":[1.6,.4],
"SOUTH DAKOTA":[3,.6],
"TENNESSEE":[.4,1.2],
"TEXAS":[3.8,.4],
"UTAH":[3.8,.2],
"VIRGINIA":[.8,.6],
"VERMONT":[2.4,.2],
"WASHINGTON":[2.2,.8],
"WISCONSIN":[3.4,.4],
"WEST VIRGINIA":[3,.4],
"WYOMING":[2.2,.4],
"WASHINGTON D.C.":[.4,.2],
"USA":[1,2],
"CUSTOM":[.2,.4],
"ALL50":[2,.4]
}