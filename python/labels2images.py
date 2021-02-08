#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 13:28:45 2021

@author: Kim Miikki

Overlay modes
-------------
Layer Type     Description              Time file extension
1     Internal interval                 -
2     ts       text stamps              ts
3     pts      presentation time stamps pts

ts format
---------
T:255,0,0     # Text color is red (RGB format)
B:128,128,128 # Gray text box
A:0.2         # Alpha for text box: 0-1, where 0 is transparent and 1 opaque
S:0           # Text and text box on same layer: 0 = no, 1 = yes
STRING1
STRING2
STRING3

Header lines: 4

String format:
12:40:00   Frame 1, Display frame unless - is specified
12:40:01-- Frame 2, Hide text from this frame onwards
12:40:02   Frame 3, Hidden frame
12:40:03++ Frame 4, Display text from this frame onwards

Empty lines are discarded

"""
import cv2
import math
import os
import pathlib
import sys
import time
from pathlib import Path
from rpi.inputs2 import *

units=["ms","s","min","h","d"]
divisors=[1,1000,1000*60,1000*60*60,1000*60*60*365]

font = cv2.FONT_HERSHEY_DUPLEX

# Internal mode
# Color values are in BGR format
text_color=(255,255,255)
text_scale=1
alphaText=False
marginal_x=30
marginal_y=50
vspace=10
hspace=10
rect_color=(0,0,0)
rect_alpha = 0.2

text_prefix="t= "
decimals_time=3
dst="labelpics"
pngMode=True
interval=0
intervalUpdate=0
pts_intervalUpdate=0

# TS mode
ts_file="labels.ts"
ts_text_color=(0,0,0)
ts_text_scale=1
ts_rect_color=(0,128,0)
ts_rect_alpha=0.4
tsAlphaText=False
ts_marginal_x=30
ts_marginal_y=50
ts_vspace=10
ts_hspace=10
ts_texts=[]
ts_text_max=0
ts_visible=[]
ts_visible_line=0
is_ts_visible=True

# TS mode
timelabels_ts="timelabels.ts"
pts_file="timelabels.pts"
pts_text_color=(0,255,0)
pts_text_scale=1
pts_rect_color=(128,128,0)
pts_rect_alpha=0.4
ptsAlphaText=False
pts_marginal_x=30
pts_marginal_y=50
pts_vspace=10
pts_hspace=10
pts_values=[]
pts_texts=[]
pts_unit=""
pts_divisor=1
pts_decimals=2

isInterval=True
isTS=False
isPTS=False
isCommonAlpha=False
common_alpha=0.4

def getTextInfo(text,font,scale=1.0):
    #font = cv2.FONT_HERSHEY_DUPLEX
    (text_width,text_height),baseline=cv2.getTextSize(text,font,scale,1)
    return text_width,text_height

def getRectCoordinates(offset_x,offset_y,hspace,vspace,text_height):
    x0=offset_x-hspace
    y0=offset_y-text_height-vspace
    x1=offset_x+text_width+hspace
    y1=offset_y+vspace
    return x0,y0,x1,y1

def getTimeStr(start,interval,pictures,intMode=True):
    t=start+interval*pictures
    if intMode:
        return str(t)
    else:
        t=str(round(t,decimals_time))
        fillzeros=decimals_time-(len(t)-(t.rfind(".")+1))
        t+="0"*fillzeros
        return t        

def TextPosition(label,width,height,hspace,vspace,text_width,text_height,marginal_x,marginal_y):
    textPositions=[]
    textPositions.append([1,"TL",marginal_x,marginal_y])
    textPositions.append([2,"TC",int((width-text_width)/2),marginal_y])
    textPositions.append([3,"TR",int(width-text_width-marginal_x),marginal_y])
    textPositions.append([4,"CL",marginal_x,int((height+text_height)/2)])
    textPositions.append([5,"CC",int((width-text_width)/2),int((height+text_height)/2)])
    textPositions.append([6,"CR",int(width-text_width)-marginal_x,int((height+text_height)/2)])
    textPositions.append([7,"BL",marginal_x,int(height+text_height-marginal_y)])
    textPositions.append([8,"BC",int((width-text_width)/2),int(height+text_height-marginal_y)])
    textPositions.append([9,"BR",int(width-text_width)-marginal_x,int(height+text_height-marginal_y)])
    modes=len(textPositions)
    mode=0
    print("")
    while True:
        try:
            print("Overlay "+label+" positions")
            print("Md\tPos\tX0\tY0")
            for row in textPositions:
                tmp=str(row[0])+"\t"+str(row[1])+"\t"+str(row[2])+"\t"+str(row[3])
                tmp+="\t"
                print(tmp)
            tmp=input("Select text position (1..."+str(modes)+"): ")
            mode=int(tmp)
        except ValueError:
            print("Not a valid number!")
            continue
        else:
            if ((mode<1)or(mode>modes)):
                print("Invalid mode!\n")
                continue
            break
    
    text_x=textPositions[mode-1][2]
    text_y=textPositions[mode-1][3]
    rect_x0,rect_y0,rect_x1,rect_y1=getRectCoordinates(text_x,
                                                       text_y,
                                                       hspace,
                                                       vspace,text_height)    
    return text_x,text_y,rect_x0,rect_y0,rect_x1,rect_y1

def parseRGB(rgbString):
    r=0
    g=0
    b=0
    tmp=rgbString.strip()
    tmp=tmp.split(",")
    if isinstance(tmp,list) and len(tmp)==3:
        try:
            r=int(tmp[0])
            g=int(tmp[1])
            b=int(tmp[2])
        except:
            pass
    return (b,g,r)

def autounit(timeval):
    divisor=1
    u=0
    # Seconds
    if timeval/1000>=5:
        u+=1
        divisor*=1000
    # Minutes
    if timeval/(1000*60)>=5:
        u+=1
        divisor*=60
    # Hours
    if timeval/(1000*60*60)>=5:
        u+=1
        divisor*=60
    # Days
    if timeval/(1000*60*60*24)>=5:
        u+=1
        divisor*=24   
    return units[u],divisor

print("Labels to Images - labels2images.py")
print("(C) Kim Miikki 2021\n")

curdir=os.getcwd()
print("Current directory:")
print(curdir)
print("")

# Test if ts or pts files are present
if pathlib.Path(ts_file).exists():
    isTS=True
if pathlib.Path(pts_file).exists():
    isPTS=True
if isTS and isPTS:
    isInterval=False

isInterval=inputYesNo("Interval","Enable interval mode",isInterval)
print("")
isTS=inputYesNo("Interval","Enable TS mode",isTS)
print("")
isPTS=inputYesNo("Interval","Enable PTS mode",isPTS)
print("")

if not True in [isInterval,isTS,isPTS]:
    print("Label mode not selected!")
    sys.exit(0)

path=Path(curdir)
dst=str(path)+"/"+dst+"/"
try:
  if not os.path.exists(dst):
    os.mkdir(dst)
except OSError:
  print("Unable to create a directory under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

ext=input("Frames extension: ")
ext=ext.strip()
ext=ext.lower()
if len(ext)>0:
    if ext[0]!=".":
        ext="."+ext

# Calculate filtered files
files=0
sampleFile=""
for p in sorted(path.iterdir(),reverse=True):
    suffix=p.suffix.lower()
    if p.is_file():
        if suffix==ext:
            if files==0:
                sampleFile=p.name
            files+=1

if files==0:
    print("No files found!")
    sys.exit(0)

# Read sample image
frame = cv2.imread(sampleFile)
height,width,channels=frame.shape

if isInterval:
    print("")
    print("Interval mode")
    print("-------------")
    # Get time values
    unit=str(input("Unit: "))
    start=str(input("Start time: "))
    max_interval=files
    while interval<=0:
        interval=float(input("Interval between two frames: "))
    intervalUpdate=inputValue("update interval:",1,max_interval,1,"","Interval is out of range!",True)
    
    isInt=False
    try:
        float(start)
        float(interval)
    except:
        print("Invalid time value(s).")
        sys.exit(1)
    else:
        isInt=float(start).is_integer() and float(interval).is_integer()
    
    if isInt:
        start=int(start)
        interval=int(interval)
    else:
        start=float(start)
        interval=float(interval)

    # Create sample string
    sample=text_prefix+getTimeStr(start,interval,files,isInt)
    if len(unit)>0:
        sample+=" "+unit
    text=sample
    text_width,text_height=getTextInfo(text,font,text_scale)
    text_x,text_y,rect_x0,rect_y0,rect_x1,rect_y1=TextPosition("interval label",
                                                               width,
                                                               height,
                                                               hspace,
                                                               vspace,
                                                               text_width,
                                                               text_height,
                                                               marginal_x,
                                                               marginal_y)
if isTS:
    print("")
    print("TS mode")
    print("-------")
    # Read TS file values
    i=0
    var_lines=4
    var_list=[]
    var_names=[]
    lines=0
    sample=""
    with open(ts_file) as fp:
        for line in fp:
            line=line.strip()
            #print(line)
            i+=1
            if i<=var_lines:
                # Split line to var,value
                tmp=line.split(":")                
                if len(tmp)==2:
                    var=tmp[0].strip().upper()
                    val=tmp[1].strip()
                    if var not in var_names:
                        var_list.append([var,val])
                        var_names.append(var)
            else:
                # Append text to labels list
                if len(line)>0:
                    lines+=1
                    tmp=line[-2:]
                    if tmp in ["--","++"]:
                        visible=True
                        is_ts_visible=True
                        if tmp=="--":
                            visible=False
                            is_ts_visible=False
                        line=line[:-2]
                        ts_visible.append([lines,visible])
                    if is_ts_visible and len(line)>ts_text_max:
                        sample=line
                        ts_text_max=len(line)
                    ts_texts.append(line)
    # Assign values for varibles from a list
    for row in var_list:
        if row[0]=="T":
            ts_text_color=parseRGB(row[1])
        elif row[0]=="B":
            ts_rect_color=parseRGB(row[1])
        elif row[0]=="A":
            try:
                ts_rect_alpha=float(row[1])
            except:
                ts_rect_alpha=1.0
        elif row[0]=="S":
            try:
                if int(row[1])==1:
                    tsAlphaText=True
                else:
                    tsAlphaText=False
            except:
                tsAlphaText=False
    # Create sample string with maximum length
    text=sample
    text_width,text_height=getTextInfo(text,font,ts_text_scale)
    ts_text_x,ts_text_y,ts_rect_x0,ts_rect_y0,ts_rect_x1,ts_rect_y1=TextPosition("text",
                                                                                 width,
                                                                                 height,
                                                                                 ts_hspace,
                                                                                 ts_vspace,
                                                                                 text_width,
                                                                                 text_height,
                                                                                 ts_marginal_x,
                                                                                 ts_marginal_y)    
    
if isPTS:
    print("")
    print("PTS mode")
    print("--------")
    # Read PTS values and options
    i=0
    var_lines=4
    var_list=[]
    var_names=[]
    sample=""
    with open(pts_file) as fp:
        for line in fp:
            line=line.strip()
            if len(line)>0:
                pts_values.append(float(line))
    if pathlib.Path(timelabels_ts).exists():
        with open(timelabels_ts) as fp:
            for line in fp:
                line=line.strip()
                i+=1
                if i<=var_lines:
                    # Split line to var,value
                    tmp=line.split(":")                
                    if len(tmp)==2:
                        var=tmp[0].strip().upper()
                        val=tmp[1].strip()
                        if var not in var_names:
                            var_list.append([var,val])
                            var_names.append(var)
    # Assign values for varibles from a list
    for row in var_list:
        if row[0]=="T":
            pts_text_color=parseRGB(row[1])
        elif row[0]=="B":
            pts_rect_color=parseRGB(row[1])
        elif row[0]=="A":
            try:
                pts_rect_alpha=float(row[1])
            except:
                pts_rect_alpha=1.0
        elif row[0]=="S":
            try:
                if int(row[1])==1:
                    ptsAlphaText=True
                else:
                    ptsAlphaText=False
            except:
                ptsAlphaText=False
    last=len(pts_values)
    # Determine auto time scale
    if last>0:
        last-=1
        t=pts_values[last]
        auto_unit,auto_divisor=autounit(t)
        print("Auto unit: "+auto_unit)
        print("Maximum value: "+str(round(t/auto_divisor)))
        acceptAuto=inputYesNo("auto unit","Accept auto unit: "+auto_unit,True)
        if acceptAuto:
            pts_unit=auto_unit
            pts_divisor=auto_divisor
        else:
            pts_unit=inputListValue("Unit",units,auto_unit,"Not a valid unit!",True)
            pts_divisor=divisors[units.index(pts_unit)]
            print("Divisor: "+str(pts_divisor))
            print("Maximum value: "+str(t/pts_divisor))
        pts_decimals=inputValue("decimals",0,10,pts_decimals,"","Decimals is out of range!",True)
        pts_intervalUpdate=inputValue("update PTS interval:",1,files,1,"","Interval is out of range!",True)
        visibleUnit=inputYesNo("visible unit","Show unit",True)
        pts_prefix=input("PTS prefix: ")
        # Calculate maximum integer length
        if pts_decimals>0:
            max_int_len=len(str(int(math.ceil(pts_values[last]/pts_divisor))))
            max_val_len=max_int_len+pts_decimals+1
            f="{:."+str(pts_decimals)+"f}"
        else:
            max_int_len=len(str(int(pts_values[last]/pts_divisor)))
        for v in pts_values:
            tmp=""
            if len(pts_prefix)>0:
                tmp=pts_prefix+" "
            t=round(v/pts_divisor,pts_decimals)
            if pts_decimals==0:
                tmp+=str(int(t)).rjust(max_int_len," ")
            else:
                t=f.format(v/pts_divisor)
                t=t.rjust(max_val_len," ")
                tmp+=t
            if visibleUnit:
                tmp+=" "+pts_unit
            pts_texts.append(tmp)
            # Create sample string with maximum length
        text=pts_texts[last]
        text_width,text_height=getTextInfo(text,font,pts_text_scale)
        pts_text_x,pts_text_y,pts_rect_x0,pts_rect_y0,pts_rect_x1,pts_rect_y1=TextPosition("PTS text",
                                                                                     width,
                                                                                     height,
                                                                                     ts_hspace,
                                                                                     ts_vspace,
                                                                                     text_width,
                                                                                     text_height,
                                                                                     ts_marginal_x,
                                                                                     ts_marginal_y)    
    else:
        print("No PTS data found!")
        
numSeries=[isInterval,isTS,isPTS].count(True)
if numSeries>1:
   isCommonAlpha=inputYesNo("Common alpha for different label types","Enable common alpha",True)
   if isCommonAlpha:
       common_alpha=inputValue("common alpha",0.0,1.0,common_alpha,"","Alpha is out of range!",False)
   print("")
   
i=0
ts_line=0
pts_line=0
frame_overlay=[]
is_ts_visible=True
ts_listsize=len(ts_texts)
pts_listsize=len(pts_texts)
for p in sorted(path.iterdir()):
    suffix=p.suffix.lower()
    if p.is_file() and suffix==ext:    

        # Read image and create a copy
        frame = cv2.imread(p.name)
        frame_cpy = frame.copy()
        
        if isInterval:
            # Generete text from time
            if i % intervalUpdate == 0:
                text=text_prefix+getTimeStr(start,interval,i,isInt)
                if len(unit)>0:
                    text+=" "+unit
            print(p.name+" |I  | "+text)
            # Draw a rectangle
            cv2.rectangle(frame, (rect_x0,rect_y0), (rect_x1,rect_y1), rect_color, cv2.FILLED)
            if isCommonAlpha:
                cv2.putText(frame, text, (text_x,text_y), font, text_scale, text_color, 1, cv2.LINE_AA)
            else:
                if alphaText:
                    cv2.putText(frame, text, (text_x,text_y), font, text_scale, text_color, 1, cv2.LINE_AA)
                frame_overlay=cv2.addWeighted(frame, rect_alpha, frame_cpy,1-rect_alpha, gamma=0) 
                if not alphaText:
                    cv2.putText(frame_overlay, text, (text_x,text_y), font, text_scale, text_color, 1, cv2.LINE_AA)
                if numSeries>1:
                    frame = frame_overlay
                    frame_cpy = frame.copy()

        if isTS and ts_line<ts_listsize:
            ts_text=ts_texts[ts_line]
            ts_line+=1 
            if len(ts_visible)>0 and ts_visible_line<len(ts_visible):
               if ts_line==ts_visible[ts_visible_line][0]:
                   is_ts_visible=ts_visible[ts_visible_line][1]
                   ts_visible_line+=1
            if is_ts_visible:
                # Draw a rectangle
                cv2.rectangle(frame, (ts_rect_x0,ts_rect_y0), (ts_rect_x1,ts_rect_y1), ts_rect_color, cv2.FILLED)
                if isCommonAlpha:
                    cv2.putText(frame, ts_text, (ts_text_x,ts_text_y), font, ts_text_scale, ts_text_color, 1, cv2.LINE_AA)
                else:
                    if tsAlphaText:
                        cv2.putText(frame, ts_text, (ts_text_x,ts_text_y), font, ts_text_scale, ts_text_color, 1, cv2.LINE_AA)
                    frame_overlay=cv2.addWeighted(frame, ts_rect_alpha, frame_cpy,1-ts_rect_alpha, gamma=0) 
                    if not tsAlphaText:
                        cv2.putText(frame_overlay, ts_text, (ts_text_x,ts_text_y), font, ts_text_scale, ts_text_color, 1, cv2.LINE_AA)
                    if numSeries>1:
                        frame = frame_overlay
                        frame_cpy = frame.copy()  
                print(p.name+" |TS | "+ts_text)
            else:
                frame_overlay=frame
                print(p.name+" |TS | ")

        if isPTS and pts_line<pts_listsize:                  
            if i % pts_intervalUpdate == 0:
                pts_text=pts_texts[pts_line]
            pts_line+=1
            # Draw a rectangle
            cv2.rectangle(frame, (pts_rect_x0,pts_rect_y0), (pts_rect_x1,pts_rect_y1), pts_rect_color, cv2.FILLED)
            if isCommonAlpha:
                cv2.putText(frame, pts_text, (pts_text_x,pts_text_y), font, pts_text_scale, pts_text_color, 1, cv2.LINE_AA)
            else:
                if ptsAlphaText:
                    cv2.putText(frame, pts_text, (pts_text_x,pts_text_y), font, pts_text_scale, pts_text_color, 1, cv2.LINE_AA)
                frame_overlay=cv2.addWeighted(frame, pts_rect_alpha, frame_cpy,1-pts_rect_alpha, gamma=0)
                if not ptsAlphaText:
                    cv2.putText(frame_overlay, pts_text, (pts_text_x,pts_text_y), font, pts_text_scale, pts_text_color, 1, cv2.LINE_AA)
            print(p.name+" |PTS| "+pts_text)
        elif isPTS:
            print(p.name+" |PTS| ")
            
        if isCommonAlpha:
            # Process common alpha texts
            frame_overlay=cv2.addWeighted(frame, ts_rect_alpha, frame_cpy,1-ts_rect_alpha, gamma=0) 

        tmp=dst+"/"
        if pngMode:
            tmp+=p.stem+".png"
        else:
            tmp+=p.name
        cv2.imwrite(tmp,frame_overlay)
        i+=1
cv2.destroyAllWindows()
