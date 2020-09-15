#!/usr/bin/python3
# (C) Kim Miikki and Alp Karakoc 2020

import cv2
from picamera import PiCamera
import os,sys,tty,termios
from rpi.inputs import *
from rpi.camerainfo import *
import csv

frame_name="roi-fov.png"
roi_name="roi-image.png"
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

def dict_to_int(key):
    return int(roi_dict[key])

def dict_to_float(key):
    return float(roi_dict[key])

print("Raspberry Pi Camera ROI Preview and Selection")
print("")

capture_image=inputYesNo("Capture initial picture from camera","Capture image mode","y")
if capture_image=="n":
    print("FOV file: "+frame_name+"\n")
else:
    if camera_detected==0:
        print("Raspberry Pi camera module not found!")
        exit(0)
    
    path = os.getcwd()
    print("Current directory:")
    print(path) 
    
    print("\nCapture initial frame: SPACE")
    print("Exit program:  ESC\n")
    
    camera=PiCamera(resolution=(camera_maxx,camera_maxy))
    camera.start_preview()
    camera.awb_mode = "auto"
    
    # Capture initial frame for ROI selection
    while True:
      ch=getch()
      if ch==chr(SPACE):
        camera.stop_preview()
        print("Capturing initial frame...")
        camera.capture(frame_name)
        camera.stop_preview()
        camera.close()
        break
      elif ch==chr(ESC):
        camera.stop_preview()
        camera.close()
        exit(0)

img = cv2.imread(frame_name)

# create a window
cv2.namedWindow('SELECT ROI AND CLICK ENTER',flags=cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO) # 1 definition window
# Cropped image - ROI
#cv2.namedWindow('image_roi', flags = cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO) # define a region of interest window
#cv2.imshow('image', img)
# whether to show crosschair
showCrosshair = True # whether to display the line of intersection
# if true, then from the center
# if false, then from the left-top
fromCenter = False # whether to start selecting from the center
# then let use to choose the ROI
rect = cv2.selectROI('SELECT ROI AND CLICK ENTER', img, showCrosshair, fromCenter)
# Also be a rect = cv2.selectROI ( 'image', img, False, False) # remember not to get rid of the above statement is set to
# rect = cv2.selectROI('image', img, showCrosshair=False, fromCenter=False)
# get the ROI
if rect==(0,0,0,0):
    print("ROI not selected!")
    exit(0)
(x, y, w, h) = rect 

# Get image dimensions
img_x1=img.shape[1]
img_y1=img.shape[0]

# Auto-correct if selection is out of range
if x<0:
    x=0
if y<0:
    y=0
if w>img_x1:
    w=img_x1
if h>img_y1:
    h=img_y1

items = (x, y, x+w, y+h, w, h) # (initial x, initial y, end x, end y, width, height)
# Crop image
imCrop = img[int(y) : int(y+h), int(x):int(x+w)]

# write image to local disk
cv2.imwrite(roi_name, imCrop)

# Get image dimensions and calculate ROI
crop_x0=items[0]
crop_x1=items[2]
crop_y0=items[1]
crop_y1=items[3]
roi_x0=roix(crop_x0)
roi_w=roix(crop_x1-crop_x0)
roi_y0=roiy(crop_y0)
roi_h=roiy(crop_y1-crop_y0)

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

print("Roi option: -roi "+
      str(roi_x0)+","+
      str(roi_y0)+","+
      str(roi_w)+","+
      str(roi_h))

# All these waitkeys are a hack to get the OpenCV window to close
cv2.waitKey(1)
cv2.destroyAllWindows()
for i in range (1,5):
    cv2.waitKey(1)
