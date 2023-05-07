#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 09:49:54 2023

@author: Kim Miikki

pip.csv format:
pip1,x0_1,y0_1,alpha1
pip2,x0_2,y0_2,alpha2
pip3,x0_3,y0_3,alpha3

str,int,int,float

Use PNG when alpha<1
"""

import cv2
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

csvname='pip.csv'
pipname='pip'
outdir='img'

# Supported image formats:
exts=['.png','.jpg']
primary='.png'
secondary=list(set(exts)-set([primary]))[0]
isHeader=False

def sort_csv(file_path,header):
    with open(file_path) as file:
        reader = csv.reader(file)
        if header:
            header = next(reader) # skip header
        data = []
        for row in reader:
            if len(row) >= 3:
                data.append((row[0], int(row[1]), int(row[2]),float(row[3])))
        sorted_data = sorted(data, key=lambda x: x[0])
    return sorted_data

def first_digit_pos(s):
    for i, c in enumerate(s):
        if c.isdigit():
            return i
    return -1

def swap(a,b):
    return b,a

print("Add pip(s) to frame")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print('')
if curdir!='/':
    curdir+='/'

try:
    if not os.path.exists(outdir):
        os.mkdir(outdir)
except OSError:
    print("Unable to create a directory or directories under following path:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)
    
dirs = []
dirs = []
for dir in sorted(os.listdir()):
    if os.path.isdir(dir) and dir.startswith(pipname) and dir[len(pipname):].isdigit() and os.access(dir, os.R_OK):
        dirs.append(dir)
            
pipxy=sort_csv(csvname,isHeader)

# Read all frames from current directory and add pips on it
pris=[]
secs=[]
prinums=[]
secnums=[]
for name in sorted(path.iterdir()):
    if name.is_file() and name.suffix in exts:
        tmp=name.stem
        pos=first_digit_pos(tmp)
        if pos>=0:
            num=tmp[pos:]
            if num.isdigit():
                if name.suffix==primary:
                    pris.append(tmp+primary)
                    prinums.append(num)
                elif name.suffix==secondary:
                    secs.append(tmp+secondary)
                    secnums.append(num)
countpris=len(pris)
countsecs=len(secs)

if countpris>=countsecs:
    frames=pris
    nums=prinums
else:
    primary,secondary=swap(primary,secondary)
    countpris,countsecs=swap(countpris,countsecs)
    frames=secs
    nums=secnums

print(primary[-3:].upper()+' frames found: '+str(countpris))

success=0
fails=0
i=0

t1=datetime.now()
for frame in frames:
    if i==0:
        print('\nProcessing:')
    n=i
    i+=1
    print(frame[:-4]+': ',end='')
    
    # Read the frame as a base image
    isOk=True
    try:
        img=cv2.imread(frame)
        height,width,ch=img.shape
    except:
        fails+=1
        isOk=False
        print('skip',end='')
    
    if isOk:
        # Add pips on the frame
        for d in dirs:
            fstem=d+'/'+nums[n]
            print(d+':',end='')
            file1=fstem+primary
            file2=fstem+secondary
            
            # Try to open file1
            isPIP=False
            j=1
            idx=0
            for f in [file1,file2]:
                if not isPIP and os.path.isfile(f):
                    try:
                        pip=cv2.imread(f)
                        im_height,im_width,im_ch=img.shape
                        idx=j
                        isPIP=True
                        print(str(j),end='')
                    except:
                        pass
                j+=1
            if isPIP:
                # Copy the frame as canvas for the image
                canvas = img.copy()
                
                # Get (x0,y0) and alpha for the pip
                x0,y0,alpha=pipxy[idx][1:]
                alpha=float(alpha)
                
                # Add the image to canvas
                x1 = x0+im_width
                y1 = y0+im_height
                xclip = 0
                yclip = 0
                if x1 >= width:
                    x1 = width
                    xclip = x0+im_width-width
                if y1 >= height:
                    y1 = height
                    yclip = y0+im_height-height
                if xclip > 0 and yclip > 0:
                    canvas[y0:y1, x0:x1] = img[:-yclip, :-xclip]
                elif xclip > 0:
                    canvas[y0:y1, x0:x1] = img[:, :-xclip]
                elif yclip > 0:
                    canvas[y0:y1, x0:x1] = img[:-yclip, :]
                else:
                    canvas[y0:y1, x0:x1] = img
                    
                # Add the image to the frame using the mask
                img = cv2.addWeighted(canvas, alpha, img, 1-alpha, 0)
            else:
                print('-',end='')
            print(' ',end='')
        cv2.imwrite(outdir+'/'+nums[n]+'.png', img)
        success+=1
    print('')
    
t2=datetime.now()

print('\nFiles processed: '+str(success))
print('Time elapsed: '+str(t2-t1))    
 