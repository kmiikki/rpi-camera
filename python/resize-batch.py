#!/usr/bin/python3
# (C) Kim Miikki 2020
  
import cv2
import math
import os
import sys
from pathlib import Path
from datetime import datetime
import re
from rpi.inputs import *

# Global variables
IGNORE_ORIENTATION=False
CONVERT_TO_PNG=False
MAX_PIXELS=10000
DEFAULT_PIXELS=1600
ROUND_UP=False

fname=""
pictures=0
default_axis="x"
subdir=""
orientation=""
resize_length=0

# Arrays
subdirs=["resize_x","resize_y"]

inter_methods=[cv2.INTER_NEAREST,
               cv2.INTER_LINEAR,
               cv2.INTER_CUBIC,
               cv2.INTER_AREA,
               cv2.INTER_LANCZOS4
               ]
method=2

def newFilename(oldname,ext):
  newname=re.sub("\s+", "_", oldname.strip())
  if CONVERT_TO_PNG:
      newname+=".png"
  else:
      newname+=ext
  return newname

def create_subdir(resize_axis="X"):
    global subdir
    try:
        if resize_axis.upper()=="Y":
            subdir=subdirs[1]
        else:
            subdir=subdirs[0]
        if not os.path.exists(subdir):
            os.mkdir(subdir)
    except OSError:
        print("Unable to create a directory or directories under following path:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)

print("Image batch resize tool")

# Get current directory
curdir=os.getcwd()

path=Path(curdir)
foldername=os.path.basename(curdir)

override=inputYesNo("override","Override default options","N")
if override=="y":
    ans=inputYesNo("orientation selective resize","Orientation selective resize","Y")
    if ans=="y":
        IGNORE_ORIENTATION=False
    else:
        IGNORE_ORIENTATION=True
    ans=inputYesNo("images to png","Convert images to PNG","N")
    if ans=="y":
        CONVERT_TO_PNG=True
    else:
        CONVERT_TO_PNG=False
    ans=inputYesNo("ceil","Alternative A/R round method: ceil","N")
    if ans=="y":
        ROUND_UP=True
    else:
        ROUND_UP=False  

resize_width_enabled=inputYesNo("width","Resize by width","Y")
if resize_width_enabled=="y":
    orientation="X"
else:
    orientation="Y"

#tmp=orientation+" "
if resize_width_enabled=="y":
    tmp="width"
else:
    tmp="height"
resize_length=inputValue(tmp,1,MAX_PIXELS,DEFAULT_PIXELS,"","Value out of range!",False)

t1=datetime.now()
print("")
print("Resize options")
print("--------------")
print("Convert images to PNG: ",end="")
if CONVERT_TO_PNG:
    print("yes")
else:
    print("no")
print("A/R round method: ",end="")
if ROUND_UP:
    print("ceil")
else:
    print("int")

print("Resize method: "+str(inter_methods[method]))
if IGNORE_ORIENTATION:
    print("All images will be resized")
else:
    print("Only ",end="")
    if orientation=="X":
        print("landscape ",end="")
    else:
        print("portrait ",end="")
    print("images will be resized")
print("")
create_subdir(orientation)

for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    same_dimensions=True
    fname=p.name
    try:
      img = cv2.imread(str(path)+"/"+fname)
      # Get image dimensions
      w=img.shape[1]
      h=img.shape[0]
    except:
      print("Unable to resize: "+fname)
      continue
    else:
      try:
        newname=newFilename(p.stem,p.suffix)
        fullpath=subdir+"/"+newname
        if not IGNORE_ORIENTATION:
            skip=False
            tmp=""
            if orientation=="X" and w/h<1:
                tmp+="portrait"
                skip=True
            elif orientation=="Y" and w/h>1:
                tmp+="landscape"
                skip=True
            if skip:
                print("Skipped: "+fname+" ("+tmp+")")
                continue
        if orientation=="X":
            newx=int(resize_length)
            if not ROUND_UP:
                newy=round(h*resize_length/w)
            else:
                newy=math.ceil(h*resize_length/w)
        else:
            newy=int(resize_length)
            if not ROUND_UP:
                newx=round(w*resize_length/h)
            else:
                newx=math.ceil(w*resize_length/h)
        tmp=" >> "+str(newx)+"x"+str(newy)
        print("Resized: "+fname+tmp,end="")
        if CONVERT_TO_PNG and p.suffix.lower()!=".png":    
            print(" -> "+newname)
        else:
            print("")
        imResize=cv2.resize(img,(newx,newy),interpolation=inter_methods[method])
        cv2.imwrite(fullpath,imResize)
        pictures+=1                
      except:
        print("Unable to save: "+newname)
        continue
        
t2=datetime.now()

print("")
print("Pictures resized: "+str(pictures))
print("Time elapsed:     "+str(t2-t1))
