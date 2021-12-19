#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 16 08:42:47 2021

@author: Kim Miikki
@name:   roi-aselect.py

"""

import argparse
import csv
import cv2
import os
import sys
import numpy as np
from pathlib import Path

s_default=20
th_default=5.0
threshold=-1
th_under=False
th_over=False
img_sel=[]

cross_col=(255,0,0)
decimals=4
roi=[-1,-1,-1,-1]
isROI=False

def roix(value):
    return round(value/img_x1,decimals)

def roiy(value):
    return round(value/img_y1,decimals)

def getMarkerCoordinates(w,h,x,y,s):
    top=int(y-s/2)
    bottom=top+s
    left=int(x-s/2)
    right=left+s
    if top<0:
        top=0
    if bottom>h-1:
        bottom=h-1
    if left<0:
        left=0
    if right>w-1:
        right=w-1
    return(left,right,top,bottom)

def getThresholdCoordinate(direction,mean,x,y,s):
    global img
    delta_x=0
    delta_y=0
    sadjust=int(s/2)
    if direction==0:
        # Up
        sx=x-sadjust
        ex=x+sadjust
        sy=y-sadjust
        ey=y-sadjust+1
        delta_y=-1
    elif direction==1:
        # Right
        sx=x+sadjust-1
        ex=x+sadjust
        sy=y-sadjust
        ey=y+sadjust
        delta_x=1
    elif direction==2:
        # Down
        sx=x-sadjust
        ex=x+sadjust
        sy=y+sadjust-1
        ey=y+sadjust
        delta_y=1
    elif direction==3:
        # Left
        sx=x-sadjust
        ex=x-sadjust+1
        sy=y-sadjust
        ey=y+sadjust
        delta_x=-1

    # Fix values outside ranges
    if sx<0:
        sx=0
    elif sx>w-1:
        sx=w-1
    if ex<0:
        ex=0
    elif ex>w-1:
        ex=w-1
    if sy<0:
        sy=0
    elif sy>h-1:
        sy=h-1
    if ey<0:
        ey=0
    elif ey>h-1:
        ey=h-1

    # Fix slicing values
    if ex<=sx:
        ex=sx+1
    if ey<=sy:
        ey=sy+1

    while True:    
        line=img[sy:ey,sx:ex]
        mean_line=line.mean(axis=(0,1)).mean()
        if th_under:
            if mean_line<mean-threshold:
                break
        if th_over:
            if mean_line>mean+threshold:
                break
        sx+=delta_x
        ex+=delta_x
        sy+=delta_y
        ey+=delta_y
        if (sx<0 or sx>w-1) or (ex<0 or ex>w-1):
            break
        if (sy<0 or sy>h-1) or (ey<0 or ey>h-1):
            break
    if sy<0:
        sy=0
    elif sy>h-1:
        sy=h-1
    if sx<0:
        sx=0
    elif sx>w-1:
        sx=w-1
    if direction==0 or direction==2:
        return sy
    else:
        return sx       

def click_event(event, x, y, flags, param):
    global img_clone,img_clone2
    global roi,isROI
    if x<0 or x>=w:
        return
    if y<0 or y>=h:
        return
    if event == cv2.EVENT_LBUTTONDOWN:
        (selx1,selx2,sely1,sely2)=getMarkerCoordinates(w,h,x,y,s)
        if sely1==sely2 or selx1==selx2:
            return
        img_sel=img[sely1:sely2,selx1:selx2]
        mean_bgr=img_sel.mean(axis=(0,1))
        neg_bgr=tuple(255-mean_bgr)
        m=mean_bgr.mean()
        ysel1=getThresholdCoordinate(0,m,x,y,s)
        ysel2=getThresholdCoordinate(2,m,x,y,s)
        xsel1=getThresholdCoordinate(3,m,x,y,s)
        xsel2=getThresholdCoordinate(1,m,x,y,s)
        print("("+str(x)+","+str(y)+")")
        
        # Draw selection area
        blk=np.zeros(img.shape,np.uint8)
        cv2.rectangle(blk, (xsel1,ysel1), (xsel2,ysel2), neg_bgr,-1)
        img_clone=cv2.addWeighted(img,1,blk,0.25,1)
        
        # Draw selection cross
        sadjust=int(s/2)
        blk=np.zeros(img.shape,np.uint8)
        cv2.rectangle(blk,(xsel1,y-sadjust),(xsel2,y+sadjust),cross_col,-1)
        cv2.rectangle(blk,(x-sadjust,ysel1),(x+sadjust,ysel2),cross_col,-1)
        img_clone2=cv2.addWeighted(img_clone,1,blk,0.25,1)
        
        cv2.imshow('Select ROI',img_clone2)
        roi=[xsel1,ysel1,xsel2,ysel2]
        isROI=True
    elif event == cv2.EVENT_RBUTTONDOWN:
        # Clear all markers 
        img_clone=img.copy()
        cv2.imshow('Select ROI', img_clone)
        roi=[-1,-1,-1,-1]
        isROI=False

parser=argparse.ArgumentParser()
parser.add_argument("-f","--file",type=Path, help="specify the image name",required=True)
parser.add_argument('-t',type=float,help="threshold (default: "+str(th_default)+") as float ",required=False)
parser.add_argument('-s',type=float,help="selection size s x s (default: "+str(s_default)+") as integer ",required=False)
parser.add_argument("-u", action="store_true", help="enable under threshold",required=False)
parser.add_argument("-o", action="store_true", help="enable over threshold",required=False)
args = parser.parse_args()

if args.file:
    stem=args.file.stem
    fname=str(args.file.name)
    filename=str(args.file)
if not os.path.isfile(filename):
    print("File "+str(filename)+" not found!")
    sys.exit(0)

if args.t != None:
    threshold=float(args.t)
    if threshold<0 or threshold>255:
        threshold=th_default
else:
    threshold=th_default

if args.s != None:
    s=int(args.s)
else:
    s=s_default
    
if args.u==True:
    th_under=True
if args.o==True:
    th_over=True
if not True in [th_under,th_over]:
    th_under=True
    th_over=True

stem+="-"

print("Auto ROI selection")
print("(C) Kim Miikki 2021")
print("")
print("Image file: "+filename)
print("")

print("Current directory:")
curdir=os.getcwd()
path=Path(curdir)
print(curdir)

print("")
print("1. Select ROI by pressing the mouse left button")
print("2. Remove ROI by pressing the mouse right button")
print("3. Press any key to accept the selection")

img = cv2.imread(filename)
if len(img.shape)==2:
    h,w=img.shape
elif len(img.shape)==3:
    h,w,ch=img.shape
img_clone=img.copy()
img_clone2=img.copy()

cv2.namedWindow("Select ROI", cv2.WINDOW_NORMAL)
cv2.imshow("Select ROI",img_clone)
cv2.setMouseCallback("Select ROI", click_event)
cv2.waitKey(0)

print("")

if isROI:    
    print("Saving roi.ini")
    # Build and save a ROI file
    img_x0=0
    img_y0=0
    img_x1=w
    img_y1=h
    crop_x0=roi[0]
    crop_x1=roi[2]
    crop_y0=roi[1]
    crop_y1=roi[3]
    roi_x0=roix(crop_x0)
    roi_w=roix(crop_x1-crop_x0+1)
    roi_y0=roiy(crop_y0)
    roi_h=roiy(crop_y1-crop_y0+1)
    
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
    
    # Save ROI images
    print("Saving ROI image files")
    cv2.imwrite("roi-patch.jpg",img_clone)
    cv2.imwrite("roi-selection.jpg",img_clone2)
    cv2.imwrite("roi.jpg",img[crop_y0:crop_y1,crop_x0:crop_x1])
        
else:
    print("ROI not selected.")
    
# All these waitkeys are a hack to get the OpenCV window to close
cv2.waitKey(1)
cv2.destroyAllWindows()
for i in range (1,5):
    cv2.waitKey(1)

