#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Sun Jan 22 14:38:06 2023

@author: Kim Miikki
'''

import argparse
import os
import cv2
import numpy as np
import sys
from datetime import datetime
from pathlib import Path

# Variable definitions
subdir = 'img'
wframe = 1920
hframe = 1080
colframe = 'e0e0e0'  # light gray color
opacity = 1
x0 = 0
y0 = 0

def valid_hex(hex_color: str) -> bool:
    isOk = True

    # Template:
    # abcdef
    # 123456
    tmp = hex_color.zfill(6)
    if len(tmp) != 6:
        isOk = False
    else:
        try:
            int(tmp, 16)
        except:
            isOk = False
    return isOk


def hex_to_bgr(hex_color: str) -> tuple:
    ''' Convert a hex color value to BGR format. '''
    color=hex_color.zfill(6)
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    return tuple(reversed(rgb))


print('Add a frame to images - (c) Kim Miikki 2023')
print('')

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print('Current directory:')
print(curdir)
print('')

parser = argparse.ArgumentParser()
parser.add_argument('-a', help='frame width', type=int, required=False)
parser.add_argument('-b', help='frame height', type=int, required=False)
parser.add_argument('-c', help='frame color (RGB hex value, format: abcdef)', type=str, required=False)
parser.add_argument('-x', help='image x0 coordinate', type=int, required=False)
parser.add_argument('-y', help='image y0 coordinate', type=int, required=False)
parser.add_argument('-o', help='image opacity (0-1)', type=float, required=False)
args = parser.parse_args()

if args.a!= None:
    wframe=int(args.a)
if args.b!= None:
    hframe=int(args.b)
if args.c!= None:
    try:
        tmp=args.c
        if valid_hex(tmp):
            colframe=tmp.zfill(6)
    except:
        print('Invalid color value, using default: '+hex(int(colframe,16))[2:].zfill(6).lower())

if args.x != None:
    x0=int(args.x)
if args.y != None:
    y0=int(args.y)
if args.o != None:
    value=float(args.o)
    if value<0:
        value=0
    elif value>1:
        value=1
    opacity=value

# Create a blank image with the desired frame size and color
frame = np.zeros((hframe, wframe, 3), dtype=np.uint8)
frame[:] = hex_to_bgr(colframe)

# Create a subdirectory for the output images
if not os.path.exists(subdir):
    os.mkdir(subdir)

# Iterate through all JPG and PNG files in the current directory
isFirst=True
t1=datetime.now()
i=0
for filename in os.listdir():
    if filename.endswith('.jpg') or filename.endswith('.png'):
        if isFirst:
            print('Processing:')
            isFirst=False
            
        
        # Load the image
        img = cv2.imread(filename)

        # Copy the blank image as canvas for the image
        canvas = frame.copy()

        # Add the image to canvas
        x1 = x0+img.shape[1]
        y1 = y0+img.shape[0]
        xclip = 0
        yclip = 0
        if x1 >= wframe:
            x1 = wframe
            xclip = x0+img.shape[1]-wframe
        if y1 >= hframe:
            y1 = hframe
            yclip = y0+img.shape[0]-hframe
        if xclip > 0 and yclip > 0:
            canvas[y0:y1, x0:x1] = img[:-yclip, :-xclip]
        elif xclip > 0:
            canvas[y0:y1, x0:x1] = img[:, :-xclip]
        elif yclip > 0:
            canvas[y0:y1, x0:x1] = img[:-yclip, :]
        else:
            canvas[y0:y1, x0:x1] = img
            
        # Add the image to the frame using the mask
        img = cv2.addWeighted(canvas, opacity, frame, 1-opacity, 0)

        # Save the output image to the 'img' subdirectory
        tmp=subdir+'/'+Path(filename).stem+'.png'
        print(tmp)
        cv2.imwrite(tmp, img)
        i+=1
t2=datetime.now()

print('\nFiles processed: '+str(i))
print('Time elapsed: '+str(t2-t1))