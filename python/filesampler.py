#!/usr/bin/python3

"""
Created on 2020-11-22
@author: Kim Miikki
"""

import argparse
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
filter_start=""
isFilter=False
isBareNumber=False
isConsequentNumbering=False
isDigits=False
fname=""
stem=""
numinverse=0
numsamples=0
filedigits=0
mindigits=0
auto_digits=0
digits=0
file_list=[]

def option_str(option,selected,end="\n"):
    s=option+": "
    if selected:
        s+="Yes"
    else:
        s+="No"
    s+=end
    return s

parser=argparse.ArgumentParser()
parser.add_argument("-b", action="store_true", help="bare number as file name stem")
parser.add_argument("-n", action="store_true", help="consequent numbering of sampled files")
parser.add_argument("-d", type=int, help="number of digits in sampled files (override auto digits)", required=False)
parser.add_argument("-f", nargs=1, type=str, help="filter start string",required=False)
args = parser.parse_args()

arguments=""
if args.b:
    isBareNumber=True
    arguments+="-b"
if args.n:
    isConsequentNumbering=True
    if len(arguments)>0:
        arguments+=" "
    arguments+="-n"
if args.d != None:
    digits=int(args.d)
    if digits<1:
        digits=1
    isDigits=True
    if len(arguments)>0:
        arguments+=" "
    arguments+="-d "+str(digits)
if args.f != None:
    filter_start=args.f[0]
    isFilter=True
    if len(arguments)>0:
        arguments+=" "
    arguments+="-f "+filter_start

print("Filesampler")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

if isFilter:
    print("File start pass filter: "+filter_start)
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
        if isFilter:
            if fname.find(filter_start)!=0:
                continue
        file_list.append(fname)

"""
Intervals:

123456    interval comment
111111    1        file sampling not required
101010    2        minimum sampling interval
100100    3	
100010    4
100001    5
100000(1) 6
"""

files=len(file_list)
#files_half=files // 2
max_interval=files

if files<2:
    print("")
    print("Files found: "+str(files))
    print("At least 2 files are required for sampling!")
    print("")
    sys.exit(0)

## Enable a sampling range if files > 2
if files>2:
    interval_mode=inputYesNo("Interval","Use interval",True)
    if interval_mode:
        interval=inputValue("interval:",2,max_interval,2,"","Interval is out of range!",True)
    else:
        # Calculate minumum %
        pmin=round(1/max_interval*100,2)
        pmax=50
        percent=inputValue("sample percent:",pmin,pmax,pmax,"%","Percent is out of range!",False)
        interval=int(round(100/percent,0))
        print("Calculated interval: "+str(interval))
else:
    interval=2
    print("Interval set to 2")

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

stem=file_list[0]
stem=os.path.splitext(stem)[0]

# Calculate auto_digits and extrac stem without numbering
if isBareNumber or isConsequentNumbering or isDigits:
    for c in reversed(stem):
        if c.isdigit():
            filedigits+=1
        else:
            break
    if filedigits>0:
        stem=stem[:-filedigits]
    numsamples=1+int((files-1)/interval)
    numinverse=files-numsamples
    if inverse:
        mindigits=len(str(numinverse))
    else:
        mindigits=len(str(numsamples))
    if filedigits<mindigits:
        filedigits=mindigits
    auto_digits=filedigits

if isDigits:
    if digits<auto_digits:
        print("\nWarning: Option digits is smaller than sampled files digits ("+
              str(digits)+" < "+str(auto_digits)+")")
else:
    digits=auto_digits

# Create a log file
file=open("filesampler.log","w")
file.write("filesampler\n\n")
file.write("Source directory: "+curdir+"\n")
dst=curdir
if dst!="/":
    dst+="/"
dst+=sample_dir
file.write("Sample directory: "+dst+"\n\n")
if len(arguments)>0:
    file.write("Arguments: "+arguments+"\n\n")
file.write("Options:\n")
if isFilter:
    file.write("File start pass filter : "+filter_start+"\n")
file.write(option_str("Bare numbering of files",isBareNumber))
file.write(option_str("Consequent numbering   ",isConsequentNumbering))
file.write("Digits: "+str(digits)+"\n")
file.write(option_str("Normal sort mode",normal_mode))
file.write(option_str("List all files",ext_all))
if not ext_all:
    file.write("Extension for files included in search: "+ext+"\n")
file.write(option_str("Interval mode",interval_mode))
if interval_mode:
    file.write("Interval: "+str(interval)+"\n")
else:
    file.write("Sample percent     : "+str(percent)+" %\n")
    file.write("Calculated interval: "+str(interval)+"\n")
file.write(option_str("Inverse sampling",inverse))

t1=datetime.now()
i=0
s=0
for f in file_list:
    sample=False
    r=i % interval
    i+=1
    if inverse and r>0:
        sample=True
    elif not inverse and r==0:
        sample=True
    if sample:
        newfile=""
        if isConsequentNumbering:
            s+=1
            if len(str(s))>digits:
                print("Skip: "+f+", digits exceeded")
                continue
            if not isBareNumber:
                newfile=stem
            newfile+=str(s).rjust(digits,"0")
            suffix=os.path.splitext(f)[1]
            if len(suffix)>0:
                newfile+=suffix
        else:
            if not (isDigits or isBareNumber):
                newfile=f
            else:
                stem=os.path.splitext(f)[0]
                try:                
                    number=int(stem[-auto_digits:])
                except:
                    print("Skip: "+f+", '"+stem[-auto_digits:]+"' is not a valid number")
                    continue
                if len(str(number))>digits:
                    print("Skip: "+f+", digits exceeded")
                    continue
                stem=stem[:-auto_digits]
                if not isBareNumber:
                    newfile=stem
                newfile+=str(number).rjust(digits,"0")
                suffix=os.path.splitext(f)[1]
                if len(suffix)>0:
                    newfile+=suffix
        sample_files+=1
        shutil.copy2(f,sample_dir+"/"+newfile)

t2=datetime.now()

file.write("\nFiles sampled: "+str(sample_files)+"\n")
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
print("\nFiles sampled: "+str(sample_files))
print("Time elapsed: "+str(t2-t1))
