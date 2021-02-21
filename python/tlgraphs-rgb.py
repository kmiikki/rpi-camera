#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 08:28:27 2021

@author: Kim Miikki
"""

import csv
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
logname="tlgraphs-rgb.log"
rgbname="rgb.csv"
outdir="rgb_tl"
ts_file="labels.ts"
delimeter=","
x_max_decimals=3
y_max_decimals=3
pngMode=True

data_lines=0
leading_zeros=0
headers=[]
lines=[]
time_text="Time"
unit=""
xaxis_label=""
yaxis_label=""
bracket_type=["()","[]"]
brackets="[]"
font_size=16

firstCharUpper=True
time_mode=True
# True:  header[1]="time [unit]" or
# False: header[1]="number"
auto_scale=False

xmin=0
xmax=0
ymin=0
ymax=0
rymin=0
rymax=0
gymin=0
gymax=0
bymin=0
bymax=0
bwymin=0
bwymax=0
xdecimals=0
ydecimals=0

isBW=False
isR=False
isG=False
isB=False
isLabelsFile=False
visLabelX=True
visLabelY=True

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

print("Generate time-lapse images from "+rgbname)

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
    with open(rgbname) as fp:
        line=0
        for row in fp:
            row=row.strip()
            if len(row)==0:
                continue
            if line>0:
                data_lines+=1
            line+=1
except:
    print("Unable to open: "+rgbname)
    print("Program is terminated.")
    print("")
    sys.exit(0)
    

interval_data=inputValue("data interval:",1,data_lines,interval_data,"","Interval is out of range!",True)    

# Extract headers and data
with open(rgbname) as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=delimeter)
    line=0
    for row in csv_reader:
        if len(row)==0:
            continue
        if line==0:
            headers=row
        elif (line-1) % interval_data == 0:
            lines.append([row[0],float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])])
        line+=1

if len(headers)!=6:
    print("Incorrect data header!")
    sys.exit(0)

if len(lines)==0:
    print("No RGB data!")
    sys.exit(0)
    
if headers[1]=="number":
    xaxis_label="Image"
    time_mode=False
else:
    time_mode=True
    unit=headers[1]
    left=unit.find("[")
    right=unit.rfind("]")
    if left>0:
        time_text=unit[:left].strip()
    if left>=0 and (right-left)>1:
        unit=unit[left+1:right]
        unit.strip()
    else:
        unit=""
    if len(unit)>0:
        brackets=inputListValue("bracket type",bracket_type,
                                brackets,"Not valid brackets",True)
        if firstCharUpper:
            xaxis_label=time_text[0].upper()+time_text[1:]
        xaxis_label+=" "
        if brackets=="()":
            xaxis_label+="("+unit+")"
        else:
            xaxis_label+="["+unit+"]"
    else:
        xaxis_label=input("Custom x-axis label: ")
        if len(xaxis_label)==0:
            visLabelX=False
isAuto=inputYesNo("auto label","Accept x-axis auto label '"+xaxis_label+"'",True)
if not isAuto:
    xaxis_label=input("Custom x-axis label: ")
    if len(yaxis_label)==0:
        visLabelX=False


# Minium and maximum values for all series
values=len(lines)-1
xmin=lines[0][1]
xmax=lines[values][1]
for col in range(2,6):
    i=0
    miny=-1
    maxy=-1
    for row in lines:
        if miny<0:
            miny=lines[i][col]
            maxy=lines[i][col]
        else:
            if lines[i][col]<miny:
                miny=lines[i][col]
            if lines[i][col]>maxy:
                maxy=lines[i][col]
        i+=1
    if col==2:
        bwymin=miny
        bwymax=maxy
    elif col==3:
        rymin=miny
        rymax=maxy
    elif col==4:
        gymin=miny
        gymax=maxy
    elif col==5:
        bymin=miny
        bymax=maxy
        
# Plot Selection
plot_selections=["RGB","BW","CUSTOM"]
selected_plotsbrackets=inputListValue("plot type",plot_selections,
                                      "CUSTOM","Not a valid selection",True,True)
if selected_plotsbrackets=="RGB":
    isR=True
    isG=True
    isB=True
elif selected_plotsbrackets=="BW":
    isBW=True
else:
    isBW=inputYesNo("BW","Enable BW channel",isBW)
    isR=inputYesNo("R","Enable R channel",isR)
    isG=inputYesNo("G","Enable G channel",isG)
    isB=inputYesNo("B","Enable B channel",isB)
isLabelsFile=inputYesNo("file write","Write labels.ts file",isLabelsFile)

if True in [isBW,isR,isG,isB]:
    ymins=[]
    ymaxs=[]
    if isBW:
        ymins.append(bwymin)
        ymaxs.append(bwymax)
    if isR:
        ymins.append(rymin)
        ymaxs.append(rymax)
    if isG:
        ymins.append(gymin)
        ymaxs.append(gymax)
    if isB:
        ymins.append(bymin)
        ymaxs.append(bymax)    
    ymin=min(ymins)
    ymax=max(ymaxs)
    
    # Create Y axis label
    if isBW and (not True in [isR,isG,isB]):
        yaxis_label="Grayscale mean value"
    elif (not isBW) and ([isR,isG,isB].count(True)>1):
        yaxis_label="RGB channel mean values"
    elif isBW and (True in [isR,isG,isB]):
        yaxis_label="RGB and Grayscale mean values"
    elif (not isBW) and ([isR,isG,isB].count(True)==1):
        if isR:
            yaxis_label="Red channel mean value"
        elif isG:
            yaxis_label="Green channel mean value"
        elif isB:
            yaxis_label="Blue channel mean value"
    isAuto=inputYesNo("auto label","Accept y-axis auto label '"+yaxis_label+"'",True)
    if not isAuto:
        yaxis_label=input("Custom y-axis label: ")
        if len(yaxis_label)==0:
            visLabelY=False
    tmp="Auto x-axis scale: "+str(xmin)+"-"+str(xmax)
    xauto=inputYesNo("auto x-axis scale",tmp,True)
    if not xauto:
        xmin=inputValue("x-axis min",0,xmax,xmin,"","Value out of range!",False)
        xmax=inputValue("x-axis max",xmin,xmax*2,xmax,"","Value out of range!",False)
    tmp="Auto y-axis scale: "+str(ymin)+"-"+str(ymax)
    yauto=inputYesNo("auto y-axis scale",tmp,True)
    if not yauto:
        ymin=inputValue("y-axis min",0,254,ymin,"","Value out of range!",False)
        ymax=inputValue("y-axis max",ymin,255,ymax,"","Value out of range!",False)
    xdecimals=int(inputValue("x-axis decimals",0,x_max_decimals,x_max_decimals,"","Value out of range!",False))
    ydecimals=int(inputValue("y-axis decimals",0,y_max_decimals,y_max_decimals,"","Value out of range!",False))
    
    img_width=inputValue("Master image width:",1,max_width,master_width,"","Width is out of range!",True)
    img_height=inputValue("Master image height:",1,max_height,master_height,"","Height is out of range!",True)
    pip_per_master=inputValue("PIP size (PIPs/master image axis):",2,10,3,"","Value is out of range!",True)
    pip_rect=pipXY("br",pip_per_master,(0,0,img_width-1,img_height-1))

    xmin=round(xmin,xdecimals)
    xmax=round(xmax,xdecimals)
    ymin=round(ymin,ydecimals)
    ymax=round(ymax,ydecimals)
    maxdigits=len(str(len(lines)))
    
    matrix=np.array(lines,dtype="object")
    matrix=matrix.T

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
    file.write("Bracket type : "+brackets+"\n")
    file.write("\n")
    file.write("Plots:\n")
    file.write(option_str("BW  ",isBW))
    file.write(option_str("RGB ",isR and isG and isB))
    file.write(option_str("R ch",isR))
    file.write(option_str("G ch",isG))
    file.write(option_str("B ch",isB))
    file.write("\n")
    file.write(option_str("Write labels.ts file",isLabelsFile))
    file.write(option_str("Time mode",time_mode))
    file.write("Unit: "+unit+"\n")
    file.write("\n")
    file.write("x-axis label     : "+xaxis_label+"\n")
    file.write(option_str("x-axis auto scale",xauto))
    file.write("x scale min      : "+str(xmin)+"\n")
    file.write("x scale max      : "+str(xmax)+"\n")
    file.write("x-axis decimals  : "+str(xdecimals)+"\n")
    file.write("\n")
    file.write("y-axis label     : "+yaxis_label+"\n")
    file.write(option_str("y-axis auto scale",yauto))
    file.write("y scale min      : "+str(ymin)+"\n")
    file.write("y scale max      : "+str(ymax)+"\n")
    file.write("y-axis decimals  : "+str(ydecimals)+"\n")
    file.write("\n")
    file.write("Master image width : "+str(master_width)+"\n")
    file.write("Master image height: "+str(master_height)+"\n")
    file.write("PIP/master axis    : "+str(pip_per_master)+"\n")
    file.write("PIP image width    : "+str(w)+"\n")
    file.write("PIP image height   : "+str(h)+"\n")

    # File writer part
    if isLabelsFile:
        tsheader=[]
        tsheader.append("T:255,255,255")
        tsheader.append("B:128,128,128")
        tsheader.append("A:0.4")       
        tsheader.append("S: 0")
        filets=open(ts_file,"w")
        for row in tsheader:
            filets.write(row+"\n")
        prefix="RGB: "
        # Apply rounding to all data elements
        for line in lines:
            line[1]=round(line[1],xdecimals)
            if xdecimals==0:
                line[1]=int(line[1])
            for i in range(2,6):
                line[i]=round(line[i],ydecimals)
                if ydecimals==0:
                    line[i]=int(line[i])
            r=f"{line[3]:.{ydecimals}f}"
            g=f"{line[4]:.{ydecimals}f}"
            b=f"{line[3]:.{ydecimals}f}"
            s=prefix+r+","+g+","+b
            filets.write(s+"\n")
        filets.close()
    
    t1=datetime.now()
    i=0
    print("Processing:")
    for data in lines:
        # Generate graphs
        i+=1
        fig=plt.figure()
        fig.set_size_inches(wi,hi)
        fig.set_size_inches(hi*(w/h),hi)

        plt.xlim(xmin,xmax)
        plt.ylim(ymin,ymax)
        if visLabelX:
            plt.xlabel(xaxis_label,fontsize=font_size)
        if visLabelY:
            plt.ylabel(yaxis_label,fontsize=font_size)
        # Plot data
        if isBW:
            plt.plot(matrix[1][:i],matrix[2][:i],color="k")
        if isR:
            plt.plot(matrix[1][:i],matrix[3][:i],color="r")
        if isG:
            plt.plot(matrix[1][:i],matrix[4][:i],color="g")
        if isB:
            plt.plot(matrix[1][:i],matrix[5][:i],color="b")
        #plt.show()
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
