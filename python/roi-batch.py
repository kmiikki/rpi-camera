#!/usr/bin/python3
# (C) Kim Miikki and Alp Karakoc 2020
  
import cv2
import csv
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import re
from rpi.roi import *
from rpi.inputs2 import *

CONVERT_TO_PNG=False

frame_name="roi-fov.jpg"
roi_name="roi-image.jpg"

exclude=[]
exclude.append(frame_name)
exclude.append(roi_name)
exclude.append("roi-fov.png")
exclude.append("roi-image.png")

# Global variables
fname=""
pictures=0

def newFilename(oldname,ext):
  newname=re.sub("\s+", "_", oldname.strip())
  if CONVERT_TO_PNG:
      newname+=".png"
  else:
      newname+=ext
  return newname

parser=argparse.ArgumentParser()
parser.add_argument("-i", action="store_true", help="interactive mode")
parser.add_argument("-p", action="store_true", help="save images in lossless PNG format")
args = parser.parse_args()

original_format=True
if args.p:
    original_format=False

print("ROI batch crop tool")
print("")
roi_result=validate_roi_values()
if roi_result:
    display_roi_status()
else:
    print("ROI file not found. Program is terminated.")
    exit(0)

if args.i:
    print("")
    original_format=inputYesNo("original format","Keep original format instead of PNG",
                               original_format)
print("")

errors=validate_img_crop()
if len(errors)>0:
    print("Invalid coordinates:")
    for item in errors:
        print(item)
    exit(0)

# Get current directory
curdir=os.getcwd()
pngdir=curdir+"/roi"
path=Path(curdir)
foldername=os.path.basename(curdir)

try:
  if not os.path.exists(pngdir):
    os.mkdir(pngdir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

t1=datetime.now()
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    same_dimensions=False
    fname=p.name
    if fname in exclude:
        continue
    try:
      img = cv2.imread(str(path)+"/"+fname)
      # Get image dimensions
      w=img.shape[1]
      h=img.shape[0]
      if w==roi_img_x1 and h==roi_img_y1:
          same_dimensions=True
    except:
      print("No ROI cropping: "+fname)
      continue
    else:
      try:
        if original_format:
            ext=p.suffix
        else:
            ext=".png"
        newname=newFilename(p.stem,ext)
        fullpath=pngdir+"/"+newname
        if same_dimensions:
            # Crop image
            imCrop = img[int(roi_crop_y0) : int(roi_crop_y1), int(roi_crop_x0):int(roi_crop_x1)]
            cv2.imwrite(fullpath,imCrop)
            pictures+=1
      except:
        print("Unable to save: "+newname)
        continue
      else:
        tmp=fname+" ("+str(w)+"x"+str(h)+"): "
        if same_dimensions:
            tmp+="-> "+newname
        else:
            tmp+="Different dimensions"
        print(tmp)
        
t2=datetime.now()

print("\nPictures converted: "+str(pictures))
print("Time elapsed:       "+str(t2-t1))

