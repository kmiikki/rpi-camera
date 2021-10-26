#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 25 19:46:51 2021

@author: Kim Miikki

Spectrometer:
Ocean Insight Flame UV-VIS Spectrometer
"""

import argparse
import os
import pandas as pd
import sys
from pathlib import Path

ylabel="Intensity (counts)"
xlabel="Wavelength (nm)"
data_dir="data"
file_format="ASCII (with header data)"

in_files=[]
in_count=0
filter_start=""
ext=".txt"

parser=argparse.ArgumentParser()
parser.add_argument("-f", nargs=1, type=str, help="filename start string",required=False)
args = parser.parse_args()

if args.f != None:
    filter_start=args.f[0]

print("Ocean spectrometer spectra to CSV files")
print("File format: ",end="")
print(file_format)

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

while filter_start=="":
    try:
        tmp=input("Filename start pass filter (Default=NONE: <Enter>): ")
        if tmp=="":
            print("All *"+ext+" included in search")
            break
        filter_start=tmp
        break
    except:
        print("Not a valid string.")
        continue

# Create a list of files
# Template:
# fname.split(match)
# ['20211021_FLMT044961', '21', '122.txt']
match="__"
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    if suffix==ext:
        fname=p.name
        if fname.find(filter_start)!=0:
            continue            
        tmp=fname.split(match)
        if len(tmp) != 3:
            continue
        order=int(tmp[1])
        in_files.append([fname,order])
in_count=len(in_files)

if in_count==0:
    print("No data files found!")
    sys.exit(0)

try:
  if not os.path.exists(data_dir):
    os.mkdir(data_dir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# Sort files by "Order"
df=pd.DataFrame(in_files,columns = ["Name", "Order"])
df=df.sort_values("Order")
in_filtered=in_filtered=df["Name"]

# Parse files and write data files to the subdirectory
digits=len(str(in_count))
i=0

# Find the spectral data start string
# Template:
# >>>>>Begin Spectral Data<<<<<
match=">>>>>Begin Spectral Data<<<<<"
separator="\t"

print("")
print("Data parser started:")
for name in in_filtered:
    with open(name, 'r') as f:
        lines = [line.strip() for line in f]
    new_name=str(i).rjust(digits,"0")+"-"+name[:-4]+".csv"
    try:
        idx=lines.index(match)
    except:
        print("! "+name+" not processed (no match).")
    print(new_name)
    idx+=1
    f = open(data_dir+"/"+new_name,"w")
    f.write(xlabel+","+ylabel+"\n")
    while idx<len(lines):
        row=lines[idx].split(separator)
        f.write(row[0]+","+row[1]+"\n")
        idx+=1
    f.close()
    i+=1
