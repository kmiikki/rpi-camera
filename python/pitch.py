#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 12 08:34:19 2021

@author: Kim Miikki
"""

import argparse
import csv
import cv2
import os
import sys
import math
import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import MaxNLocator
from pathlib import *
from scipy.signal import find_peaks
from rpi.inputs2 import *

batch=True
inverse=False # Color mode
view=False
save=True
pitchplot=False
logs=True
horizontal=True
fname=""
parent=""
stem=""
ch=0
linew=0.5
exclude_prefix=("ca","xca","yca")
results=[]

# Peak fit parameters
distance=25
prominence=10
minmax_distance=1000

# Interval length threshold
dthres=2.0

# Default unit and maximum digts of the calibration value
unit="mm"
digits=5

# Round the calibration value with a specified number of digits
def getpitch(value,digits):
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
parser.add_argument("file", type=Path, nargs="?", help="image")
parser.add_argument("-d", action="store_true", help="do not create color analysis files")
parser.add_argument("-n", action="store_true", help="do not create separate log files")
parser.add_argument("-i", action="store_true", help="generate a pitch plot")
parser.add_argument("-p", action="store_true", help="plot calibration graphs on screen")
args = parser.parse_args()

if args.d:
    save=False

if args.n:
    logs=False

if args.i:
    pitchplot=True

if args.p:
    view=True

if horizontal:
    isVertical=False

print("Pitch 1.0, (c) Kim Miikki 2021")

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

if args.file!=None:
    if os.path.isfile(args.file):
        stem=args.file.stem
        fname=str(args.file.name)
        parent=str(args.file.parent)
        batch=False
    else:
        print("File "+str(args.file)+" not found!")
        sys.exit(0)

if parent=="":
    parent=curdir
    
if batch:
    files=sorted(path.iterdir())
else:
    files=[PosixPath(fname)]
    
# Ask for unit and value
while True:
    try:
        tmp=input("Enter unit (Default="+str(unit)+": <Enter>): ")
        if tmp=="":
            print("Default unit selected: "+str(unit))
            break
        unit=tmp
        break
    except:
        print("Not a valid unit.")
        continue

while True:
    try:
        cal=input("Calibration value (pixels/"+unit+"): ")
        cal=float(cal)
        if cal<=0:
            print("Invalid value!")
            continue
        break
    except:
        print("Invalid value!")

# Ask for image orientation
horizontal=inputYesNo("horizontal mode","Horizontal analysis",not isVertical)

# Enter peak fit parameters
inverse=inputYesNo("inverse mode","Inverse color scale",False)
distance=inputValue("minimal peak distance:",1,minmax_distance,distance,"","Distance is out of range!",True)
prominence=inputValue("minimal prominence of peaks:",0,255,prominence,"","Prominence is out of range!",False)
dthres=inputValue("interval length threshold:",0.01,5.0,dthres,"","Threshold is out of range!",False)

c=0
for p in files:
    if Path(p).is_dir():
        continue
    suffix=p.suffix.lower()
    if p.is_file() and (suffix==".png" or suffix==".jpg"):
        fname=p.name
        if fname.startswith(exclude_prefix):
            print("Excluded : "+fname)
            continue
        print("Analyzing: "+fname)

        try:
            # Load a calibration image
            tmp=parent
            if tmp=="/":
                tmp=""
            img=cv2.imread(tmp+"/"+fname,cv2.IMREAD_UNCHANGED)
            stem=p.stem
        except:
            print("Unable to open "+fname+"!")
            continue
        
        if img is None:
            print("Not a valid image: "+fname)
            continue
        
        if len(img.shape)==3:
            if img.shape[2]==3:
                ch=3
            h,w,ch=img.shape
        elif len(img.shape)==2:
            ch=1
            h,w=img.shape
        if not ch in [1,3]:
            print(fname+" does not have 1 or 3 color channels.")
            continue
    
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
        plt.plot(values,color="blue",linewidth=linew)
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
            
            # Plot peak prominences
            pvalues=properties["prominences"]
            fig=plt.figure()
            ax=fig.gca()
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            plt.hist(properties["prominences"],rwidth=0.8)
            plt.xlabel("Peak prominence")
            plt.ylabel("Count")
            if save:
                # calpp = Calibration peak prominance plot
                plt.savefig(curdir+"calpp-"+stem+".png", dpi=300)
            if view:
                plt.show() 
            plt.close(fig)
            
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
            pitch=getpitch(dmean/cal,digits)
            pitch_median=getpitch(dmedian/cal,digits)

            results.append([stem,c+1,pitch,pitch_median,dmean,dmedian,dstd,len(peaks),n,dmin,dmax])        
        
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
                print("Adjust peak fit parameters or increase threshold.")
                continue
            
            if logs:
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
                file.write("Pitch mean  : "+str(pitch)+" "+unit+"\n")
                file.write("Pitch median: "+str(pitch_median)+" "+unit+"\n\n")
                file.close()
            
            if logs:
                # Create and save a list of peak data
                peakheader=["Peak","Prominence","Distance"]
                peakdata=[]
                i=0
                imax=len(peaks)
                for p in properties["prominences"]:
                    s=[peaks[i],p]
                    if i<imax-1:
                        s.append(distances[i])
                    peakdata.append(s)
                    i+=1
                # capdata = color analysis peakdata
                with open(curdir+"capdata-"+stem+".csv","w",newline="\n") as csvfile:
                    writer=csv.writer(csvfile,delimiter=',',quotechar='"')
                    writer.writerow(peakheader)
                    writer.writerows(peakdata)
               
            print("")
            print("Pitch mean  : "+str(pitch)+" "+unit)
            print("Pitch median: "+str(pitch_median)+" "+unit)
            print("")
            
            c+=1

        elif len(peaks)==1:
            print("Unable to calculate. Only one peak found.")
        elif len(peaks)==0:
            print("Unable to calculate. Peaks not found.")
if c==0:
    print("No pitch data")
else:

    # Save results to a file
    header=["Name","Image","Pitch mean("+unit+")","Pitch median("+unit+")","Mean","Median","Sdev","Peaks","N","Min","Max"]
    # Current directory
    cdir=str(PosixPath(curdir).resolve()).split("/")[-1]    
    with open(cdir+".csv","w",newline="\n") as csvfile:
        writer=csv.writer(csvfile,delimiter=',',quotechar='"')
        writer.writerow(header)
        writer.writerows(results)
    
    # Plot/save a pitch graph
    if (True in [save,view,pitchplot]) and c>1:
        ar=np.array(results).T
        xs=ar[1].astype(np.int)
        ys=ar[2].astype(np.float)
        
        fig=plt.figure()
        ax=fig.gca()
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        plt.xlim(xs[0],xs[-1])
        ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
        plt.plot(xs,ys)
        plt.xlabel(header[1])
        plt.ylabel(header[2])
        if save or pitchplot:
            # capi = Color analysis pitch plot
            plt.savefig(curdir+"capi-"+cdir+".png", dpi=300)
        if view:
            plt.show()    
        plt.close(fig)
