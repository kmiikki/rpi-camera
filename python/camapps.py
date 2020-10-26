#!/usr/bin/python3
# RPI High Speed Camera Software Suite (C) Kim Miikki 2020
import os
from rpi.inputs import *

menu=list()

# Categories
# 1 Composition
# 2 Exposure
# 3 White Balance Calibration
# 4 Images and Videos
# 5 Image Analysis and Operations
categories=[
    "Composition",
    "Exposure",
    "White Balance Calibration",
    "Images and Videos",
    "Image Analysis and Operations"
]

# Menu format
# Category,Selection,"Description","Program name"
menu = [
  [1,1,"Camera info","camera_model.py"],
  [1,2,"Camera preview","campreview.py"],
  [1,3,"Video preview","vidpreview.py"],
  [2,4,"Auto exposure shutter speed","expss.py"],
  [2,5,"Exposure bracketing","bracket-exposure.py"],
  [2,6,"Detect minimum exposure time","dminexp.py"],
  [3,7,"Auto white balance (AWB) gains","awb_gains.py"],
  [3,8,"Optimal gains from a calibration file","optimum_gains.py"],
  [3,9,"Calibration","calibratecam.py"],
  [4,10,"Capture lossless pictures","capturepics-preview.py"],
  [4,11,"Camera","camera.py"],
  [4,12,"Camera without preview","capturepics.py"],
  [4,13,"Time-lapse","timelapse.py"],
  [4,14,"Video recorder","fpsvideo.py"],
  [5,15,"Create videos from images","gtlvideo.py"],
  [5,16,"Color analysis","rgbinfo.py"],
  [5,17,"Split images to RGB channels","rgbsplit.py"],
  [5,18,"Combine RGB channels to color images","rgbcombine.py"],
  [5,19,"Split RGB channels to gray scale","bw-rgbsplit.py"],
  [5,20,"Combine RGB gray scale channels to color images","bw-rgbcombine.py"],
  [5,21,"Convert images to PNG format","pics2png.py"],
  [5,22,"Images to time-lapse files","gen_tlfiles.py"]
 ]

exitProgram=False
while not exitProgram:
    print("RPI High Speed Camera Software Suite (C) Kim Miikki 2020")
    oldCategory=0
    i=0
    for cat,sel,description,name in menu:
        if oldCategory<cat:
            print("")
            print(categories[oldCategory])
            oldCategory=cat
        print(str(sel).rjust(2," "),description)
        i+=1
    print("")
    print(" 0 Exit")
    print("")
    selection=inputValue("task",0,i,0,"")
    if selection>0:
        arg=""
        pname=menu[selection-1][3]
        if selection==8:
            arg=input("Enter RGB calibration file name: ")
            pname+=" "
            pname+=arg
        print("Launching: "+pname)
        print("")
        os.system(pname)
        print("")
        continue
    exitProgram=True
