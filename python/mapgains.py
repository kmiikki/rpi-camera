#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 18:05:32 2021

@author: Kim Miikki

Mandatory files (input/output):
rgbmap-DT.pkl
rgbmap-b-gains-DT.csv
rgbmap-r-gains-DT.csv

Mandatory files (output):
rgbmap-cal-DT.txt
rgbmap-mdist-DT.png

where DT="YYYYMMDD-hhmm"
"""
import argparse
import os
import sys
import csv
import pickle
import cv2
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import picamera.array
from time import sleep
from rpi.camerainfo import *
from rpi.roi import *
from rpi.inputs2 import *

# Camera settings
exposure=20000 # µs
exp_mode="off"
awb_mode="off"
iso=100
width=320
height=240
pip=(0,0,width,height)

# R and B gains ranges
rs=[1,8]
r_step=1
bs=[1,8]
b_step=1
decimals=10
rgb_decimals=3

# Interactive values
red_gain_start=0.0001
red_gain_min=rs[0]
red_gain_max=rs[1]
red_step=1

blue_gain_start=0.0001
blue_gain_min=bs[0]
blue_gain_max=bs[1]
blue_step=1

rmap=[]
gmap=[]
bmap=[]
bwmap=[]
rlist=[]
blist=[]

pklfile=""
dt_part=""
curdirPrinted=False
previewImage=True
file_mode=False
interactive=True
all_files=True

results=[]

print("Mapgains - Map Raspberry Pi gamera gains and calibration")
print("(C) Kim Miikki 2021")
print("")

parser=argparse.ArgumentParser()
parser.add_argument("-f", type=Path, help="file mode: read rgbmap-YYYYMMDD-hhmm.pkl")
parser.add_argument("-a", action="store_true", help="auto, non-interactive mode")
parser.add_argument("-d", action="store_true", help="Disable image preview")
parser.add_argument("-n", action="store_true", help="Do not create all analysis files")
args = parser.parse_args()

if args.f:
    pklfile=args.f
    error=False
    if pklfile.is_dir():
        print(str(pklfile)+" is not a valid filename!")
        error=True
    elif not pklfile.exists():
        print(str(pklfile)+" does not exist!")
        error=True
    if error:
        sys.exit(1)
    if (pklfile.parent != pklfile.name) and not (str(pklfile.parent) == "."):
        os.chdir(pklfile.parent)
        print("Current directory set to: "+str(pklfile.parent))
        pklfile=pklfile.name
        curdirPrinted=True
    pklfile=str(pklfile)
    file_mode=True

if args.a:
    interactive=False

if args.d:
    previewImage=False

if args.n:
    all_files=False

if not file_mode:
    # ROI
    roi_result=validate_roi_values()
    if roi_result:
        display_roi_status()
        print("")

if not curdirPrinted:
    print("Current directory:")
    curdir=os.getcwd()
    print(curdir)

if file_mode:
    # Template: rgbmap-20211014-1639.pkl
    # dt:  4+2+2+1+4 + ext: 4 = 17
    dt_part=(pklfile[-17:])[:-4]
    
    # Read data
    with open(pklfile,"rb") as f:
        data=pickle.load(f)
        
    # Check data.shape and pklfile length
    error=False
    x=0
    y=0
    z=0
    error=False
    try:
        x,y,z=data.shape
        if x==0 or y==0:
            print("Incorrect table size: ("+str(x)+","+str(y)+")")
            error=True
        if z!=4:
            print("Incorrect number of layers (4 required): "+str(z))
            error=True
    except:
        print("Invalid data shape in the pickle file.")
        error=True
    if error:
        sys.exit(1)
    
    rmap=data[:,:,0]
    gmap=data[:,:,1]
    bmap=data[:,:,2]        
    bwmap=data[:,:,3]

    ## Read R and B gain ranges from files
    try:
        with open("rgbmap-r-gains-"+dt_part+".csv", "r") as f:
            reader = csv.reader(f)
            rlist=next(reader)
        rlist=list(np.array(rlist).astype(float))
    except:
        print("rgbmap-r-gains-"+dt_part+".csv not found!")
        sys.exit(1)
    try:
        with open("rgbmap-b-gains-"+dt_part+".csv", "r") as f:
            reader = csv.reader(f)
            blist=next(reader)
        blist=list(np.array(blist).astype(float))
    except:
        print("rgbmap-b-gains-"+dt_part+".csv not found!")
        sys.exit(1)

    # Check gain lists lengths
    error=False
    if y!=len(rlist):
        print("R gain list length mismatch with data rows")
        error=True
    if x!=len(blist):
        print("B gain list length mismatch with data columns")
        error=True
    if error:
        sys.exit(1)
elif interactive:
    print("")
    if camera_revision=="imx477":
        exp_min=250
    elif camera_revision=="imx219":
        exp_min=1
    exp_max=camera_max_exposure
    exp_default=exposure
    exposure=inputValue("exposure time",exp_min,exp_max,exp_default,"µs","Exposure is out of range!",True)
    print("")
    
       # Red gain range and step
    red_gain_min=inputValue("red gain min",red_gain_start,red_gain_max,red_gain_min,"","Gain out of range!",False)
    if red_gain_max<red_gain_min:
        red_gain_max=red_gain_min
    red_gain_max=inputValue("red gain max",red_gain_min,red_gain_max,red_gain_max,"","Gain out of range!",False)
    red_max_step=round(red_gain_max-red_gain_min,10)
    if red_max_step<red_step:
        red_step=red_max_step
    if red_max_step==0.0:
        print("Red gain min and max are equal. Red step auto adjusted to 1.0.")
        red_step=1.0
    else:
        red_step=inputValue("red gain step",red_gain_start,red_max_step,red_step,"","Step out of range!",False)
    print("")

    # Blue gain range and step
    blue_gain_min=inputValue("blue gain min",blue_gain_start,blue_gain_max,blue_gain_min,"","Gain out of range!",False)
    if blue_gain_max<blue_gain_min:
        blue_gain_max=blue_gain_min
    blue_gain_max=inputValue("blue gain max",blue_gain_min,blue_gain_max,blue_gain_max,"","Gain out of range!",False)
    blue_max_step=round(blue_gain_max-blue_gain_min,3)
    if blue_max_step<blue_step:
        blue_step=blue_max_step
    if blue_max_step==0.0:
        print("Blue gain min and max are equal. Blue step auto adjusted to 1.0.")
        blue_step=1.0
    else:
        blue_step=inputValue("blue gain step",blue_gain_start,blue_max_step,blue_step,"","Step out of range!",False)

    rs=[red_gain_min,red_gain_max]
    r_step=red_step
    bs=[blue_gain_min,blue_gain_max]
    b_step=blue_step

if not file_mode:
    # Create R and B gains lists
    rlist=list(np.linspace(rs[0],rs[1],round((rs[1]-rs[0])/r_step+1)))
    rlist=[round(num,decimals) for num in rlist]
    blist=list(np.linspace(bs[0],bs[1],round((bs[1]-bs[0])/b_step+1)))
    blist=[round(num,decimals) for num in blist]

if not file_mode:
    from picamera import PiCamera

    print("")
    print("Capture mode")
    print("")
    
    if not roi_result:
        roi_x0=0.5-width/(2*camera_maxx)
        roi_y0=0.5-height/(2*camera_maxy)
        roi_w=width/camera_maxx
        roi_h=height/camera_maxy
    zoom=(roi_x0,roi_y0,roi_w,roi_h)
        
    # Set camera options
    camera=PiCamera(resolution=(width,height))
    camera.iso=iso
    if previewImage:
        camera.start_preview(fullscreen=False,window=pip)
    # Wait for the automatic gain control to settle
    sleep(2)
    # Now fix the values
    camera.exposure_mode=exp_mode
    camera.awb_mode=awb_mode
    camera.shutter_speed=int(exposure)
    camera.zoom=zoom
    
    ct0=datetime.now()
    i=0
    print("rgain,bgain: red,green,blue")
    with picamera.array.PiRGBArray(camera) as output:
        for red in rlist:
            rl=[]
            gl=[]
            bl=[]
            bwl=[]
            for blue in blist:
                camera.awb_gains=(red,blue)
                camera.capture(output,"rgb")
                # output.array.shape: (240, 320, 3)
                rgb_means=np.array(output.array).mean(axis=(0,1))
                r_avg=round(rgb_means[0],rgb_decimals)
                g_avg=round(rgb_means[1],rgb_decimals)
                b_avg=round(rgb_means[2],rgb_decimals)
                bw_avg=round(rgb_means.mean(),rgb_decimals)
                i+=1
                print(str(red)+","+str(blue)+": "+str(r_avg)+","+str(g_avg)+","+str(b_avg))
                rl.append(r_avg)
                gl.append(g_avg)
                bl.append(b_avg)
                bwl.append(bw_avg)
                output.truncate(0)
            rmap.append(rl)
            gmap.append(gl)
            bmap.append(bl)
            bwmap.append(bwl)
    ct1=datetime.now()
    
# Generate stem name for results
now=datetime.now()
dt_part=now.strftime("%Y%m%d-%H%M")
pklname="rgbmap-"+dt_part+".pkl"

print("")
print("Analyzing data")
at0=datetime.now()
# Flatten RGB maps
isMin=False
rvals=np.array(rmap).ravel()
gvals=np.array(gmap).ravel()
bvals=np.array(bmap).ravel()
rg=abs(rvals-gvals)
rb=abs(rvals-bvals)
gb=abs(gvals-bvals)
mdist=(rg+rb+gb)/3
mmin=mdist.min()
mmax=mdist.max()
mmean=mdist.mean()
mvar=mdist.var()
mmedian=np.median(mdist)
# Get an array from the tuple
mpos=list(np.where(mdist==mmin))[0]
# Select first element from the array
if len(mpos>0):
    mpos=mpos[0]
    isMin=True
    rindex=mpos // len(blist)
    bindex=mpos % len(blist)
    red=rlist[rindex]
    blue=blist[bindex]
    
    if not file_mode:
        # Capture a sample picture
        camera.awb_gains=(red,blue)
        with picamera.array.PiRGBArray(camera) as output:
            camera.capture(output,"rgb")
            cv2.imwrite("rgbmap-cal-image-"+dt_part+".png",np.array(output.array))
            output.truncate(0)
else:
    print("Index of minimum distance not found!")
    print("mmin: "+str(mmin))

if not file_mode:
    camera.close()

# Save data in pickle format
data=np.dstack((rmap,gmap,bmap,bwmap))
with open(pklname,"wb") as f:
    pickle.dump(data,f)

# Write R and B gain ranges to files
with open("rgbmap-r-gains-"+dt_part+".csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(rlist)
with open("rgbmap-b-gains-"+dt_part+".csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(blist)

if all_files:
    # Write R, G, B channel data to files
    with open("rgbmap-r-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(rmap)
    with open("rgbmap-g-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(gmap)
    with open("rgbmap-b-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(bmap)
    with open("rgbmap-bw-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(bwmap)

    # Save R,G ,B channel data to gray scale image files
    fig=plt.figure()
    plt.title("Red mean response")
    plt.ylabel("Red gain")
    plt.xlabel("Blue gain")
    plt.imshow(rmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
    plt.gca().invert_yaxis()
    plt.savefig("rgbmap-r-im-"+dt_part+".png",dpi=300)
    plt.close(fig)
    
    fig=plt.figure()
    plt.title("Green mean response")
    plt.ylabel("Red gain")
    plt.xlabel("Blue gain")
    plt.imshow(gmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
    plt.gca().invert_yaxis()
    plt.savefig("rgbmap-g-im-"+dt_part+".png",dpi=300)
    plt.close(fig)
    
    fig=plt.figure()
    plt.title("Blue mean response")
    plt.ylabel("Red gain")
    plt.xlabel("Blue gain")
    plt.imshow(bmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
    plt.gca().invert_yaxis()
    plt.savefig("rgbmap-b-im-"+dt_part+".png",dpi=300)
    plt.close(fig)
    
    fig=plt.figure()
    plt.title("Gray mean response")
    plt.ylabel("Red gain")
    plt.xlabel("Blue gain")
    plt.imshow(bwmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
    plt.gca().invert_yaxis()
    plt.savefig("rgbmap-bw-im-"+dt_part+".png",dpi=300)
    plt.close(fig)

if isMin:
    ctext="["+str(rindex)+","+str(bindex)+"]"
    
    # Create a RGB mean distance plot
    fig=plt.figure()
    plt.title("RGB mean distance")
    plt.ylabel("Distance")
    plt.xlabel("Index number")
    plt.xlim(0,len(mdist)-1)
    plt.plot(mdist)
    plt.plot(mpos,mmin,marker="o",mec="r",mfc="red")
    plt.text(mpos,mmin,ctext)
    plt.savefig("rgbmap-mdist-"+dt_part+".png",dpi=300)
    plt.close(fig)
    
    if all_files:
        with open("rgbmap-mdist-"+dt_part+".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow(mdist)

at1=datetime.now()

if isMin:    
    results.append("")
    tmp="Mode: "
    if not file_mode:
        tmp+="capture and "
    tmp+="analyze"
    results.append(tmp)
    results.append("Time: "+str(now))
    results.append("")
    if not file_mode:
        results.append("Capture time: "+str(ct1-ct0))
    results.append("Analyze time: "+str(at1-at0))
    results.append("")
    results.append("Calibration")
    results.append("-----------")
    results.append("Red gain : "+str(rlist[rindex]))
    results.append("Blue gain: "+str(blist[bindex]))
    results.append("Minimal distance: "+str(round(mmin,rgb_decimals)))
    results.append("")
    results.append("Red and blue gains")
    results.append("-------------------")
    results.append("R gain min : "+str(red_gain_min))
    results.append("R gain max : "+str(red_gain_max))
    results.append("R gain step: "+str(r_step))
    results.append("")
    results.append("B gain min : "+str(blue_gain_min))
    results.append("B gain max : "+str(blue_gain_max))
    results.append("B gain step: "+str(b_step))    
    results.append("")
    results.append("Matrix   : "+str(len(rlist))+"x"+str(len(blist)))
    results.append("Position : "+ctext)
    results.append("Index    : "+str(mpos))
    results.append("")
    results.append("Distance distribution")
    results.append("---------------------")
    results.append("N     : "+str(len(mdist)))
    results.append("Min   : "+str(round(mmin,rgb_decimals)))
    results.append("Max   : "+str(round(mmax,rgb_decimals)))
    results.append("Mean  : "+str(round(mmean,rgb_decimals)))
    results.append("Median: "+str(round(mmedian,rgb_decimals)))
    results.append("Var   : "+str(round(mvar,rgb_decimals)))

    # Print calibration results
    for line in results:
        print(line)

    # Save calibration results
    with open ("rgbmap-cal-"+dt_part+".txt","w") as f:
        f.write("Mapgains Log File\n")
        for line in results:
            f.write(line+"\n")
