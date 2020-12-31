#!/usr/bin/python3
# (C) Kim Miikki 2020

import argparse
import csv
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import cv2
from datetime import datetime

t1=0
t2=0
fname=""
pictures=0
results=[]
rgb=[]
files=[]

ask_unit=False
t=0.0
start=0.0
interval=1.0
decimals=10
decimals_time=3
unit=""
delimiter=","
isStart=False
isInterval=False
isUnit=False
scale_y=False
file_mode=False
unit_mode=False
display_mode=False
new_times=False

adir="rgb"
outname="rgb.csv"
testname=".testfile.tmp"

parser=argparse.ArgumentParser()
parser.add_argument("-f", action="store_true", help="file mode: read rgb.csv")
parser.add_argument('-s',type=float,help="start time for first frame as float",required=False)
parser.add_argument('-i',type=float,help="interval between two frames as float",required=False)
parser.add_argument("-u", nargs="*", type=str,help="x unit string",required=False)
parser.add_argument("-y", action="store_true", help="auto scale y axis")
parser.add_argument("-d", action="store_true", help="display figures")
args = parser.parse_args()

if args.s != None:
    start=float(args.s)
    isStart=True
    unit_mode=True

if args.i != None:
    interval=float(args.i)
    if interval==0:
        interval=1
    isInterval=True
    unit_mode=True

# Ask for unit if args.u=="-u"
if args.u != None:
    if len(args.u)>0:
        unit=args.u[0]
    else:
        ask_unit=True
    isUnit=True
    unit_mode=True

if args.y:
    scale_y=True

if args.d:
    display_mode=True

if args.f:
    file_mode=True
    if unit_mode:
        new_times=True

print("RGBmean 1.0, (c) Kim Miikki 2020")

curdir=os.getcwd()
path=Path(curdir)
adir=str(path)+"/"+adir+"/"

if (not file_mode) or new_times:
    try:
      if not os.path.exists(adir):
        os.mkdir(adir)
    except OSError:
      print("Unable to create a directory under following path:\n"+curdir)
      print("Program is terminated.")
      print("")
      sys.exit(1)
    
    # Test if a RGB file can be created
    try:
      file=open(adir+outname,"w")
    except OSError:
      print("Unable to create a RGB file in following directory:\n"+curdir)
      print("Program is terminated.")
      print("")
      sys.exit(1)
else:
    try:
      file=open(testname,"w")
    except OSError:
      print("Unable to create a file in following directory:\n"+curdir)
      print("Program is terminated.")
      print("")
      sys.exit(1)
    else:
      file.close()
      os.remove(testname)

if isStart or isInterval or isUnit:
    if not isStart:
        start=float(input("Start time: "))
    if not isInterval:
        interval=0
        while interval<=0:
            interval=float(input("Interval between two frames: "))
    if (not isUnit) or ask_unit:
        unit=input("X axis unit: ")
else:
    start=1.0
    interval=1.0

if start.is_integer():
    t=int(start)
else:
    t=float(start)
if interval.is_integer():
    interval=int(interval)

t1=datetime.now()
if not file_mode:
    for p in sorted(path.iterdir()):
      suffix=p.suffix.lower()
      if p.is_file() and (suffix==".png" or suffix==".jpg"):
        fname=p.name
        img=cv2.imread(str(path)+"/"+fname)
        h,w,ch=img.shape
        if ch==1:
          print(fname+" has only 1 channel. Skipping file.")
          continue                    
        rgb_means=np.array(img).mean(axis=(0,1))
        pictures+=1
        if pictures==1:
          print("\nAnalyzing:")

        r_avg=round(rgb_means[2],decimals)
        g_avg=round(rgb_means[1],decimals)
        b_avg=round(rgb_means[0],decimals)
        bw_avg=round((r_avg+g_avg+b_avg)/3,decimals)
        files.append(fname)
        t=start+(pictures-1)*interval
        t=round(t,decimals_time)
        if unit_mode:
            tmp=str(t)
        else:
            tmp=str(pictures)
        if unit != "":
            tmp+=" "
            tmp+=unit
        tmp+=": "
        tmp+=fname+": "+str(w)+"x"+str(h)
        print(tmp)
        if unit_mode:
            rgb.append([t,bw_avg,r_avg,g_avg,b_avg])
        else:
            rgb.append([pictures,bw_avg,r_avg,g_avg,b_avg])
else:
    # File mode: Read RGB.csv file
    try:
        file_rgb=open(outname,"r")
    except OSError:
        print("Unable to open "+outname+" in following directory:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)
    else:
        csv_reader=csv.reader(file_rgb,delimiter=delimiter)
        header=next(csv_reader)
        columns=6
        isOk=True
        if len(header)!=columns:
            isOk=False
        # Parse header
        if isOk:
            if header[1]=="number":
                unit=""
                unit_mode=False
            elif not new_times:
                # Unit template: time [h] -> h
                unit=header[1]
                if len(unit)>2:
                    unit=unit[:-1]
                    pos=unit.rfind("[")
                    if pos>0:
                        unit=unit[pos+1:]
                    else:
                        unit=""
                    unit_mode=True
                else:
                    unit_mode=True
        # Read RGB values
        if isOk:
            for row in csv_reader:
                # print(row)
                if len(row)!=columns:
                    print("Invalid line: "+str(row))
                    isOk=False
                    continue
                if unit_mode:
                    if not new_times:
                        t=float(row[1])
                    else:
                        t=start+pictures*interval
                        t=round(t,decimals_time)
                else:
                    t=int(row[1])
                rgb.append([t,float(row[2]),float(row[3]),float(row[4]),float(row[5])])
                if new_times:
                    files.append(row[0])
                pictures+=1
        file_rgb.close()
        if not new_times:
            adir=""
        if not isOk:
            print("")
            print("Invalid "+outname+" file. Program is terminated.")
            print("")
            sys.exit(1)

t2=datetime.now()

if len(rgb)==0:
    print("")
    print("No pictures or RGB data. Program is terminated.")
    print("")
    sys.exit(1)
            
matrix=np.array(rgb,dtype="object")
matrix=matrix.T
rgb_mins=[matrix[2].min(),matrix[3].min(),matrix[4].min()]
rgb_maxs=[matrix[2].max(),matrix[3].max(),matrix[4].max()]
bw_min=matrix[1].min()
bw_max=matrix[1].max()

if pictures>1:
    # Plot RGB means
    fig=plt.figure()
    if not unit_mode:
        ax = plt.figure().gca()
        ax.xaxis.get_major_locator().set_params(integer=True)
    plt.xlim(matrix[0].min(),matrix[0].max())
    if scale_y:
        plt.ylim(min(rgb_mins),max(rgb_maxs))
    else:
        plt.ylim(0,255)
    plt.plot(matrix[0],matrix[2],color="r")
    plt.plot(matrix[0],matrix[3],color="g")
    plt.plot(matrix[0],matrix[4],color="b")
    if unit_mode:
        plt.xlabel("Time ["+unit+"]")
    else:
        plt.xlabel("Image")
    plt.ylabel("RGB mean")
    plt.savefig(adir+"RGB-mean.png",dpi=300)
    if display_mode:
        plt.show()
    plt.close(fig)
    
    # Plot BW means in x direction
    fig=plt.figure()
    if not unit_mode:
        ax = plt.figure().gca()
        ax.xaxis.get_major_locator().set_params(integer=True)    
    plt.xlim(matrix[0].min(),matrix[0].max())
    if scale_y:
        plt.ylim(bw_min,bw_max)
    else:
        plt.ylim(0,255)
    plt.plot(matrix[0],matrix[1],color="k")
    if unit_mode:
        plt.xlabel("Time ["+unit+"]")
    else:
        plt.xlabel("Image")
    plt.ylabel("BW mean")
    plt.savefig(adir+"BW-mean.png",dpi=300)
    if display_mode:
        plt.show()
    plt.close(fig)

print("")
if (not file_mode) or new_times:
    header="picture_name"+delimiter
    if unit_mode:
        header+="time "+"["+unit+"]"+delimiter
    else:
       header+="number"+delimiter
    header+="bw"+delimiter
    header+="red"+delimiter
    header+="green"+delimiter
    header+="blue"
    file.write(header+"\n")
    columns=len(rgb[0])
    f=0
    for row in rgb:
      file.write(files[f]+delimiter)
      f+=1
      s=""
      for i in range(0,columns):
        s+=str(row[i])
        if i<columns-1:
          s+=delimiter
      file.write(s+"\n")
    file.close()
    
    print("Pictures analyzed: "+str(pictures))
else:
    print("Rows analyzed: "+str(pictures))
print("Time elapsed: "+str(t2-t1))
