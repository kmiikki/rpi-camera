#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 11:56:23 2022

@author: Kim Miikki
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import cv2

extensions=['.png','.jpg','.bmp','.tif','.tiff','.dib','.jpeg','.jpe',',pbm','.pgm','.ppm','.sr','.ras']
exclude=['roi.ini']

stem=''
filename=''
outdir="crop"
defaultExt=".png"
c=0
r=0
l=0
t=0
b=0

reduce=True
isInput=False
preserveExt=False 
isBatch=True
isFixDim=False

parser=argparse.ArgumentParser()
parser.add_argument('-i',type=str,help='input file name',required=False)
parser.add_argument('-c',type=int,help='common crop marginal as integer',required=False)
parser.add_argument('-l',type=int,help='left crop width as integer',required=False)
parser.add_argument('-r',type=int,help='right crop width as integer',required=False)
parser.add_argument('-t',type=int,help='top crop height as integer',required=False)
parser.add_argument('-b',type=int,help='bottom crop height as integer',required=False)
parser.add_argument('-o',action='store_true',help='preserve original file format')
parser.add_argument('-f',action='store_true',help='fix odd dimensions by adjusting crop marginals')
args = parser.parse_args()

print('Cropmargins 1.0, (c) Kim Miikki 2022')
print('')
print('Current directory:')
curdir=os.getcwd()
print(curdir)
print('')
path=Path(curdir)
adir=str(path)+'/'+outdir+'/'

if args.i != None:
    isInput=True
    isBatch=False
    filename=args.i
    stem=Path(filename).stem

if args.c != None:
    c=int(abs(args.c))
    r=c
    l=c
    t=c
    b=c

if args.r != None:
    r=int(abs(args.r))

if args.l != None:
    l=int(abs(args.l))

if args.t != None:
    t=int(abs(args.t))

if args.b != None:
    b=int(abs(args.b))

if args.o:
    preserveExt=True

if args.f:
    isFixDim=True
  
if (l+r+t+b) == 0 and isFixDim == False:
    print("Crop margins not defined!")
    sys.exit(0)


try:
  if not os.path.exists(outdir):
    os.mkdir(outdir)
except OSError:
  print('Unable to create a directory or directories under following path:\n'+curdir)
  print('Program is terminated.')
  print('')
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
    print(name+', size '+str(w)+'x'+str(h),end='')
    
    x0=l
    x1=w-r-1
    y0=t
    y1=h-b-1
    
    dx=x1-x0+1
    dy=y1-y0+1

    if isFixDim:
        if dx % 2 == 1:
            if reduce:
                x1-=1
            else:
                x1+=1
        if dy % 2 == 1:
            if reduce:
                y0+=1
            else:
                y0-=1

    dx=x1-x0+1
    dy=y1-y0+1  
    
    error=False
    if x0>=x1 or y0>=y1:
        error=True
    if x0<0 or x1>=w:
        error=True
    if y0<0 or y1>=h:
        error=True
    
    if error:
        print('')
        print('Invalid crop coordinates: ',x0,x1,y0,y1)
    else:
        print(' -> '+str(dx)+'x'+str(dy))
        
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


t2=datetime.now()

print("")
print("Files processed: "+str(num))
print("Time elapsed: "+str(t2-t1))
