#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 15:57:34 2021

@author: Kim Miikki
"""

import csv
import math
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pathlib import Path
from rpi.inputs2 import *

max_width=9999
max_height=9999
master_width=1280
master_height=960

interval_data=1
logname="tlgraphs-xy.log"
xyname="xydata.csv"
outdir="xy_tl"
delimeter=","
x_default_decimals=2
y_default_decimals=2
x_max_decimals=10
y_max_decimals=10
pngMode=True

data_lines=0
leading_zeros=0
headers=[]
lines=[]
time_text="Time"
unit=""
xaxis_label=""
yaxis_label=""
font_size=16
auto_scale=False

xmin=0
xmax=0
ymin=0
ymax=0
xdecimals=0
ydecimals=0

columns=0
is2D=False
isLabelsFile=False
visLabelX=True
visLabelY=True
isLogX=False
isLogY=False

def pipXY(position,pics_per_axis,img_rect):
    """
    Position string:
    TL, TC, TR = Top Left    | Top Center    | Top Left
    CL, CC, CR = Center Left | Center Center | Center Left
    BL, BC, BR = Bottom Left | Bottom Center | Bottom Left
    
    img_rect=(x0,y0,x1,y0)
    return pip_rect
    
    """
    x0=-1
    y0=-1
    x1=-1
    y1=-1
    pip_rect=(-1,-1,-1,-1)
    if pics_per_axis<1 or pics_per_axis>10:
        return pip_rect
    if len(position)!=2 or type(position)!=str:
        return pip_rect
    position=position.strip()
    posy=position[0].lower()
    posx=position[1].lower()
    if not ((posy in ["t","c","b"]) and posx in ["l","c","r"]):
        return pip_rect

    # Validate img_rect
    # Format: (a,b,c,d)
    validTuple=True
    if type(img_rect)==tuple:
        if len(img_rect)==4:
            for item in img_rect:
                if type(item) is not int:
                    validTuple=False
        else:
            validTuple=False
    else:
        validTuple=False
    
    # Test int values
    if validTuple:
        if min(img_rect)<0:
            validTuple=False
        if img_rect[0]>=img_rect[2] or img_rect[1]>=img_rect[3]:
            validTuple=False
    if not validTuple:
        return pip_rect
    
    width=img_rect[2]-img_rect[0]+1
    height=img_rect[3]-img_rect[1]+1

    # Calculate PIP coordinates
    if posy=="t":
        y0=img_rect[1]
        y1=img_rect[1]+height/pics_per_axis
    elif posy=="c":
        y0=(height-height/(pics_per_axis))/2
        y1=(height+height/(pics_per_axis))/2
    elif posy=="b":
        y0=img_rect[3]-height/pics_per_axis
        y1=img_rect[3]
    
    if posx=="l":
        x0=img_rect[0]
        x1=img_rect[0]+width/pics_per_axis
    elif posx=="c":
        x0=(width-width/(pics_per_axis))/2
        x1=(width+width/(pics_per_axis))/2
    elif posx=="r":
        x0=img_rect[2]-width/pics_per_axis
        x1=img_rect[2]
   
    x0=int(x0)
    x1=int(x1)
    y0=int(y0)
    y1=int(y1)
    pip_rect=(x0,y0,x1,y1)
    return pip_rect

def option_str(option,selected,end="\n"):
    s=option+": "
    if selected:
        s+="Yes"
    else:
        s+="No"
    s+=end
    return s

print("Generate time-lapse images from "+xyname)

curdir=os.getcwd()
path=Path(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

try:
    if not os.path.exists(outdir):
        os.mkdir(outdir)
except OSError:
    print("Unable to create a directory or directories under following path:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)

# Count rgb.csv data lines
try:
    with open(xyname) as fp:
        line=0
        for row in fp:
            row=row.strip()
            if len(row)==0:
                continue
            if line>0:
                data_lines+=1
            line+=1
except:
    print("Unable to open: "+xyname)
    print("Program is terminated.")
    print("")
    sys.exit(0)
    

interval_data=inputValue("data interval:",1,data_lines,interval_data,"","Interval is out of range!",True)    

# Extract headers and data
error=False
elements=0
with open(xyname) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=delimeter)
    line=0
    for row in csv_reader:
        if len(row)==0:
            continue
        if line==0:
            headers=row
            columns=len(headers)
        elif (line-1) % interval_data == 0:
            if len(row)!=columns:
                error=True
                elements=len(row)
                break
            a=[]
            for data in row:
                a.append(float(data))
            lines.append(a)
        line+=1

if error:
    print("Data size mismatch with headers.")
    print("Header count: "+str(columns))
    print("Data count in line "+str(line+1)+": "+str(elements))
    sys.exit(0)

if len(lines)==0:
    print("No xy data!")
    sys.exit(0)

if columns<2:
    print("At least 2 data columns are required.")
    sys.exit(0)

print("Data size: "+str(columns)+"x"+str(len(lines)))
print("")

if columns==2:
    is2D=True
xaxis_label=headers[0]
yaxis_label=headers[1]
       
isAuto=inputYesNo("auto label","Accept x-axis auto label '"+xaxis_label+"'",True)
if not isAuto:
    xaxis_label=input("Custom x-axis label: ")
if len(yaxis_label)==0:
    visLabelX=False

isAuto=inputYesNo("auto label","Accept y-axis auto label '"+yaxis_label+"'",True)
if not isAuto:
    yaxis_label=input("Custom x-axis label: ")
if len(yaxis_label)==0:
    visLabelY=False
print("")

matrix=np.array(lines,dtype="object")
matrix=matrix.T

# Minium and maximum values for all series
xmin=matrix[0].min()
xmax=matrix[0].max()
ymin=matrix[1:].min()
ymax=matrix[1:].max()        

isLogX=inputYesNo("logarithmic x-axis","Logarithmic x-axis scale",False)
tmp="Auto x-axis scale: "+str(xmin)+"-"+str(xmax)
xauto=inputYesNo("auto x-axis scale",tmp,True)
if not xauto:
    if isLogX:
        x_min=1e-9
        x=math.log10(xmax)
        x_max=10**int(x+1)
    else:
        x_min=-xmin
        x_max=2*xmax
    xmin=inputValue("x-axis min",x_min,xmax,xmin,"","Value out of range!",False)
    xmax=inputValue("x-axis max",xmin,x_max,xmax,"","Value out of range!",False)
print("")

isLogY=inputYesNo("logarithmic y-axis","Logarithmic y-axis scale",False)
tmp="Auto y-axis scale: "+str(ymin)+"-"+str(ymax)
yauto=inputYesNo("auto y-axis scale",tmp,True)
if not yauto:
    if isLogY:
        y_min=1e-9
        y=math.log10(xmax)
        y_max=10**int(y+1)
    else:
        y_min=-ymin
        y_max=2*ymax
    ymin=inputValue("y-axis min",y_min,ymax,ymin,"","Value out of range!",False)
    ymax=inputValue("y-axis max",ymin,y_max,ymax,"","Value out of range!",False)
print("")

xdecimals=int(inputValue("x-axis decimals",0,x_max_decimals,x_default_decimals,"","Value out of range!",False))
ydecimals=int(inputValue("y-axis decimals",0,y_max_decimals,y_default_decimals,"","Value out of range!",False))
print("")

font_sizes=[10,12,14,16,18,20,24,36]
font_size=inputListValue("font size",font_sizes,16)
line_colors=['B', 'G', 'R', 'C', 'M', 'Y', 'K','GRAY','CUSTOM']
color=inputListValue("line color",line_colors,"K","Not a valid selection",True,True)
color=color.lower()
if color=="gray":
    color="0.5"
if color=="custom":
    r=inputValue("red color value",0,255,0,"","Value out of range!",True)
    g=inputValue("green color value",0,255,0,"","Value out of range!",True)
    b=inputValue("blue color value",0,255,0,"","Value out of range!",True)
    color="#"+(r*65536+g*256+b).to_bytes(3,"big").hex()
print("")

img_width=inputValue("Master image width:",1,max_width,master_width,"","Width is out of range!",True)
img_height=inputValue("Master image height:",1,max_height,master_height,"","Height is out of range!",True)
pip_per_master=inputValue("PIP size (PIPs/master image axis):",2,10,3,"","Value is out of range!",True)
pip_rect=pipXY("br",pip_per_master,(0,0,img_width-1,img_height-1))

if not isLogX:
    xmin=round(xmin,xdecimals)
    xmax=round(xmax,xdecimals)
if not isLogY:
    ymin=round(ymin,ydecimals)
    ymax=round(ymax,ydecimals)
maxdigits=len(str(len(lines)))

# HQ camera video mode 4
# Resolution 1012 x 760
# PIP (1/3)   337 x 253

# Matplotlib size and resolution    
wi=8
hi=6
#w=337
#h=253
w=pip_rect[2]-pip_rect[0]
h=pip_rect[3]-pip_rect[1]

# Create a log file
file=open(logname,"w")
file.write("tlgraphs-rgb\n\n")
file.write("Source directory: "+curdir+"\n\n")
file.write("Data interval: "+str(interval_data)+"\n")
file.write("\n")
file.write("x-axis label     : "+xaxis_label+"\n")
file.write("x-axis log scale : ")    
if isLogX:
    file.write("Yes\n")
else:
    file.write("No\n")
file.write(option_str("x-axis auto scale",xauto))
file.write("x scale min      : "+str(xmin)+"\n")
file.write("x scale max      : "+str(xmax)+"\n")
file.write("x-axis decimals  : "+str(xdecimals)+"\n")
file.write("\n")
file.write("y-axis label     : "+yaxis_label+"\n")
file.write("y-axis log scale : ")        
if isLogY:
    file.write("Yes\n")
else:
    file.write("No\n")
file.write(option_str("y-axis auto scale",yauto))
file.write("y scale min      : "+str(ymin)+"\n")
file.write("y scale max      : "+str(ymax)+"\n")
file.write("y-axis decimals  : "+str(ydecimals)+"\n")
file.write("\n")
file.write("Font size : "+str(font_size)+"\n")
file.write("Line color: "+color+"\n")
file.write("\n")
file.write("Master image width : "+str(master_width)+"\n")
file.write("Master image height: "+str(master_height)+"\n")
file.write("PIP/master axis    : "+str(pip_per_master)+"\n")
file.write("PIP image width    : "+str(w)+"\n")
file.write("PIP image height   : "+str(h)+"\n")

t1=datetime.now()
i=0
print("Processing:")
for data in lines:
    # Generate graphs
    i+=1
    fig=plt.figure()
    fig.set_size_inches(wi,hi)
    fig.set_size_inches(hi*(w/h),hi)
    if isLogX:
        plt.xscale("log")
    if isLogY:
        plt.yscale("log")
    
    plt.xlim(xmin,xmax)
    plt.ylim(ymin,ymax)
    if visLabelX:
        plt.xlabel(xaxis_label,fontsize=font_size)
    if visLabelY:
        plt.ylabel(yaxis_label,fontsize=font_size)
    # Plot data
    if is2D:
        plt.plot(matrix[0][:i],matrix[1][:i],color=color)
    tmp=str(i).zfill(maxdigits)
    print(tmp+"/"+str(len(lines)))
    tmp=outdir+"/"+tmp
    if pngMode:
        tmp+=".png"
    else:
        tmp+=".jpg"
    plt.tick_params(labelsize=font_size)
    fig.tight_layout()
    plt.savefig(tmp,dpi=h/hi)
    plt.close()
    
t2=datetime.now()
file.write("\n")
file.write("Lines processed: "+str(i)+"\n")
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
print("")
print("Time elapsed: "+str(t2-t1))
