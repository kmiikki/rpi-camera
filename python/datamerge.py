#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 24 13:56:55 2021

@author: Kim Miikki

Usage:
datamerge.py file1 file2 file3 ...

"""
import os
import sys
from pathlib import Path

outfile="xydata.csv"
delimiter=","

print("Combine multiple files to one file")
print("")
curdir=os.getcwd()
path=Path(curdir)

files=len(sys.argv)-1
if files<2:
    print("At least two files are required for data merging")
    sys.exit(0)

# Test which files exists
existing_files=[]
for i in range(1,files+1):
    fname=sys.argv[i]
    if os.path.isfile(fname):
        try:
            with open(fname,"r") as file:
                pass
            existing_files.append(fname)
        except:
            continue

missing=input("Missing data string (Enter = None): ")

# Open all input files
filelist=[]
for fname in existing_files:
    filelist.append(open(fname,"r"))

# Open outfile for writing
try:
    ofile=open(outfile,"w")
except:
    print("Unable to open: "+outfile)
    sys.exit(0)

file_count=len(existing_files)
listEnd=False
missing_values=0
rows=0
while True:
    s=""
    for i in range(0,file_count):
        row=filelist[i].readline().strip()
        if i==0 and not row:
            listEnd=True
            break
        if not row:
            missing_values+=1
            row=missing
        s+=row
        if i<file_count-1:
            s+=delimiter
    ofile.write(s+"\n")
    if listEnd:
        break
    rows+=1

# Close all files
ofile.close()
for f in filelist:
    f.close()

print("Rows merged    : "+str(rows))
print("Missing values : "+str(missing_values))
print("Merge file name: "+outfile)