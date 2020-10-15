#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live video preview with blur detection
Method: Variance of the Laplacian

Created on Thu Oct 15 18:35:02 2020

@author: Kim Miikki
"""
import sys
import numpy as np
import cv2

def variance_of_laplacian(image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
	return cv2.Laplacian(image, cv2.CV_64F).var()

ESC=27
SPACE=32

# Colors: black, white, red, blue, green
colors=[(0,0,0),
        (255,255,255),
        (0,0,255),
        (255,0,0),
        (0,255,0)]
color=2

Enable_HD=False
arguments=len(sys.argv)

print("Live sharpness level monitor")
print("")
if arguments==1:
    print("Default capture mode enabled.")
    print("Alternative HD mode: -HD")
if arguments==2:
    if sys.argv[1].upper()=="-HD":
        print("HD capture mode enabled")
        Enable_HD=True
print("")
print("Text color:   SPACE")
print("Exit program: ESC")


cap = cv2.VideoCapture(0)
if Enable_HD:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    var = variance_of_laplacian(gray)
    cv2.putText(frame, "Sharpness: {:d}".format(int(var)), (10, 60),
		cv2.FONT_HERSHEY_SIMPLEX, 2, colors[color], 3)
    # Display the resulting frame
    cv2.imshow('Camera live preview',frame)
    key=cv2.waitKey(1)
    if key==ESC:
        break
    elif key==SPACE:
        color+=1
        if color>len(colors)-1:
            color=0

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()