#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 07:04:00 2021

@author: Kim Miikki
"""
import os
from pathlib import Path
from rpi.inputs2 import *

start_mtime=0
first_mtime=0
header="# timecode format v2"
pts_default="extracted"
pts_name=""
times=[]

start_time=0
min_start=0           # unit s:  1 µs
max_start=2592000     # unit s: 30 d
default_start=0

interval=0
min_interval=0.000001 # unit s:  1 µs
max_interval=2592000  # unit s: 30 d
default_int=1

def get_time(start_time,first_mtime,mtime):
    return round(1000*(start_time+(mtime-first_mtime)),3)

def get_time_interval(start_time,interval,count):
    return round(1000*(start_time+interval*(count-1)),3)

# Get current directory
print("ptsextract")
print("")
curdir=os.getcwd()
path=Path(curdir)
print("Current directory:")
print(curdir)
print("")

start_time=inputValue("start time",min_start,max_start,default_start,"s","Value out of range!",False)
isMtime=inputYesNo("mtime mode","Use file mtime instead of interval",True)
if not isMtime:
    interval=inputValue("interval",min_interval,max_interval,1,"s","Value out of range!",False)

l=0
while l==0:
    ext=input("File extension: ")
    ext=ext.strip()
    if len(ext)==0:
        print("Enter extension!")
        continue
    elif len(ext)==1 and ext.isalnum()==False:
        print("Invalid extension!")
        continue
    l=len(ext)
    if ext[0]!=".":
        ext="."+ext
       
pts_name=os.path.basename(curdir)
if len(pts_name)==0:
    pts_name=pts_default
pts_name+=".pts"

times.append(header)
file=0
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file() and p.suffix==ext:
    file+=1
    fname=p.name
    mtime=os.path.getmtime(fname)
    if file==1:
       first_mtime=mtime
    if isMtime:
        t=get_time(start_time,first_mtime,mtime)
    else:
        t=get_time_interval(start_time,interval,file)
    print(fname,'{:.3f}'.format(t))
    times.append('{:.3f}'.format(t))

if file>0:
    try:
        with open(pts_name, "w") as f: 
            for row in times:
                f.write(row+"\n")
        print("")
        print(pts_name+" created with "+str(file)+" time stamps")
    except:
        print("Unable to create: "+pts_name)
else:
    print("Files not found!\n")