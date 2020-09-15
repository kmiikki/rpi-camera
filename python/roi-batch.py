#!/usr/bin/python3
# (C) Kim Miikki and Alp Karakoc 2020
  
import cv2
import csv
import os
import sys
from pathlib import Path
from datetime import datetime
import re

CONVERT_TO_PNG=False

# Global variables
fname=""
w=0
h=0
pictures=0
decimals=4
delimiter=";"
img_x0=0
img_y0=0
img_x1=0
img_y1=0
crop_x0=0
crop_x1=0
crop_y0=0
crop_y1=0

def validate_img_crop():
    # Validate image and crop values
    error_list=[]

    if img_x0<0:
        error_list.append("img_x0 < 0")
    elif img_x1<=img_x0:
        error_list.append("img_x1 <= img_x0")
    if img_y0<0:
        error_list.append("img_y0 < 0")
    elif img_y1<=img_y0:
        error_list.append("img_y1 <= img_y0")

    elif crop_x0<img_x0 or crop_x0>(img_x1):
        error_list.append("crop_x0 out of range")
    elif crop_x1<(img_x0+1) or crop_x1>(img_x1):
        error_list.append("crop_x1 out of range")
    elif crop_x0>=crop_x1:
        error_list.append("crop_x0 >= crop_x1")
        
    elif crop_y0<img_y0 or crop_y0>(img_y1-1):
        error_list.append("crop_y0 out of range")
    elif crop_y1<(img_y0+1) or crop_y1>(img_y1):
        error_list.append("crop_y1 out of range")
    elif crop_y0>=crop_y1:
        error_list.append("crop_y0 >= crop_y1")
    return error_list

def dict_to_int(key):
    return int(roi_dict[key])

def dict_to_float(key):
    return float(roi_dict[key])

# Template
# scale; coordinate name; value
# original;img_x1;4055
# original;crop_x1;1920 
# normalized;x1;1.0

def newFilename(oldname,ext):
  newname=re.sub("\s+", "_", oldname.strip())
  if CONVERT_TO_PNG:
      newname+=".png"
  else:
      newname+=ext
  return newname

print("ROI batch crop tool")
print("")

roilist=[]

roi_dict={
    "img_x0":0,
    "img_x1":0,
    "img_y0":0,
    "img_y1":0,
    "crop_x0":0,
    "crop_x1":0,
    "crop_y0":0,
    "crop_y1":0,
    "roi_x0":0,
    "roi_y0":0,
    "roi_w":0,
    "roi_h":0}

with open("roi.ini","r",newline="") as csvfile:
    csvreader=csv.reader(csvfile,delimiter=";")
    for row in csvreader:
        if row[1] in roi_dict:
            roi_dict[row[1]]=row[2]

# Copy roi_dict values to image and crop variables
img_x0=dict_to_int("img_x0")
img_x1=dict_to_int("img_x1")
img_y0=dict_to_int("img_y0")
img_y1=dict_to_int("img_y1")
crop_x0=dict_to_int("crop_x0")
crop_x1=dict_to_int("crop_x1")
crop_y0=dict_to_int("crop_y0")
crop_y1=dict_to_int("crop_y1")
roi_x0=dict_to_float("roi_x0")
roi_w=dict_to_float("roi_w")
roi_y0=dict_to_float("roi_y0")
roi_h=dict_to_float("roi_h")
            
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
    try:
      img = cv2.imread(str(path)+"/"+fname)
      # Get image dimensions
      w=img.shape[1]
      h=img.shape[0]
      if w==img_x1 and h==img_y1:
          same_dimensions=True
    except:
      print("No ROI cropping: "+fname)
      continue
    else:
      try:
        newname=newFilename(p.stem,p.suffix)
        fullpath=pngdir+"/"+newname
        if same_dimensions:
            # Crop image
            imCrop = img[int(crop_y0) : int(crop_y1), int(crop_x0):int(crop_x1)]
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

