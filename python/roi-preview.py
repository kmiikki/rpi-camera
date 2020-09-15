#!/usr/bin/python3
# (C) Kim Miikki 2020

#import cv2
#import numpy as np
import csv
from picamera import PiCamera
import os,sys,tty,termios
from rpi.camerainfo import *

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
crop_enabled=True

ESC=27
ENTER=13
SPACE=32

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
def getch():
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)
  return ch

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

zoom=(roi_x0,roi_y0,roi_w,roi_h)

print("Raspberry Pi Camera ROI Preview")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)

print("\nToggle between FOV and ROI: SPACE")
print("Exit program:  ESC")

camera=PiCamera(resolution=(camera_maxx,camera_maxy))
camera.zoom=zoom
camera.awb_mode = "auto"
camera.start_preview()

# Capture initial frame for ROI selection
while True:
  ch=getch()
  if ch==chr(SPACE):
    crop_enabled=not crop_enabled
    if crop_enabled:
        camera.zoom=zoom
    else:
        camera.zoom=(0,0,1,1)
  elif ch==chr(ESC):
    camera.stop_preview()
    camera.close()
    exit(0)
