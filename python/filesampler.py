#!/usr/bin/python3

"""
Created on 2020-11-17
@author: Kim Miikki
"""

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime
from rpi.inputs2 import *

t1=0
t2=0
files=0
sample_files=0
sample_dir="files"
ext=""
fname=""
file_list=[]

print("Filesampler")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

normal_mode=inputYesNo("Normal sorting","Normal sort mode",True)
ext_all=inputYesNo("Select all","List all files",True)

if not ext_all:
    while True:
        try:
            ext=input("Extension for files included in search? ")
            if ext=="":
                print("All files included in search")
                ext_all=True
                break
            ext=ext.lower()
            if ext[0]!=".":
                ext="."+ext
            if ext.count(".")>1 or len(ext)==1:
                raise Exception("invalid extension")
            break
        except:
            print("Invalid extension!")  

try:
  if not os.path.exists(sample_dir):
    os.mkdir(sample_dir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)
  
for p in sorted(path.iterdir(),reverse=not normal_mode):
  suffix=p.suffix.lower()
  if p.is_file():
    if suffix==ext or ext_all:
        fname=p.name
        file_list.append(fname)
files=len(file_list)
files_half=files // 2

if files<2:
    print("")
    print("Files found: "+str(files))
    print("At least 2 files are required for sampling!")
    print("")
    sys.exit(0)

if files>2:
    interval_mode=inputYesNo("Interval","Use interval",True)
    if interval_mode:
        interval=inputValue("interval:",2,files_half,2,"","Interval is out of range!",True)
    else:
        # Calculate minumum %
        pmin=round(2/files*100,2)
        pmax=50
        percent=inputValue("sample percent:",pmin,pmax,pmax,"%","Percent is out of range!",True)
        interval=int(100/percent)
        print("Calculated interval: "+str(interval))
else:
    interval=2

inverse=inputYesNo("Inverse mode","Inverse sampling",False)

"""
include or exclude mode:
interval=5

exclude:
1,2,3,4,5,6 =>
1,-,-,-,-,6

include (inverse):
1,2,3,4,5,6,7,8,9,10,11,12 =>
-,2,3,4,5,-,7,8,9,10, -,12
"""

t1=datetime.now()
i=0
for f in file_list:
    sample=False
    r=i % interval
    if inverse and r>0:
        sample=True
    elif not inverse and r==0:
        sample=True
    if sample:            
        shutil.copy2(f,sample_dir+"/"+f)
        #print(i,i % interval,f)
        sample_files+=1
    i+=1

t2=datetime.now()

print("\nFiles sampled: "+str(sample_files))
print("Time elapsed: "+str(t2-t1))
