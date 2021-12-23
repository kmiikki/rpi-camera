#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 10 17:34:56 2021

@author: Kim Miikki

Arguments:
-f rgb.csv -x -y -d

"""

import argparse
import csv
from csv import DictReader
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
np.set_printoptions(suppress=True) #prevent numpy exponential 
                                   #notation on print, default False
from scipy.signal import find_peaks
from sklearn.metrics import auc
from pathlib import Path
from datetime import datetime
from rpi.inputs2 import *

MIN_SCANS=4
MAX_SCANS=50
default_scans=8

MIN_WL=350
MAX_WL=1150

# rgb.csv file read threshold
bw_threshold=0

# start peaks height threshold
start_peak_h=20

color_threshold=1

baseline_error=""
filename="rgb.csv"
delimiter=","
isReverse=True
isManualThreshold=False
isGrid=True
isAutoX=False
isAutoY=False
isShow=False
decimals=3

parser=argparse.ArgumentParser()
parser.add_argument("-f","--file",type=Path, help="specify RGB file name",required=False)
parser.add_argument("-t", type=int,help="baseline threshold as integer (1-128)",required=False)
parser.add_argument("-n", action="store_true", help="non-reverse mode")
parser.add_argument("-x", action="store_true", help="auto scale y axis")
parser.add_argument("-y", action="store_true", help="auto scale y axis")
parser.add_argument("-ng", action="store_true", help="disable grid")
parser.add_argument("-d", action="store_true", help="display figures on screen")
args = parser.parse_args()

if args.file:
    stem=args.file.stem
    fname=str(args.file.name)
    filename=str(args.file)
if not os.path.isfile(filename):
    print("File "+str(filename)+" not found!")
    sys.exit(0)
stem+="-"

if args.t != None:
    isManualThreshold=True
    tmp=int(args.t)
    if tmp>0 and tmp<128:
        color_threshold=tmp
    else:
        baseline_error="Threshold out of range. Using default threshold."
if args.n:
    isReverse=False
if args.x:
    isAutoX=True
if args.y:
    isAutoY=True
if args.ng:
    isGrid=False
if args.d:
    isShow=True

print("Spectrum analysis for rgb.csv type data file")
print("(C) Kim Miikki 2021")
print("")
print("Analysis file: "+filename)
print("")

if len(baseline_error)>0:
    print(baseline_error)
    print("")

print("Current directory:")
curdir=os.getcwd()
path=Path(curdir)
print(curdir)
print("")

# Load rgb data from a file
#
# Table format:
# picture_name,number,bw,red,green,blue
data=[]
ranges=[]
start=-1
end=-1
with open(filename) as csv_file:
    csv_dict_reader=DictReader(csv_file, delimiter=delimiter)
    column_names=csv_dict_reader.fieldnames
    for row in csv_dict_reader:
        number=int(row["number"])
        bw=float(row["bw"])
        red=float(row["red"])
        green=float(row["green"])
        blue=float(row["blue"])
        data.append([number,bw,red,green,blue])
        if bw>bw_threshold:
            if start<0:
                start=number
        else:
            if start>0:
                end=number-1
                ranges.append([start,end,end-start+1])
                start=-1
data_lines=len(data)

if start>0:
    end=number
    ranges.append([start,end,end-start+1])
    start=-1

# Find the largest data range
ranges.sort(key = lambda i: i[2],reverse=True)
if len(ranges)<1:
    print("No data found. Program is terminated.")
    sys.exit(0)
start=ranges[0][0]
end=ranges[0][1]
if isReverse:
    data.sort(reverse=isReverse)
    start,end = data_lines-end,data_lines-start
 
data=np.array(data)
data=data.T

# Select the spectrum data range
spectrum=data[:,start:end]

# Get RGB and RGB difference arrays
bws=spectrum[1]
rs=spectrum[2]
gs=spectrum[3]
bs=spectrum[4]

bws_diff=np.diff(bws,1)
rs_diff=np.diff(rs,1)
gs_diff=np.diff(gs,1)
bs_diff=np.diff(bs,1)

bws_adiff=abs(bws_diff)
rs_adiff=abs(rs_diff)
gs_adiff=abs(gs_diff)
bs_adiff=abs(bs_diff)

default_wl_min=MIN_WL
default_wl_max=MAX_WL

scans=inputValue("scans/nm",MIN_SCANS,MAX_SCANS,default_scans,"","Scans is out of range!",True)
wl_min=inputValue("scan start",MIN_WL,MAX_WL-10,default_wl_min,"nm","Wavelength is out of range!",True)
if default_wl_max<wl_min+10:
    default_wl_max=wl_min+10
    
wl_max=inputValue("scan end  ",wl_min+10,MAX_WL,default_wl_max,"nm","Wavelength is out of range!",True)

pdist=scans

# Find scan interval
pdist=pdist-2

# Find start peak from the start
start_peaks,start_peaks_height=find_peaks((bws_adiff)[:int(len(bws_adiff)/2)],height=start_peak_h)
if len(start_peaks)>0:
    start=start_peaks[-1]+1       
    spectrum=data[:,start:end]

    bws=spectrum[1]
    rs=spectrum[2]
    gs=spectrum[3]
    bs=spectrum[4]
    
    bws_diff=np.diff(bws,1)
    rs_diff=np.diff(rs,1)
    gs_diff=np.diff(gs,1)
    bs_diff=np.diff(bs,1)
    
    bws_adiff=abs(bws_diff)
    rs_adiff=abs(rs_diff)
    gs_adiff=abs(gs_diff)
    bs_adiff=abs(bs_diff)

bws_peaks,bws_properties=find_peaks(bws_adiff,distance=pdist)

sum_adiff=rs_adiff+gs_adiff+bs_adiff
sum_adiff_peaks,sum_adiff_properties=find_peaks(sum_adiff,distance=pdist)
sum_adiff_peaksint=np.diff(sum_adiff_peaks,1)

if len(spectrum)<0:
    print("No peaks found.")
    sys.exit(0)

color=-1

print("")
print("Mean scan width: "+str(round(sum_adiff_peaksint.mean(),3)))
print("")
tmp=""
while True:
    tmp=input("Select calibration color (R,G,B; Default=R):")
    tmp=tmp.strip().upper()
    if tmp=="":
        print("Default selected: R")
        color=2
        break
    if tmp=="R":
        color=2
    elif tmp=="G":
        color=3
    elif tmp=="B":
        color=4
    if color>0:
        break

colors=["red","green","blue"]
ch_wl_default=[579,481,385]
wl_cal=inputValue(colors[color-2]+" lower limit wavelength",MIN_WL,MAX_WL,ch_wl_default[color-2],"nm","Wavelength is out of range!",True)

# calculate mean RGB values/nm
index=0  
sp=[]
wl=wl_min
print("")
print("Analyzing the spectrum")

while wl<=wl_max:
    if index+1 >= len(sum_adiff_peaks):
        break
    a=sum_adiff_peaks[index]
    b=sum_adiff_peaks[index+1]
    part=spectrum[:,a:b]
    gray=round(part[1].mean(),3)
    red=round(part[2].mean(),3)
    green=round(part[3].mean(),3)
    blue=round(part[4].mean(),3)   
    sp.append([index,gray,red,green,blue])
    index+=1
    wl+=1

# Convert sp to a Numpy array and transpose it
sp=np.array(sp)
sp=sp.T

# Get RGB channel spectra
bws=sp[1]
rs=sp[2]
gs=sp[3]
bs=sp[4]       

# Determine the baseline for the selected channel
baseline=0
basemin=1
basemax=20
csum=(sp[color]==0).sum()
results=[]
results.append([csum,0])
for i in range(basemin,basemax+1):
    n=(sp[color]<i).sum()
    d=n-csum
    csum+=d
    results.append([d,i])

# Get the baseline
results.sort(reverse=True)
value=-1
for line in results:
    #print(line)
    count=line[0]
    pos=line[1]
    if value<0:
        value=pos
        continue
    if count>10 and pos>value:
        value=pos
    elif count<=10:
        break
if value>0:
    baseline=value
if not isManualThreshold:
    color_threshold=baseline

# Search for the channel lower limit
ch_res=(sp[color]>=color_threshold)
peakFound=False
findZero=False
i=0
while i<len(bws):
    result=ch_res[i]
    if findZero and result:
        peakFound=True
        break
    if (not findZero) and (not result):
        findZero=True
    i+=1
if not peakFound:
    print("Channel "+colors[color-2]+" lower limit not found.")
    sys.exit(0)

# Adjust the spectrum wavelength    
adj_nm=wl_cal-i
sp[0]+=adj_nm
range_start=i-10
range_end=i+10+1
if range_start<0:
    range_start=0
if range_end>=len(sp.T):
    range_end=len(sp.T)-1
sp_print=sp.T[range_start:range_end]

# Print the calibration region
header="WL".rjust(8)+"GRAY".rjust(8)+"R".rjust(9)+"G".rjust(9)+"B".rjust(9)
print(header)
for row in sp_print:
    wl=int(row[0])
    gray=row[1]
    red=row[2]
    green=row[3]
    blue=row[4]
    print((str(wl)+" nm").rjust(7),str(gray).rjust(8),str(red).rjust(8),str(green).rjust(8),str(blue).rjust(8))

wl_adj=inputValue("adjust wavelength",-10,10,0,"nm","Wavelength is out of range!",True)
if wl_adj != 0:
    sp[0]-=wl_adj

xs=sp[0]
#xs=np.arange(wl_min,wl_max+1,1)

# Calculate RGB areas
gray_area=round(auc(xs,bws))
red_area=round(auc(xs,rs))
green_area=round(auc(xs,gs))
blue_area=round(auc(xs,bs))

# Find highest RGB peaks
peaks=[]
if bs.max()>0:
    bpeaks=np.where(bs==bs.max())
    for i in bpeaks[0]:
        peaks.append(["B",xs[i],bs[i],blue_area])

if gs.max()>0:
    gpeaks=np.where(gs==gs.max())
    for i in gpeaks[0]:
        peaks.append(["G",xs[i],gs[i],green_area])

if rs.max()>0:
    rpeaks=np.where(rs==rs.max())
    for i in rpeaks[0]:
        peaks.append(["R",xs[i],rs[i],red_area])

if bws.max()>0:
    bwpeaks=np.where(bws==bws.max())
    for i in bpeaks[0]:
        peaks.append(["GRAY",xs[i],bws[i],gray_area])

print("")
print("Saving data...")
   
# Plot a calibration graph: RGB
tmp=stem
tmp+="spectrum"
tmp+="-rgb.png"

if isAutoX:
    minx=sp[0][0]
    maxx=sp[0][-1]
else:
    minx=wl_min
    maxx=wl_max
    
if isAutoY:
    miny=sp[2:5].min()
    maxy=sp[2:5].max()
else:
    miny=0
    maxy=255
fig=plt.figure()
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer = True))
plt.xlim(minx,maxx)
plt.ylim(miny,maxy)
if isGrid:
    plt.grid()
plt.plot(xs,sp[2],color="r")
plt.plot(xs,sp[3],color="g")
plt.plot(xs,sp[4],color="b")
#if isCalibration:
#    plt.axvline(int(wl_ref+wl_adj),color="k",ls="--")
plt.xlabel("Wavelength (nm)")
plt.ylabel("RGB mean")
plt.savefig(tmp,dpi=300)
plt.axvline(int(wl_cal+wl_adj),color="k",ls="--")
tmp=stem
tmp+="spectrum"
tmp+="-rgb-cal.png"
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show(fig)
plt.close(fig)

# Red spectrum
tmp=stem
tmp+="spectrum"
tmp+="-r.png"
if isAutoY:
    miny=sp[2].min()
    maxy=sp[2].max()
fig=plt.figure()
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer = True))
plt.xlim(minx,maxx)
plt.ylim(miny,maxy)
if isGrid:
    plt.grid()
plt.plot(xs,sp[2],color="r")
plt.xlabel("Wavelength (nm)")
plt.ylabel("RGB mean, red channel")
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show(fig)
plt.close(fig)

# Green spectrum
tmp=stem
tmp+="spectrum"
tmp+="-g.png"
if isAutoY:
    miny=sp[3].min()
    maxy=sp[3].max()
fig=plt.figure()
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer = True))
plt.xlim(minx,maxx)
plt.ylim(miny,maxy)
if isGrid:
    plt.grid()
plt.plot(xs,sp[3],color="g")
plt.xlabel("Wavelength (nm)")
plt.ylabel("RGB mean, green channel")
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show(fig)
plt.close(fig)

# Red spectrum
tmp=stem
tmp+="spectrum"
tmp+="-b.png"
if isAutoY:
    miny=sp[4].min()
    maxy=sp[4].max()
fig=plt.figure()
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer = True))
plt.xlim(minx,maxx)
plt.ylim(miny,maxy)
if isGrid:
    plt.grid()
plt.plot(xs,sp[4],color="b")
plt.xlabel("Wavelength (nm)")
plt.ylabel("RGB mean, blue channel")
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show(fig)
plt.close(fig)
    
# Gray spectrum
tmp=stem
tmp+="spectrum"
tmp+="-gray.png"
if isAutoY:
    miny=sp[1].min()
    maxy=sp[1].max()
fig=plt.figure()
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer = True))
plt.xlim(minx,maxx)
plt.ylim(miny,maxy)
if isGrid:
    plt.grid()
plt.plot(xs,sp[1],color="k")
plt.xlabel("Wavelength (nm)")
plt.ylabel("Gray mean")
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show(fig)
plt.close(fig)

# Area plot
tmp=stem
tmp+="aspectrum"
tmp+="-areas.png"
fig=plt.figure()
height = [red_area,green_area,blue_area]
bars = ("RED","GREEN","BLUE")
x_pos = np.arange(len(bars))
# Create bars with different colors
plt.bar(x_pos, height, color=["red","green","blue"])
# Create names on the x-axis
plt.xticks(x_pos, bars)
plt.ylabel("Area under curve")
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show()
plt.close(fig)

# Height plot
tmp=stem
tmp+="aspectrum"
tmp+="-heights.png"
fig=plt.figure()
height = [rs.max(),gs.max(),bs.max()]
bars = ("RED","GREEN","BLUE")
x_pos = np.arange(len(bars))
# Create bars with different colors
plt.bar(x_pos, height, color=["red","green","blue"])
# Create names on the x-axis
plt.xticks(x_pos, bars)
plt.ylabel("Maximum peak height (color value)")
plt.savefig(tmp,dpi=300)
if isShow:
    plt.show()
plt.close(fig)

# Save a data file
sp=sp.T
header=["Wavelength (nm)","Gray","Red","Green","Blue"]
tmp=stem+"aspectrum.csv"
with open(tmp,"w") as file:
    writer=csv.writer(file,delimiter=",")
    writer.writerow(header)
    for row in sp:
        wavelength=str(int(row[0]))
        gray=str(row[1])
        red=str(row[2])
        green=str(row[3])
        blue=str(row[4])
        writer.writerow([wavelength,gray,red,green,blue])

# Save RGB peak data
header=["Color","Wavelength (nm)","Height","Area"]
tmp=stem+"aspectrum-peaks.csv"
with open(tmp,"w") as file:
    writer=csv.writer(file,delimiter=",")
    writer.writerow(header)
    for row in peaks:
        c=str(row[0])
        wavelength=str(int(row[1]))
        height=str(int(row[2]))
        area=str(row[3])
        writer.writerow([c,wavelength,height,area])


# Append the analysis data to a log array
log=[]
at1=datetime.now()
log.append("Spectrum analysis log file")
log.append("")
log.append("Time: "+str(at1))
log.append("")
log.append("Spectrum file: "+filename)
log.append("")
tmp="Reverse mode: "
if isReverse:
    tmp+="Yes"
else:
    tmp+="No"
log.append(tmp)
log.append("")
log.append("Scan")
log.append("----")
tmp=str(wl_min)+"-"+str(wl_max)+" nm"
log.append("Range (measurement): "+tmp)
tmp=str(int(xs[0]))+"-"+str(int(xs[-1]))+" nm"
log.append("Range (data)       : "+tmp)
log.append("Scans/nm           : "+str(scans))
log.append("Mean scan width    : "+str(round(sum_adiff_peaksint.mean(),3)))
if color==2:
    tmp="R"
elif color==3:
    tmp="G"
elif color==4:
    tmp="B"
else:
    tmp="N/A"
log.append("Calibration color     : "+str(tmp))
log.append("Calibration wavelength: "+str(wl_cal)+" nm")
log.append("Wavelength adjustment : "+str(wl_adj)+" nm")
log.append("")

if isAutoX:
    tmp="Yes"
else:
    tmp="No"
log.append("Auto x-axis : "+tmp)
if isAutoY:
    tmp="Yes"
else:
    tmp="No"
log.append("Auto y-axis : "+tmp)
if isGrid:
    tmp="Yes"
else:
    tmp="No"
log.append("Grid enabled: "+tmp)

log.append("")
log.append("Thresholds")
log.append("----------")
log.append("Read threshold       : "+str(bw_threshold))
log.append("Color threshold      : "+str(color_threshold))
log.append("Baseline calculated  : "+str(results[0][1]))
if isManualThreshold and len(baseline_error)==0:
    log.append("Manual baseline      : "+str(color_threshold))
log.append("")
log.append("Start peaks threshold: "+str(start_peak_h))

# Save the log file
tmp=stem+"aspectrum.log"
with open (tmp,"w") as f:
    for line in log:
        f.write(line+"\n")
