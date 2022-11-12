# ledmap_poweroff.py - Mark Harris

#from ledmap import *
import json
import sys
import time


def shutdown():

    print("One Moment Please...")
#    matrix.Clear()
    time.sleep(2)
    print("Screen Should Now Be Blank")

if __name__ == "__main__":
    shutdown()