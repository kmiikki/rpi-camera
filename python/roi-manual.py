#!/usr/bin/python3
# (C) Kim Miikki 2020

import os,sys
import cv2
from rpi.inputs import *
import csv

# Global variables
MAX_PIXELS=10000
default_w=1920
default_h=1080
load_pic=False
absolute_mode=False
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

def roix(value):
    return round(value/img_x1,decimals)

def roiy(value):
    return round(value/img_y1,decimals)

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

print("ROI manual selection")

arguments=len(sys.argv)
if arguments==1:
    print("Manual dimensions mode selected. Alternative usage: roi-manual.py 'image file'")
elif arguments==2:
    fname=sys.argv[1]
    load_pic=True
elif arguments>2:
    print("Too many arguments!")
    exit(1)

path = os.getcwd()
if load_pic:
    try:
        img = cv2.imread(str(path)+"/"+fname)
        # Get image dimensions
        w=img.shape[1]
        h=img.shape[0]
    except:
      print("Unable to get image dimensions: "+fname)
      exit(1)
else:
    # Get custom dimensions
    print("")
    w=inputValue("width",1,MAX_PIXELS,default_w,"","Width out of range!")
    h=inputValue("height",1,MAX_PIXELS,default_h,"","Height out of range!")

img_x1=w
img_y1=h

print("")
print("Current directory:")
print(path)
print("")

print("Region of Interest")
print("------------------")
crop_x0=inputValue("X0",0,w-1,0,"","X0 out of range!")
crop_y0=inputValue("Y0",0,h-1,0,"","Y0 out of range!")
if absolute_mode:
    crop_x1=inputValue("X1",crop_x0+1,w,w,"","X1 out of range!")
    crop_y1=inputValue("Y1",crop_y0+1,h,h,"","Y1 out of range!")
    crop_w=crop_x1-crop_x0
    crop_h=crop_y1-crop_y0
else:    
    max_w=w-crop_x0
    max_h=h-crop_y0
    crop_w=inputValue("Width",1,max_w,max_w,"","Width out of range!")
    crop_h=inputValue("Height",1,max_h,max_h,"","Height out of range!")
    crop_x1=crop_x0+crop_w
    crop_y1=crop_y0+crop_h

roi_x0=roix(crop_x0)
roi_w=roix(crop_w)
roi_y0=roiy(crop_y0)
roi_h=roiy(crop_h)

errors=validate_img_crop()
if len(errors)>0:
    print("Invalid coordinates:")
    for item in errors:
        print(item)
    exit(0)

roilist=[]

roilist.append(["scale","coordinate name","value"])
roilist.append(["original","img_x0",img_x0])
roilist.append(["original","img_x1",img_x1])
roilist.append(["original","img_y0",img_y0])
roilist.append(["original","img_y1",img_y1])
roilist.append(["original","crop_x0",crop_x0])
roilist.append(["original","crop_x1",crop_x1])
roilist.append(["original","crop_y0",crop_y0])
roilist.append(["original","crop_y1",crop_y1])
roilist.append(["normalized","roi_x0",roi_x0])
roilist.append(["normalized","roi_y0",roi_y0])
roilist.append(["normalized","roi_w",roi_w])
roilist.append(["normalized","roi_h",roi_h])

with open("roi.ini","w",newline="") as csvfile:
    csvwriter=csv.writer(csvfile,delimiter=";")
    for s in roilist:
        csvwriter.writerow(s)

print("")
print("Roi option: -roi "+
      str(roi_x0)+","+
      str(roi_y0)+","+
      str(roi_w)+","+
      str(roi_h))
