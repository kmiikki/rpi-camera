#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 14 07:17:48 2021

@author: Kim Miikki
"""

import cv2
#import numpy as np
import os
import sys
from pathlib import Path
from rpi.inputs2 import *

# pipdir and outdir must be different than current directory
imgdir="img"
pipdir="pip"
outdir="master"
ext=""
imgfiles=0
pipfiles=0
imgdigits=0
pipdigits=0

default_imgext="jpg"
default_pipext="png"
default_masterext="png"
imgext=""
pipext=""
masterext=""

img_width=0
img_height=0
pip_width=0
pip_height=0

# imglist format: [number,img_name,pip_name]
# image_name=baseN.ext, where N=1,2,3,... ; fixed digits with leading zeros
# pip_name  =baseM.ext, where M=1,2,3,... ; fixed digits with leading zeros
imglist=[]

def ask_ext(image_type="",default="png",searchdir=True):
    if image_type!="":
        image_type+=" "
    askExt=True
    ext_text="Extension for "+image_type+"images "
    if searchdir:
        ext_text+="included in search "
    ext_text+="(Default "+default+": <ENTER>)? "
    while askExt:
        
        ext=input(ext_text)
        if ext=="":
            ext=default
            print("Default selected: "+ext)
        if ext=="" or ext=="." or ext.count(".")>1:
            print("Invalid extension!")
            continue
        if len(ext)<1:
            print("Extension too short!")
            continue
        if ext.find(".")<0:
            ext="."+ext
            askExt=False
        elif ext.find(".")==0:
            askExt=False
        else:
            print("Invalid extension!")
    return ext

def get_imgdigits(name,extension):
    errors=[]
    digits=0
    if len(name)<=len(extension):
        errors.append("No file stem")
    else:
        name=name[:-len(extension)]
        l=len(name)
        i=l-1
        while(i>=0):
            if not name[i].isdigit():
                if digits==0:
                    errors.append("No digits in stem")
                break
            digits+=1
            i-=1
    return digits,errors

def get_pipXY(position,img_rect,pip_rect):   
    """
    Position string:
    TL, TC, TR = Top Left    | Top Center    | Top Left
    CL, CC, CR = Center Left | Center Center | Center Left
    BL, BC, BR = Bottom Left | Bottom Center | Bottom Left
    
    img_rect=(x0,y0,x1,y0)
    return pip_rect
    
    """
    width=img_rect[2]-img_rect[0]+1
    height=img_rect[3]-img_rect[1]+1
    width_pip=pip_rect[2]-pip_rect[0]
    height_pip=pip_rect[3]-pip_rect[1]

    x0=-1
    y0=-1
    x1=-1
    y1=-1    
    pip_rect=(-1,-1,-1,-1)

    if len(position)!=2 or type(position)!=str:
        return pip_rect
    position=position.strip()
    posy=position[0].lower()
    posx=position[1].lower()
    if not ((posy in ["t","c","b"]) and posx in ["l","c","r"]):
        return pip_rect
    
    # Validate img_rect
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
    
    # Calculate new PIP coordinates
    if posy=="t":
        y0=img_rect[1]
        y1=img_rect[1]+height_pip
    elif posy=="c":
        y0=(height-height_pip)/2
        y1=(height+height_pip)/2
    elif posy=="b":
        y0=img_rect[3]-height_pip
        y1=img_rect[3]
    
    if posx=="l":
        x0=img_rect[0]
        x1=img_rect[0]+width_pip
    elif posx=="c":
        x0=(width-width_pip)/2
        x1=(width+width_pip)/2
    elif posx=="r":
        x0=img_rect[2]-width_pip
        x1=img_rect[2]
   
    x0=int(x0)
    x1=int(x1)
    y0=int(y0)
    y1=int(y1)
    pip_rect=(x0,y0,x1,y1) 
    return pip_rect

print("PIPgen 1.0, (c) Kim Miikki 2021")

curdir=os.getcwd()
path=Path(curdir)
print("")
print("Current directory:")
print(curdir)

try:
  if not os.path.exists(outdir):
    os.mkdir(outdir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

if imgdir!="":
    imgdir=str(path)+"/"+imgdir+"/"
else:
    imgdir=str(path)+"/"
pipdir=str(path)+"/"+pipdir+"/"
outdir=str(path)+"/"+outdir+"/"

# Test if imgdir and pipdir are present
is_imgdir=os.path.exists(imgdir)
is_pipdir=os.path.exists(pipdir)
if False in [is_imgdir,is_pipdir]:
    print("\nMissing director",end="")
    if not True in [is_imgdir,is_pipdir]:
        print("ies:")
    else:
        print("y:")
    if not is_imgdir:
        print(imgdir)
    if not is_pipdir:
        print(pipdir)
    sys.exit(0)

print("")
imgext=ask_ext("BASE",default_imgext)
pipext=ask_ext("PIP",default_pipext)
masterext=ask_ext("MASTER",default_masterext,False)
        
# Count images
image=0
imagelen=0
imagestem=""
extlen=len(imgext)
errorlist=[]
for p in sorted(Path(imgdir).iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    if suffix==imgext:
        image+=1
        fname=p.name
        if image==1:
            imagelen=len(fname)
            imgdigits,errorlist=get_imgdigits(fname,imgext)
            if len(errorlist)==0:
                imagestem=fname[:-extlen-imgdigits]
                imglist.append([image,fname,""])
                frame=cv2.imread(imgdir+fname)
                img_height,img_width,channels=frame.shape
        if image>1:
            if len(fname)!=imagelen:
                errorlist.append("Incorrect file length: "+fname)
                continue
            else:
                try:
                  n=int(fname[imagelen-extlen-imgdigits:-extlen])
                except:
                    errorlist.append("Invalid file number  : "+fname)
                    continue
            if fname[:-extlen-imgdigits]==imagestem:
                if n==image:
                    imglist.append([image,fname,""])
                else:
                    errorlist.append("Incorrect file number: "+str(n)+" != "+str(image)+", "+fname)
                #print(image,n,fname)
            else:
                errorlist.append("Different file stem: "+fname[:-extlen-imgdigits]+", "+fname)
        
if len(imglist)<image:
    errorlist.append("File numbering is not consequent")

if len(errorlist)>0:
    print("\nUnable to continue:")
    for row in errorlist:
        print(row)
    sys.exit(0)
    
# Add PIPs to imglist
pip_image=0
pip_imagelen=0
pip_imagestem=""
extlen=len(pipext)
for p in sorted(Path(pipdir).iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    if suffix==pipext:
        pip_image+=1
        fname=p.name
        if pip_image==1:
            pip_imagelen=len(fname)
            pip_imgdigits,errorlist=get_imgdigits(fname,pipext)
            if len(errorlist)==0:
                pip_imagestem=fname[:-extlen-pip_imgdigits]
                frame=cv2.imread(pipdir+fname)
                pip_height,pip_width,channels=frame.shape
        try:
            n=int(fname[pip_imagelen-extlen-pip_imgdigits:-extlen])
            if n>=0 and n<=image:
                imglist[n-1][2]=fname
        except:
            print("Skip: "+fname)

# PIP poisition selection:
print("")
print("Picture In Picture")
print("------------------")
print("")
print("    L C R")
print("  +-------+")
print("T | 1 2 3 |")
print("C | 4 5 6 |")
print("B | 7 8 9 |")
print("  +-------+")
pos=inputListValue("PIP position",listValues=[1,2,3,4,5,6,7,8,9],default=9,listErrorText="Not a valid value!",strType=False)
postr=""
if int((pos-1)/3)==0:
    postr="t"
elif int((pos-1)/3)==1:
    postr="c"
elif int((pos-1)/3)==2:
    postr="b"
if (pos-1)%3==0:
    postr+="l"
elif (pos-1)%3==1:
    postr+="c"
elif (pos-1)%3==2:
    postr+="r"

img_rect=(0,0,img_width-1,img_height-1)
pip_rect=(0,0,pip_width-1,pip_height-1)
pip=get_pipXY(postr,img_rect,pip_rect)
x0=pip[0]
y0=pip[1]

i=0
maxdigits=len(str(len(imglist)))
if len(imglist)>0:
    print("\nProcessing:")
for frame in imglist:
    i+=1
    print(str(i).zfill(maxdigits)+"/"+str(len(imglist)))
    if frame[2]!="":
        base_frame=cv2.imread(imgdir+frame[1])
        pip_frame =cv2.imread(pipdir+frame[2])
        try:
            base_frame[y0:y0+pip_height,x0:x0+pip_width]=pip_frame
            cv2.imwrite(outdir+frame[1],base_frame)
        except:
            print("Skip: "+frame[2])
            shutil.copy2(imgdir+frame[1],outdir+frame[2])
    else:
        shutil.copy2(imgdir+frame[1],outdir+frame[2])