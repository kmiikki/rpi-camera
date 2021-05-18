#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 12 08:34:19 2021

@author: Kim Miikki

Get pixels/mm or pixels/unit from a calibration image
"""

import argparse
import cv2
import os
import sys
import math
import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import MaxNLocator
from pathlib import Path
from scipy.signal import find_peaks
from rpi.inputs2 import *

inverse=False # Color mode
view=False
save=True
horizontal=True
fname=""
parent=""
stem=""
ch=0

# Peak fit parameters
distance=10
prominence=5

# Interval length threshold
dthres=0.25

# Scale and markers
imin=0.001
imax=1e6
unit="mm"
digits=5

# Round the calibration value with a specified number of digits
def getcal(value,digits):
    v=0
    dec=0
    d=math.log10(value)

    if d<=0:
        dec=digits+int(abs(d))
    elif d>0 and d<(digits-1):
        dec=digits+int((-d-1))
    elif d>=(digits-1):
        dec=0

    if dec>0:
        v=round(value,dec)
    else:
        v=round(value)
    return v

# Read and parse program arguments
parser=argparse.ArgumentParser()
parser.add_argument("file", type=Path, help="calibration image")
parser.add_argument("-d", action="store_true", help="do not create calibration files")
parser.add_argument("-p", action="store_true", help="plot calibration graphs on screen")
args = parser.parse_args()

if args.d:
    save=False

if args.p:
    view=True

if horizontal:
    isVertical=False

print("Calscale 1.0, (c) Kim Miikki 2021")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
if curdir!="/":
    curdir+="/"
print("")
print("Current directory:")
print(path)
print("")

if os.path.isfile(args.file):
    stem=args.file.stem
    fname=str(args.file.name)
    parent=str(args.file.parent)
else:
    print("File "+str(args.file)+" not found!")
    sys.exit(0)

if parent=="":
    parent=curdir

try:
    # Load a calibration image
    tmp=parent
    if tmp=="/":
        tmp=""
    img=cv2.imread(tmp+"/"+fname,cv2.IMREAD_UNCHANGED)
except:
    print("Unable to open "+fname+"!")
    sys.exit(0)

if img is None:
    print("Not a valid calibration image: "+fname)
    sys.exit(0)

if len(img.shape)==3:
    if img.shape[2]==3:
        ch=3
    h,w,ch=img.shape
elif len(img.shape)==2:
    ch=1
    h,w=img.shape

if not ch in [1,3]:
    print(fname+" does not have 1 or 3 color channels. Program is terminated.")
    sys.exit(0)

# Ask for unit and scale
while True:
    try:
        tmp=input("Enter unit (Default="+str(unit)+": <Enter>): ")
    except:
        print("Not a valid unit.")
        continue
    else:
        if tmp=="":
            print("Default unit selected: "+str(unit))
        else:
            unit=tmp
        break

# Ask for image orientation
if h>w:
    isVertical=True
horizontal=inputYesNo("horizontal mode","Horizontal calibration",not isVertical)

# Enter peak fit parameters
if horizontal:
    tmp=w
else:
    tmp=h

inverse=inputYesNo("inverse mode","Inverse color scale",False)
distance=inputValue("minimal peak distance:",1,round(tmp/2),distance,"","Distance is out of range!",True)
prominence=inputValue("minimal prominence of peaks:",0,255,prominence,"","Prominence is out of range!",False)
dthres=inputValue("interval length threshold:",0.01,1.0,dthres,"","Threshold is out of range!",False)

# Convert color image to grayscale
if ch==3:
    if horizontal:
        img=img.mean(axis=0)
    else:
        img=img.mean(axis=1)
    values=img.mean(axis=1)

if ch==1:
    if horizontal:
        values=img.mean(axis=0)
    else:
        values=img.mean(axis=1)

# Invert valleys to peaks
if inverse:
    ivals=values
else:
    ivals=values*-1

# Find peaks from a 1-D array
peaks,properties=find_peaks(ivals,prominence=prominence,distance=distance)

fig=plt.figure()
plt.plot(values,color="blue")
plt.plot(peaks,values[peaks],"x",color="red")
plt.xlim(0,len(values))
if horizontal:
    tmp="X"
else:
    tmp="Y"
tmp+=" coordinate"
plt.xlabel(tmp)
plt.ylabel("Grayscale mean value")
if save:
    # calca = Calibration color analysis
    plt.savefig(curdir+"calca-"+stem+".png", dpi=300)
if view:
    plt.show()
plt.close(fig)

if len(peaks)>1:
    
    # Calculate element-wise peak distances
    distances=[]
    left=peaks[0]
    i=0
    while i<len(peaks)-1:
        i+=1
        right=peaks[i]
        distances.append(right-left)
        left=right
    
    # Prepare distance data
    dmin=min(distances)
    dmax=max(distances)
    dists=np.unique(distances)
    ds=[]
    for element in dists:
        ds.append([element,distances.count(element)])
    dxs=np.array(ds)[:,0]
    dys=np.array(ds)[:,1]
    
    # Plot distances as a bar diagram
    fig=plt.figure()
    ax=fig.gca()
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    plt.bar(dxs,dys)
    plt.xlabel("Interval length")
    plt.ylabel("Count")
    if save:
        # calca = Calibration bar plot
        plt.savefig(curdir+"calbp-"+stem+".png", dpi=300)
    if view:
        plt.show()    
    plt.close(fig)
    
    # Calculate mean, median and sdev
    n=len(distances)
    dmean=np.mean(distances)
    dmedian=np.median(distances)
    dmin=np.min(distances)
    dmax=np.max(distances)
    dstd=np.std(distances)

    print("")
    print("Distance statistics (pixel values):")
    print("Peaks     : "+str(len(peaks)))
    print("Intervals : "+str(n))
    print("Mean      : "+str(dmean))
    print("Median    : "+str(dmedian))
    print("Min       : "+str(dmin))
    print("Max       : "+str(dmax))
    print("Sdev      : "+str(dstd))

    # Test if any distance is over threshold
    isValid=True
    for element in dxs:
        if abs((element-dmean)/dmean)>=dthres:
            if isValid:
                print("")
                print("Distance threshold: "+str(dthres))
                print("--------------------"+"-"*len(str(dthres)))
                isValid=False
            print("Exceeded at interval "+str(element)+": "+str((element-dmean)/dmean))
    if not isValid:
        print("")
        print("Adjust peak fit parameters to filter non-marker peaks or increase threshold.")
        sys.exit(0)

    # Create a log file
    now = datetime.now()
    dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")
    file=open(curdir+"cal-"+stem+".log","w")
    file.write("calscale.py log file"+"\n\n")
    file.write("Log created on "+dt_string+"\n\n")
    if (path!=""):
        file.write("Analysis directory: "+str(path)+"\n\n")
    else:
        file.write("File path: Not defined\n\n")
    file.write("Calibration parameters:\n")
    file.write("Image name    : "+fname+"\n")
    file.write("Image width   : "+str(w)+"\n")
    file.write("Image height  : "+str(h)+"\n")
    file.write("Color channels: "+str(ch)+"\n")
    file.write("Orientation   : ")
    if horizontal:
        file.write("horizontal")
    else:
        file.write("vertical")
    file.write("\n")
    file.write("Inverse mode  : ")
    if inverse:
        file.write("yes")
    else:
        file.write("no")
    file.write("\n\n")
    file.write("Minimal peak distance    : "+str(distance)+"\n")
    file.write("Minimal peak prominence  : "+str(prominence)+"\n")
    file.write("Interval length threshold: "+str(dthres)+"\n\n")
    
    # Results
    file.write("Distance statistics (pixel values):"+"\n")
    file.write("Peaks     : "+str(len(peaks))+"\n")
    file.write("Intervals : "+str(n)+"\n")
    file.write("Mean      : "+str(dmean)+"\n")
    file.write("Median    : "+str(dmedian)+"\n")
    file.write("Min       : "+str(dmin)+"\n")
    file.write("Max       : "+str(dmax)+"\n")
    file.write("Sdev      : "+str(dstd)+"\n\n")
    
    # Format the calibration value
    cal=getcal(dmean,digits)
    file.write("Calibration value: "+str(cal)+" pixels/"+unit+"\n")
    file.close()
       
    print("")
    print("Calibration value: "+str(cal)+" pixels/"+unit)

elif len(peaks)==1:
    print("Unable to calibrate. Only one peak found.")
elif len(peaks)==0:
    print("Unable to calibrate. Peaks not found.")