#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 14 09:50:31 2022

@author: Kim Miikki
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
import cv2

extensions=['.png','.jpg','.bmp','.tif','.tiff','.dib','.jpeg','.jpe',',pbm','.pgm','.ppm','.sr','.ras']
exclude=['roi.ini']

stem=''
filename=''
minThreshold=1e-9
maxThreshold=255
outdir="crop"
defaultExt=".png"
xm=0
ym=0
threshold=0
decimals=4

isInput=False
isROI=False
preserveExt=False 
isX=False
isY=False
isThreshold=False
isBatch=True
isFixDim=False

def roix(value):
    return round(value/img_x1,decimals)

def roiy(value):
    return round(value/img_y1,decimals)

parser=argparse.ArgumentParser()
parser.add_argument('-i',type=str,help='input file name',required=False)
parser.add_argument('-o',action='store_true',help='preserve original file format')
parser.add_argument('-x',type=float,help='maximum horizontal marginal as integer',required=False)
parser.add_argument('-y',type=float,help='maximum vertical marginal as integer',required=False)
parser.add_argument('-t',type=float,help='threshold value as float, '+str(minThreshold)+' < t <= '+str(maxThreshold))
parser.add_argument('-f',action='store_true',help='fix odd dimensions by adjusting crop marginals')
args = parser.parse_args()

if args.i != None:
    isInput=True
    isROI=True
    isBatch=False
    filename=args.i
    stem=Path(filename).stem

if args.o:
    preserveExt=True

if args.x != None:
    isX=True    
    tmp=int(args.x)
    if tmp<0:
        tmp=0
    xm=tmp   

if args.y != None:
    isY=True    
    tmp=int(args.y)
    if tmp<0:
        tmp=0
    ym=tmp

if args.t != None:
    isThreshold=True    
    tmp=float(args.t)
    if tmp<minThreshold:
        tmp=minThreshold
    elif tmp>maxThreshold:
        tmp=maxThreshold
    threshold=tmp

if args.f:
    isFixDim=True

print('Autocrop 1.0, (c) Kim Miikki 2022')
print('')
print('Current directory:')
curdir=os.getcwd()
print(curdir)
print('')
path=Path(curdir)
adir=str(path)+'/'+outdir+'/'

try:
  if not os.path.exists(outdir):
    os.mkdir(outdir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# Generate a list of input files
files=[]
if isInput:
    files.append(filename)
else:
    for p in sorted(path.iterdir()):
        suffix=p.suffix.lower()
        if p.is_file() and suffix in extensions:
            fname=p.name
            if not fname in exclude:
                files.append(fname)

# Crop all images in the list
num=0
t1=datetime.now()                
if len(files)>0:
    print("Processing:")
for name in files:
    try:
        img=cv2.imread(name)
        h,w,ch=img.shape
    except:
        print(' - Unable to open: '+name)
        continue
    print(name+', size '+str(w)+'x'+str(h))
    
    x0=0
    x1=w-1
    y0=0
    y1=h-1
    
    lmean=img[0:h,0:1].mean(axis=(0,1)).mean()
    rmean=img[0:h,w-1:w].mean(axis=(0,1)).mean()
    tmean=img[0:1,0:w].mean(axis=(0,1)).mean()
    bmean=img[h-1:h,0:w].mean(axis=(0,1)).mean()
    
    # Search the left start
    while x0<w:
        mean=img[0:h,x0:x0+1].mean(axis=(0,1)).mean()
        if not isThreshold:
            if abs(mean-lmean)>0:
                break
        elif abs(mean-lmean)>=threshold:
            break
        x0+=1
    if isX:
        x0=x0-xm
    if x0<0:
        x0=0
        
    # Search the right end
    while x1>0:
        mean=img[0:h,x1:x1+1].mean(axis=(0,1)).mean()
        if not isThreshold:
            if abs(mean-rmean)>0:
                break
        elif abs(mean-rmean)>=threshold:
            break
        x1-=1
    x1+=1
    if isX:
        x1=x1+xm
    if x1>w-1:
        x1=w-1

    # Search the top start
    while y0<h:
        mean=img[y0:y0+1,0:w].mean(axis=(0,1)).mean()
        if not isThreshold:
            if abs(mean-tmean)>0:
                break
        elif abs(mean-tmean)>=threshold:
            break
        y0+=1
    if isY:
        y0=y0-ym
    if y0<0:
        y0=0
        
    # Search the bottom end
    while y1>0:
        mean=img[y1:y1+1,0:w].mean(axis=(0,1)).mean()
        if not isThreshold:
            if abs(mean-bmean)>0:
                break
        elif abs(mean-bmean)>=threshold:
            break
        y1-=1
    y1+=1
    if isY:
        y1=y1+ym
    if y1>h-1:
        y1=h-1

    # Fix image crop odd dimensions
    if isFixDim:
        if (x1-x0) % 2 == 1:
            if x1<w-2:
                x1+=1
            else:
                x1-=1
        if (y1-y0) % 2 == 1:
            if y1<h-2:
                y1+=1
            else:
                y1-=1
        
    if x0>=x1 or y0>=y1:
        print('Invalid crop coordinates: ',x0,x1,y0,y1)
    else:
        # Crop and save the image
        im_crop=img[y0:y1,x0:x1]
        if preserveExt:
            cv2.imwrite(adir+name,im_crop)
        else:
            tmp=adir
            stem=Path(name).stem
            tmp+=stem+".png"
            cv2.imwrite(tmp,im_crop)
        num+=1

if isROI:    
    print("")
    print("Saving roi.ini")
    # Build and save a ROI file
    img_x0=0
    img_y0=0
    img_x1=w
    img_y1=h
    crop_x0=x0
    crop_x1=x1
    crop_y0=y0
    crop_y1=y1
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
    cv2.imwrite("roi.jpg",img[y0:y1,x0:x1])

t2=datetime.now()

print("")
print("Files processed: "+str(num))
print("Time elapsed: "+str(t2-t1))
