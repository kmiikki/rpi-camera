#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  7 16:07:32 2023

@author: Kim Miikki

roixy.py
"""
import argparse
import csv
import cv2
import numpy as np
import os
import sys
from pathlib import Path

unit='°C'
sample='thermogram.txt'

cmaps={
       'bone':      1,
       'jet':       2,
       'rainbow':   4, # inverse
       'cool':      8,
       'hot':       11,
       'inferno':   14,
       'plasma':    15,
       'twilight':  18,
       'turbo':     20,
       'deepgreen': 21
       }

# Default colormap
cmap=cmaps['jet']

is_thermogram=False
is_data=False

def matrix_to_image(matrix, cmap):
    is_invert=False
    if cmap in [cmaps['rainbow']]:
        is_invert=True 
    
    if is_invert:
        matrix*=-1

    mat = cv2.normalize(matrix, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    colormap = cv2.applyColorMap(mat, cmap)

    if is_invert:
        matrix*=-1
        mat=255-mat
        
    return colormap, mat

def generate_thermogram():
    # Define the size of the matrix
    width,height = 1024, 768
    
    # Define the center of the hot spot and its radius
    center_x, center_y = width // 2, height // 2
    radius = 200
    
    # Define the temperature range for the hot spot
    hot_temp = 100.0
    
    # Generate a grid of distances from the center
    x, y = np.meshgrid(np.arange(width), np.arange(height))
    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    # Initialize the temperature matrix with background noise
    background_temp = np.random.normal(loc=25.0, scale=2.5, size=(height, width))
    temperature = background_temp.copy()
    
    # Apply the hot spot temperature within the specified radius
    temperature[dist < radius] = hot_temp - (hot_temp - background_temp[dist < radius]) * (dist[dist < radius] / radius)
     
    return temperature


print("XY matrix ROI selection program - (C) Kim Miikki 2023")

# Get current directory
curdir = os.getcwd()
path = Path(curdir)
print('')
print('Current directory:')
print(curdir)
print('')
if curdir != '/':
    curdir += '/'

parser = argparse.ArgumentParser()
parser.add_argument('-n', help='XY data file in CSV format (mandatory unless -g selected)', type=str, required=False)
parser.add_argument('-cmap', help='select colormab by name', type=str, required=False)
parser.add_argument('-u', help='unit string (- = none)', type=str, required=False)
parser.add_argument('-g', action='store_true', help='generate a test thermogram', required=False)
parser.add_argument('-l', action='store_true', help='list colormaps', required=False)
args = parser.parse_args()

if args.cmap != None:
    tmp=args.cmap
    try:
        cmap=cmaps[tmp]
    except KeyError:
        pass 

if args.l:
    print('Colormaps:')
    for key in list(cmaps.keys()):
        print(key)
    sys.exit(0) 

if args.u != None:
    tmp=args.u
    if tmp=='-':
        unit=''
    else:
        unit=tmp
    
if args.g:
    # Generate a random thermogram
    data = generate_thermogram()
    is_thermogram=True

if args.n != None:
    if is_thermogram:
        print('Thermogram generation disabled when XY file selected.')
        is_thermogram=False
    tmp=args.n
    try:
        data = np.genfromtxt(curdir+tmp, delimiter=',')
        is_data=True
    except:
        print('Unable to open the data file!')
        print('')
if (not is_thermogram) and (not is_data):
    print('No data file selected. Program is terminated.')
    sys.exit(0)

# Convert the thermogram to a color image
image, image_data = matrix_to_image(data,cmap)


# Print some statistics about the matrix
print('Matrix statistics:')
rows,cols=data.shape
print('')
print(f'N      : {rows*cols}')
print(f'Rows   : {rows}')
print(f'Columns: {cols}')
print('')
print(f'Minimum: {np.min(data):6.2f} '+unit)
print(f'Maximum: {np.max(data):6.2f} '+unit)
print(f'Mean   : {np.mean(data):6.2f} '+unit)
print(f'Median : {np.median(data):6.2f} '+unit)
print(f'Sdev   : {np.std(data):6.2f} '+unit)

# Save sample thermogram data
if is_thermogram:
    np.savetxt(curdir+sample, data, delimiter=',')

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
rect = cv2.selectROI('SELECT ROI AND CLICK ENTER', image, showCrosshair, fromCenter)

# Also be a rect = cv2.selectROI ( 'image', img, False, False) # remember not to get rid of the above statement is set to
# rect = cv2.selectROI('image', img, showCrosshair=False, fromCenter=False)
# get the ROI

cv2.waitKey(1)
cv2.destroyAllWindows()
for i in range (1,5):
    cv2.waitKey(1)

if rect==(0,0,0,0):
    print('')
    print("ROI not selected!")
    sys.exit(0)
(x0, y0, w, h) = rect

# Crop image
roi = image[y0 : y0+h, x0:x0+w]
    
roi_h,roi_w,ch=roi.shape
if roi_h==0 and roi_w==0:
    print('')
    print('Nothing selected.')
    sys.exit(0)

'''
roixy.ini structure
-------------------
width,n1
height,n2
roi_x0
roi_y0
roi_w
roi_h
'''
roilist=[]
roilist.append(['width',cols])
roilist.append(['height',rows])
roilist.append(['roi_x0',x0])
roilist.append(['roi_y0',y0])
roilist.append(['roi_w',roi_w])
roilist.append(['roi_h',roi_h])


# Create a roixy.ini file
print('')
print('ROI selection')
print('-------------')
with open("roixy.ini","w",newline="") as csvfile:
    csvwriter=csv.writer(csvfile,delimiter=',')
    for s in roilist:
        csvwriter.writerow(s)
        print(s[0].ljust(6)+': '+str(s[1]).rjust(5))

# Write colormap files
fov_name='roixy-fov.png'
roi_name='roixy-crop.png'
cv2.imwrite(curdir+fov_name, image)
cv2.imwrite(curdir+roi_name, roi)




