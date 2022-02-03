#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  2 00:10:21 2022

@author: Kim Miikki
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks, peak_widths
from sklearn.metrics import auc

rgb_in="" # rgbxy csv file
adir=""

distance=1000
prominence=2
width=10
rel_height=1

findPeaks=False
findValleys=False
showGraphs=False

parser=argparse.ArgumentParser()
parser.add_argument("RGB")
parser.add_argument("-p", action="store_true", help="find peaks")
parser.add_argument("-v", action="store_true", help="find valleys")
parser.add_argument('-d',type=int,help="minimal horizontal distance as integer",required=False)
parser.add_argument('-pr',type=float,help="required prominence as float",required=False)
parser.add_argument('-w',type=int,help="minimal peak width as integer",required=False)
parser.add_argument('-r',type=float,help="relative height as float",required=False)
parser.add_argument("-s", action="store_true", help="show graphs on screen")
args = parser.parse_args()

if args.p:
    findPeaks=True

if args.v:
    findValleys=True

if not True in [findPeaks,findValleys]:
    findPeaks=True
    findValleys=True
    
if args.d != None:
    tmp=int(args.d)
    if tmp>0:
        distance=tmp

if args.pr != None:
    tmp=float(args.p)
    if tmp>0:
        prominence=tmp
        
if args.w != None:
    tmp=float(args.w)
    if tmp>0:
        width=tmp

if args.r != None:
    tmp=float(args.r)
    if tmp>0 or tmp>1:
        rel_height=tmp
        
if args.s:
    showGraphs=True

fname=args.RGB
stem=Path(args.RGB).stem
rgb_in=fname

print("RGBXY Peak Find Utility 1.0, (c) Kim Miikki 2022")
print("")
print("Current directory:")
curdir=os.getcwd()
print(curdir)
print("")
path=Path(curdir)
adir=str(path)+"/"+stem+"/"

try:
  if not os.path.exists(adir):
    os.mkdir(adir)
except OSError:
  print("Unable to create a directory under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# Read the data from a csv file
rgb_data=[]
pos=[]
hlen=0
try:
    with open(rgb_in,"r") as reader_obj:
        csv_reader=csv.reader(reader_obj)
        header_rgb=next(csv_reader)
        xaxis_label=header_rgb[0]
        hlen=len(header_rgb)
               
        for row in csv_reader:
            if hlen==5:
                rgb_data.append(list(map(float,row[1:-1])))
            elif hlen==4:
                rgb_data.append(list(map(float,row[1:])))
            pos.append(int(row[0]))

except OSError:
    print("Unable to open "+rgb_in+" in following directory:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)

# Data collection template
# color,peak/valley (1 or -1), peak_pos, rel_height, area, height, ybase, x0, x1
data=[]

datalen=len(rgb_data)
arr1=np.array(rgb_data)
arr1=arr1.T

xs=pos
r=arr1[0]
g=arr1[1]
b=arr1[2]

red=[]
green=[]
blue=[]

if findPeaks:
    # Search red peaks
    fig=plt.figure()
    rpeaks,rproperties=find_peaks(r,distance=distance,prominence=prominence,width=width)
    rcontour_heights=r[rpeaks]-rproperties["prominences"]*rel_height
    rfull=peak_widths(r,rpeaks,rel_height=rel_height)
    ph=r[rpeaks]-rcontour_heights
    plt.xlabel(header_rgb[0])
    plt.ylabel(header_rgb[1])
    plt.xlim(xs[0],xs[-1])
    plt.plot(r,color="r")
    plt.plot(rpeaks,r[rpeaks],"x",color="k")
    plt.vlines(x=rpeaks,ymin=rcontour_heights,ymax=r[rpeaks],color="k")
    plt.hlines(*rfull[1:],color="k")
    plt.grid()
    plt.savefig(adir+"r_peaks.png",dpi=300)
    if showGraphs:
        plt.show()
    plt.close()
    
    i=0
    while i<len(rpeaks):
        color="R"
        peak=1 # 1 = Peak, -1 = Valley
        pos=rpeaks[i]
        rheight=rel_height
        # Calculate area under curve
        x1=int(round(rfull[2][i]))
        x2=int(round(rfull[3][i]))
        area=int(round(auc(xs[x1:x2],r[x1:x2])))
        peak_height=round(ph[i],6)
        ybase=rcontour_heights[i]
        data.append([color,peak,pos,rheight,area,peak_height,ybase,x1,x2])   
        i+=1

if findValleys:
    # Search red valleys
    r=-r
    fig=plt.figure()
    rpeaks,rproperties=find_peaks(r,distance=distance,prominence=prominence,width=width)
    rcontour_heights=r[rpeaks]-rproperties["prominences"]*rel_height
    rfull=peak_widths(r,rpeaks,rel_height=rel_height)
    ph=r[rpeaks]-rcontour_heights
    plt.xlabel(header_rgb[0])
    plt.ylabel(header_rgb[1])
    plt.xlim(xs[0],xs[-1])
    plt.plot(-r,color="r")
    plt.plot(rpeaks,-r[rpeaks],"x",color="k")
    plt.vlines(x=rpeaks,ymin=-rcontour_heights,ymax=-r[rpeaks],color="k")
    plt.hlines(y=-rfull[1],xmin=rfull[2],xmax=rfull[3],color="k")
    plt.grid()
    plt.savefig(adir+"r_valleys.png",dpi=300)
    if showGraphs:
        plt.show()
    plt.close()
    
    i=0
    while i<len(rpeaks):
        color="R"
        peak=-1 # 1 = Peak, -1 = Valley
        pos=rpeaks[i]
        rheight=rel_height
        # Calculate area under curve
        x1=int(round(rfull[2][i]))
        x2=int(round(rfull[3][i]))
        area=abs(int(round(auc(xs[x1:x2],r[x1:x2]))))
        peak_height=round(ph[i],6)
        ybase=rcontour_heights[i]
        data.append([color,peak,pos,rheight,area,-peak_height,-ybase,x1,x2])   
        i+=1

if findPeaks:
    # Search green peaks
    fig=plt.figure()
    gpeaks,gproperties=find_peaks(g,distance=distance,prominence=prominence,width=width)
    gcontour_heights=g[gpeaks]-gproperties["prominences"]*rel_height
    gfull=peak_widths(g,gpeaks,rel_height=rel_height)
    ph=g[gpeaks]-gcontour_heights
    plt.xlabel(header_rgb[0])
    plt.ylabel(header_rgb[2])
    plt.xlim(xs[0],xs[-1])
    plt.plot(g,color="g")
    plt.plot(gpeaks,g[gpeaks],"x",color="k")
    plt.vlines(x=gpeaks,ymin=gcontour_heights,ymax=g[gpeaks],color="k")
    plt.hlines(*gfull[1:],color="k")
    plt.grid()
    plt.savefig(adir+"g_peaks.png",dpi=300)
    if showGraphs:
        plt.show()
    plt.close()
    
    i=0
    while i<len(gpeaks):
        color="G"
        peak=1 # 1 = Peak, -1 = Valley
        pos=gpeaks[i]
        rheight=rel_height
        # Calculate area under curve
        x1=int(round(gfull[2][i]))
        x2=int(round(gfull[3][i]))
        area=int(round(auc(xs[x1:x2],g[x1:x2])))
        peak_height=round(ph[i],6)
        ybase=gcontour_heights[i]
        data.append([color,peak,pos,rheight,area,peak_height,ybase,x1,x2])   
        i+=1

if findValleys:
    # Search green valleys
    g=-g
    fig=plt.figure()
    gpeaks,gproperties=find_peaks(g,distance=distance,prominence=prominence,width=width)
    gcontour_heights=g[gpeaks]-gproperties["prominences"]*rel_height
    gfull=peak_widths(g,gpeaks,rel_height=rel_height)
    ph=g[gpeaks]-gcontour_heights
    plt.xlabel(header_rgb[0])
    plt.ylabel(header_rgb[2])
    plt.xlim(xs[0],xs[-1])
    plt.plot(-g,color="g")
    plt.plot(gpeaks,-g[gpeaks],"x",color="k")
    plt.vlines(x=gpeaks,ymin=-gcontour_heights,ymax=-g[gpeaks],color="k")
    plt.hlines(y=-gfull[1],xmin=gfull[2],xmax=gfull[3],color="k")
    plt.grid()
    plt.savefig(adir+"g_valleys.png",dpi=300)
    if showGraphs:
        plt.show()
    plt.close()
    
    i=0
    while i<len(gpeaks):
        color="G"
        peak=-1 # 1 = Peak, -1 = Valley
        pos=gpeaks[i]
        rheight=rel_height
        # Calculate area under curve
        x1=int(round(gfull[2][i]))
        x2=int(round(gfull[3][i]))
        area=abs(int(round(auc(xs[x1:x2],g[x1:x2]))))
        peak_height=round(ph[i],6)
        ybase=gcontour_heights[i]
        data.append([color,peak,pos,rheight,area,-peak_height,-ybase,x1,x2])   
        i+=1

if findPeaks:
    # Search blue peaks
    fig=plt.figure()
    bpeaks,bproperties=find_peaks(b,distance=distance,prominence=prominence,width=width)
    bcontour_heights=b[bpeaks]-bproperties["prominences"]*rel_height
    bfull=peak_widths(b,bpeaks,rel_height=rel_height)
    ph=b[bpeaks]-bcontour_heights
    plt.xlabel(header_rgb[0])
    plt.ylabel(header_rgb[3])
    plt.xlim(xs[0],xs[-1])
    plt.plot(b,color="b")
    plt.plot(bpeaks,b[bpeaks],"x",color="k")
    plt.vlines(x=bpeaks,ymin=bcontour_heights,ymax=b[bpeaks],color="k")
    plt.hlines(*bfull[1:],color="k")
    plt.grid()
    plt.savefig(adir+"b_peaks.png",dpi=300)
    if showGraphs:
        plt.show()
    plt.close()
    
    i=0
    while i<len(bpeaks):
        color="B"
        peak=1 # 1 = Peak, -1 = Valley
        pos=bpeaks[i]
        rheight=rel_height
        # Calculate area under curve
        x1=int(round(bfull[2][i]))
        x2=int(round(bfull[3][i]))
        area=int(round(auc(xs[x1:x2],b[x1:x2])))
        peak_height=round(ph[i],6)
        ybase=bcontour_heights[i]
        data.append([color,peak,pos,rheight,area,peak_height,ybase,x1,x2])   
        i+=1

if findValleys:
    # Search blue valleys
    b=-b
    fig=plt.figure()
    bpeaks,bproperties=find_peaks(b,distance=distance,prominence=prominence,width=width)
    bcontour_heights=b[bpeaks]-bproperties["prominences"]*rel_height
    bfull=peak_widths(b,bpeaks,rel_height=rel_height)
    ph=b[bpeaks]-bcontour_heights
    plt.xlabel(header_rgb[0])
    plt.ylabel(header_rgb[3])
    plt.xlim(xs[0],xs[-1])
    plt.plot(-b,color="b")
    plt.plot(bpeaks,-b[bpeaks],"x",color="k")
    plt.vlines(x=bpeaks,ymin=-bcontour_heights,ymax=-b[bpeaks],color="k")
    plt.hlines(y=-bfull[1],xmin=bfull[2],xmax=bfull[3],color="k")
    plt.grid()
    plt.savefig(adir+"b_valleys.png",dpi=300)
    if showGraphs:
        plt.show()
    plt.close()
    
    i=0
    while i<len(bpeaks):
        color="B"
        peak=-1 # 1 = Peak, -1 = Valley
        pos=bpeaks[i]
        rheight=rel_height
        # Calculate area under curve
        x1=int(round(bfull[2][i]))
        x2=int(round(bfull[3][i]))
        area=abs(int(round(auc(xs[x1:x2],b[x1:x2]))))
        peak_height=round(ph[i],6)
        ybase=bcontour_heights[i]
        data.append([color,peak,pos,rheight,area,-peak_height,-ybase,x1,x2])   
        i+=1

# Save the data
if len(data)>0:
    delimiter=","
    header=["Color"]
    header.append("Peak") # -1 = Valley
    header.append("Pos")  # Peak position
    header.append("RH")   # Relative haght: 1 = Full, 0.5 = Half
    header.append("Area") # a.u.
    header.append("Height")
    header.append("Y0")
    header.append("X0")
    header.append("X1")
    
    with open(adir+"peaks.csv","w") as f:
       writer=csv.writer(f,delimiter=delimiter)
       writer.writerow(header)
       writer.writerows(data)

# Create and save a log file
logname=stem+".log"
log=[]
log.append("rgbxy-peaks log file")
log.append("")
now=datetime.now()
log.append("Time: "+str(now.strftime("%Y-%m-%d, %H:%M:%S")))
log.append("")
log.append("Current directory:")
log.append(curdir)
log.append("")
log.append("RGBXY file     : "+fname)
log.append("Analysis files : "+adir)
log.append("")

tmp="Peaks mode     : "
if findPeaks:
    tmp+="Yes"
log.append(tmp)

tmp="Valleys mode   : "
if findValleys:
    tmp+="Yes"
log.append(tmp)

log.append("Distance       : "+str(distance))
log.append("Prominence     : "+str(prominence))
log.append("Width          : "+str(width))
log.append("Relative height: "+str(rheight))

with open(adir+"/"+logname, "w") as file:
    for row in log:
        file.write("%s\n" % row)
