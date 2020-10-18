#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live video preview with blur detection
Method: Variance of the Laplacian

Created on Sun Oct 18 2020

@author: Kim Miikki
"""
import csv
import cv2

def variance_of_laplacian(image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
	return cv2.Laplacian(image, cv2.CV_64F).var()

CROP_PREVIEW=True
OVERLAY=True
CONSOLE_PRINT=False

count=0
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

TAB=9
ESC=27
SPACE=32
ALT_L=  0xffe9 & 0xff # 233
CTRL_L= 0xffe3 & 0xff # 227

W=800
H=600
old_W=0
old_H=0

# Colors: black, white, red, blue, green
colors=[(0,0,0),
        (255,255,255),
        (0,0,255),
        (255,0,0),
        (0,255,0)]
color=2

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
    "img_x1":W,
    "img_y0":0,
    "img_y1":H,
    "crop_x0":0,
    "crop_x1":W,
    "crop_y0":0,
    "crop_y1":H,
    "roi_x0":0,
    "roi_y0":0,
    "roi_w":0,
    "roi_h":0}

try:
    with open("roi.ini","r",newline="") as csvfile:
        csvreader=csv.reader(csvfile,delimiter=";")
        for row in csvreader:
            if row[1] in roi_dict:
                roi_dict[row[1]]=row[2]
except:
    print("ROI file not found")
    roi_dict["img_x1"]=W
    roi_dict["img_y1"]=H
    roi_dict["crop_x1"]=W
    roi_dict["crop_y1"]=H
    roi_dict["roi_w"]=1
    roi_dict["roi_h"]=1

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

print("Live ROI sharpness level monitor")
print("")

print("Control keys")
print("------------")
print("Toggle ROI/stretch mode: SPACE")
print("Toggle overlay on/off  : Alt_L")
print("Toggle console output  : Ctrl_L")
print("Text color:   TAB")
print("Exit program: ESC")
print("")
print("Sharpness:")


cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    
if not cap.isOpened():
    print("Cannot open camera")
    exit()

old_var=0
x0=int(crop_x0*W/img_x1)
y0=int(crop_y0*H/img_y1)
x1=int(crop_x1*W/img_x1)
y1=int(crop_y1*H/img_y1)
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    im_roi=frame[y0:y1,x0:x1]
    gray = cv2.cvtColor(im_roi, cv2.COLOR_BGR2GRAY)
    var = variance_of_laplacian(gray)
    v=int(var)
    if old_var!=v:
        old_var=v
    if CONSOLE_PRINT:
        print(v)
    # Display the resulting frame
    if CROP_PREVIEW:
        if OVERLAY:
            cv2.putText(im_roi, "{:d}".format(int(var)), (4, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, colors[color], 3)
        cv2.imshow('ROI sharpness preview',im_roi)
    else:
        imResize=cv2.resize(im_roi,(W,H),interpolation=cv2.INTER_NEAREST)
        if OVERLAY:
            cv2.putText(imResize, "{:d}".format(int(var)), (4, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, colors[color], 3)
        cv2.imshow('ROI sharpness preview',imResize)
    key=cv2.waitKey(1)
    if key==ESC:
        break
    elif key==TAB and OVERLAY:
        color+=1
        if color>len(colors)-1:
            color=0
    elif key==SPACE:
        CROP_PREVIEW=not CROP_PREVIEW
    elif key==ALT_L:
        OVERLAY=not OVERLAY
    elif key==CTRL_L:
        CONSOLE_PRINT=not CONSOLE_PRINT

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()