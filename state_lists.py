# state_lists.py
# Support file for ledmap.py - Mark Harris
# Define states to list. These are predefined but can be added to.
# If one is added, you will need to add the name of the list to ledmap.py
# The number at the end helps to dictate which index of the state_list to use.
# This file holds;
#    state_list(s), which is the list that ledmap.py will use to cycle through user defined lists of states including;
#      state_single_0, a single state to display continuously
#      state_misc_1, a miscelaneous list of states defined by user.
#      state_complete_2, simply a list of all the states to make building state_list easier.
#      state_northeast_3, list of northeast states
#      state_southeast_4, list of southeast states
#      state_midwest_5, list of midwest states
#      state_southwest_6, list of southwest states
#      state_west_7, list of west states

# Note: The state listed here in state_single_0 is only a place holder.
# The default value stored in ledmap.py will be used.
state_single_0 = [
    "ARIZONA",
    ] 

# User editable list of states to rotate through
state_misc_1 = [
    "CUSTOM",
    "USA",
    "MASSACHUSETTS",
    "SOUTH CAROLINA",
    "PENNSYLVANIA",
    "FLORIDA",
    "COLORADO",
    "ARIZONA",
    "ALASKA",
    "OREGON",
    "OKLAHOMA"
    ]

# _complete This is a Complete list of states. Use this to build the 'state_list' above to display
state_complete_2 = [
    "USA",
    "ALASKA",
    "ALABAMA",
    "ARKANSAS",
    "ARIZONA",
    "CALIFORNIA",
    "COLORADO",
    "CONNECTICUT",
    "DELAWARE",
    "FLORIDA",
    "GEORGIA",
    "HAWAII",
    "IOWA",
    "IDAHO",
    "ILLINOIS",
    "INDIANA",
    "KANSAS",
    "KENTUCKY",
    "LOUISIANA",
    "MASSACHUSETTS",
    "MARYLAND",
    "MAINE",
    "MICHIGAN",
    "MINNESOTA",
    "MISSOURI",
    "MISSISSIPPI",
    "MONTANA",
    "NORTH CAROLINA",
    "NORTH DAKOTA",
    "NEBRASKA",
    "NEW HAMPSHIRE",
    "NEW JERSEY",
    "NEW MEXICO",
    "NEVADA",
    "NEW YORK",
    "OHIO",
    "OKLAHOMA",
    "OREGON",
    "PENNSYLVANIA",
    "RHODE ISLAND",
    "SOUTH CAROLINA",
    "SOUTH DAKOTA",
    "TENNESSEE",
    "TEXAS",
    "UTAH",
    "VIRGINIA",
    "VERMONT",
    "WASHINGTON",
    "WISCONSIN",
    "WEST VIRGINIA",
    "WYOMING"
    ]

state_northeast_3 = [
    "USA",
    "MASSACHUSETTS",
    "RHODE ISLAND",
    "CONNECTICUT",
    "VERMONT",
    "NEW HAMPSHIRE",
    "MAINE",
    "PENNSYLVANIA",
    "NEW JERSEY",
    "NEW YORK"
    ]

state_southeast_4 = [
    "USA",
    "GEORGIA",
    "NORTH CAROLINA",
    "SOUTH CAROLINA",
    "VIRGINIA",
    "WEST VIRGINIA",
    "KENTUCKY",
    "TENNESSEE",
    "MISSISSIPPI",
    "ALABAMA",
    "DELAWARE",
    "MARYLAND",
    "FLORIDA",
    "LOUISIANA",
    "ARKANSAS"
    ]

state_midwest_5 = [
    "USA",    
    "MINNESOTA",
    "WISCONSIN",
    "ILLINOIS",
    "OHIO",
    "INDIANA",
    "MICHIGAN",
    "MISSOURI",
    "IOWA",
    "KANSAS",
    "NEBRASKA",
    "NORTH DAKOTA",
    "SOUTH DAKOTA"
    ]

state_southwest_6 = [
    "USA",
    "ARIZONA",
    "NEW MEXICO",
    "TEXAS",
    "OKLAHOMA"
    ]

state_west_7 = [
    "USA",
    "CALIFORNIA",
    "COLORADO",
    "NEVADA",
    "HAWAII",
    "ALASKA",
    "OREGON",
    "UTAH",
    "IDAHO",
    "MONTANA",
    "WYOMING",
    "WASHINGTON"
    ]

state_all50_8 = [
    "ALL50",
    ]

state_lower48_9 = [
    "USA",
    ]
