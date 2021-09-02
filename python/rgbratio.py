#!/usr/bin/python3
# (C) Kim Miikki 2021

import argparse
import csv
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

yaxis_label_rgb="RGB/RGBref"
yaxis_label_bw="GRAY/GRAYref"
xaxis_label="Number"
t1=0
t2=0

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
firstchar_cap=True
fileTime=True
replaceBrackets=True # [] -> ()
linew_min=0.1
linew_max=2.0
linew_default=1.0
linew=linew_default
grid=True

rgb_in="rgb.csv"
rgbref_in="rgbref.csv"
adir="rgb"
outname="rgbratio.csv"

parser=argparse.ArgumentParser()
parser.add_argument("RGB")
parser.add_argument("RGBref")
parser.add_argument('-s',type=float,help="start time for first frame as float",required=False)
parser.add_argument('-i',type=float,help="interval between two frames as float",required=False)
parser.add_argument("-u", nargs="*", type=str,help="x unit string",required=False)
parser.add_argument('-w',type=float,help="line width "+str(linew_min)+"-"+str(linew_max),required=False)
parser.add_argument("-n", action="store_true", help="Do not draw grids")
parser.add_argument("-y", action="store_true", help="auto scale y-axis")
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

if args.w != None:
    linew=float(args.w)
    if linew<linew_min or linew>linew_max:
        linew=linew_default

if args.n:
    grid=False

if args.y:
    scale_y=True

rgb_in=args.RGB
rgb_ref=args.RGBref

# Add string to the analysis dir name: rgb_TEXT.csv => TEXT => rgb-TXT (dir name)
tmp=""
dotpos=rgb_in.rfind(".")
if dotpos>=0:
    tmp=rgb_in[:dotpos]
rgbpos=tmp.find("rgb")
if rgbpos==0:
    tmp=tmp[len("rgb"):]
if len(tmp)>0:
    if not tmp[0].isalnum():
        tmp=tmp[1:]
if len(tmp)>0:
    adir=adir+"-"+tmp

print("RGBratio 1.0, (c) Kim Miikki 2021")

curdir=os.getcwd()
path=Path(curdir)
adir=str(path)+"/"+adir+"/"

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
  outfile=open(adir+outname,"w")
except OSError:
  print("Unable to create a RGB file in following directory:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

if True in [isStart,isInterval,isUnit]:
    if not isStart:
        start=float(input("Start time: "))
    if not isInterval:
        interval=0
        while interval<=0:
            interval=float(input("Interval between two frames: "))
    if (not isUnit) or ask_unit:
        unit=input("X axis unit: ")
    fileTime=False
else:
    start=1.0
    interval=1.0

if start.is_integer():
    t=int(start)
else:
    t=float(start)
if interval.is_integer():
    interval=int(interval)
else:
    interval=float(interval)

# Read RGB data
rgb_data=[]
try:
    with open(rgb_in,"r") as reader_obj:
        csv_reader=csv.reader(reader_obj)
        header_rgb=next(csv_reader)
        for row in csv_reader:
            rgb_data.append(list(map(float,row[1:])))
            #print(row)
except OSError:
    print("Unable to open "+rgb_in+" in following directory:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)    

# Read RGBref data
rgb_ref_data=[]
names=[]
try:
    with open(rgb_ref,"r") as reader_obj:
        csv_reader=csv.reader(reader_obj)
        header_rgb=next(csv_reader)
        if fileTime:
            xaxis_label=header_rgb[1]
            if firstchar_cap:
                xaxis_label=xaxis_label[0].upper()+xaxis_label[1:]
            if replaceBrackets:
                xaxis_label=xaxis_label.replace("[","(")
                xaxis_label=xaxis_label.replace("]",")")
        for row in csv_reader:
            rgb_ref_data.append(list(map(float,row[1:])))
            names.append(row[0])
            #print(row)
except OSError:
    print("Unable to open "+rgb_ref+" in following directory:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)   

pictures=len(rgb_data)

arr1=np.array(rgb_data)
arr2=np.array(rgb_ref_data)

arr1=arr1.T
arr2=arr2.T

if fileTime:
    xs=arr2[0]
else:
    xs=np.linspace(start,start+interval*(pictures-1),num=pictures)
ratios=arr1[1:]/arr2[1:]
     
rgb_mins=[ratios[1].min(),ratios[2].min(),ratios[3].min()]
rgb_maxs=[ratios[1].max(),ratios[2].max(),ratios[3].max()]
bw_min=ratios[0].min()
bw_max=ratios[0].max()

if pictures>1:
    # Plot RGB mean ratios
    fig=plt.figure()
    plt.xlim(min(xs),max(xs))
    if scale_y:
        plt.ylim(min(rgb_mins),max(rgb_maxs))
    plt.plot(xs,ratios[1],color="r",linewidth=linew)
    plt.plot(xs,ratios[2],color="g",linewidth=linew)
    plt.plot(xs,ratios[3],color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(yaxis_label_rgb)
    if grid:
        plt.grid()
    plt.savefig(adir+"RGB-ratio.png",dpi=300)
    plt.close(fig)
    
    # Plot BW mean ratios
    fig=plt.figure()
    plt.xlim(min(xs),max(xs))
    if scale_y:
        plt.ylim(bw_min,bw_max)
    plt.plot(xs,ratios[0],color="k",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(yaxis_label_bw)
    if grid:
        plt.grid()
    plt.savefig(adir+"GRAY-ratio.png",dpi=300)
    plt.close(fig)
elif pictures==1:
    print("RGB/RGBref : ",end="")
    print(str(ratios[1])+","+str(ratios[2])+","+str(ratios[3]))
    print("GRAY/GRAYref : ",end="")
    print(str(ratios[0]))

if pictures>0:    
    # Save rgbratio.csv 
    header="picture_name"+delimiter
    header+=xaxis_label+delimiter
    header+="GRAY/GRAYref"+delimiter
    header+="R/Rref"+delimiter
    header+="G/Gref"+delimiter
    header+="B/Bref"
    outfile.write(header+"\n")
    columns=len(ratios)
    ratios=ratios.T
    f=0
    for row in ratios:
      outfile.write(names[f]+delimiter)
      outfile.write(str(xs[f])+delimiter)
      f+=1
      s=""
      for i in range(0,columns):
        s+=str(row[i])
        if i<columns-1:
          s+=delimiter
      outfile.write(s+"\n")  
outfile.close()