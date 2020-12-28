#!/usr/bin/python3
# RPI High Speed Camera Software Suite (C) Kim Miikki and Alp Karakoc 2020
import os
from rpi.inputs import *

menu=list()

# Categories
# 1 Composition
# 2 Focusing Tools
categories=[
    "Region of Interest",
    "Focusing Tools",
]

# Menu format
# Category,Selection,"Description","Program name"
menu = [
  [1,1,"Preview and selection","roi-select.py"],
  [1,2,"ROI from a single picture","roi-picture.py"],
  [1,3,"ROI camera preview","roi-preview.py"],
  [1,4,"ROI manual selection","roi-manual.py"],
  [1,5,"Batch crop","roi-batch.py -i -p"],
  [2,6,"ROI sharpness level monitor","roi-sharpness.py"],
  [2,7,"Sharpness level monitor and camera (server)","capture-sharpness.py -s"],
  [2,8,"Sharpness live graph monitor       (client)","sharpmon.py"],
 ]

exitProgram=False
while not exitProgram:
    print("RPI High Speed Camera ROI Software Suite (C) Kim Miikki and Alp Karakoc 2020")
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
    selection=inputValue("task",0,i,0,"")
    if selection>0:
        arg=""
        pname=menu[selection-1][3]
        print("Launching: "+pname)
        print("")
        os.system(pname)
        print("")
        continue
    exitProgram=True
