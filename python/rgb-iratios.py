#!/usr/bin/python3
# (C) Kim Miikki 2022

import argparse
import csv
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np


# y-axes labels
yaxis_label_r_g="R/G ratio"
yaxis_label_r_b="R/B ratio"

yaxis_label_g_r="G/R ratio"
yaxis_label_g_b="G/B ratio"

yaxis_label_b_r="B/R ratio"
yaxis_label_b_g="B/G ratio"

yaxis_label_r_gb="R/GBmean ratio"
yaxis_label_g_rb="G/RBmean ratio"
yaxis_label_b_rg="B/RGmean ratio"

# x-axis label
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
clipy=-1.0
minval=1e-9
unit=""
delimiter=","
isStart=False
isInterval=False
isUnit=False
scale_y=False
is_clip_y=False
isMinval=True
firstchar_cap=True
fileTime=True
replaceBrackets=True # [] -> ()
linew_min=0.1
linew_max=2.0
linew_default=1.0
linew=linew_default
grid=True

rgb_in="rgb.csv"
adir="rgb"
outname="rgbratios.csv"

def bracketsType(text):
    a=-1
    b=-1
    brackets=""
    
    # Test ()
    a=text.rfind("(")
    b=text.rfind(")")
    if b>a and a>=0:
        brackets="()"
    else:
        # Test []
        a=text.rfind("[")
        b=text.rfind("]")
        if b>a and a>=0:
            brackets="[]"
    return brackets
        
def getUnitPos(label,search="()"):
    a=-1
    b=-1
    ch1=""
    ch2=""
    text=""
    unit=""
    result=True
    if len(search)!=2:
        result=False
    else:
        ch1=search[0]
        ch2=search[1]
    if result:
        a=label.rfind(ch1)
        b=label.rfind(ch2)
        if b>a:
           unit=label[a+1:b]
           if a>0:
               text=label[:a].strip()
    return text,unit,a,b

parser=argparse.ArgumentParser()
parser.add_argument("RGB")
parser.add_argument('-s',type=float,help="start time for first frame as float",required=False)
parser.add_argument('-i',type=float,help="interval between two frames as float",required=False)
parser.add_argument('-cy',type=float,help="clip upper y value as float",required=False)
parser.add_argument("-u", nargs="*", type=str,help="x unit string",required=False)
parser.add_argument('-w',type=float,help="line width "+str(linew_min)+"-"+str(linew_max),required=False)
parser.add_argument("-n", action="store_true", help="Do not draw grids")
parser.add_argument("-y", action="store_true", help="auto scale y-axis")
parser.add_argument("-d", action="store_true", help="disable auto minimum value ("+str(minval)+")")
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

if args.cy != None:
    clipy=float(args.cy)
    if clipy>0:
        is_clip_y=True

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

print("RGB Internal Ratios 1.0, (c) Kim Miikki 2022")

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
names=[]
try:
    with open(rgb_in,"r") as reader_obj:
        csv_reader=csv.reader(reader_obj)
        header_rgb=next(csv_reader)
        xaxis_label=header_rgb[1]
        if firstchar_cap:
            xaxis_label=xaxis_label[0].upper()+xaxis_label[1:]
        if replaceBrackets:
            xaxis_label=xaxis_label.replace("[","(")
            xaxis_label=xaxis_label.replace("]",")")
        if not fileTime:
            br=bracketsType(xaxis_label)
            t,u,a,b=getUnitPos(xaxis_label,br)
            xaxis_label=t
            if len(unit)>0:
                xaxis_label+=" ("+unit+")"
            # print(t,u,a,b)
        
        for row in csv_reader:
            rgb_data.append(list(map(float,row[1:])))
            names.append(row[0])
            #print(row)
except OSError:
    print("Unable to open "+rgb_in+" in following directory:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)    

pictures=len(rgb_data)

arr1=np.array(rgb_data)

arr1=arr1.T

if fileTime:
    xs=arr1[0]
else:
    xs=np.linspace(start,start+interval*(pictures-1),num=pictures)

r=arr1[2]
g=arr1[3]
b=arr1[4]
if isMinval:
    r[r<minval]=minval
    g[g<minval]=minval
    b[b<minval]=minval
    
bw=(r+g+b)/3
    
rg_mean=np.mean([r,g],axis=0)
rb_mean=np.mean([r,b],axis=0)
gb_mean=np.mean([g,b],axis=0)
if isMinval:
    rg_mean[rg_mean<minval]=minval
    rb_mean[rb_mean<minval]=minval
    gb_mean[gb_mean<minval]=minval

r_g=r/g
r_b=r/b

g_r=g/r
g_b=g/b

b_r=b/r
b_g=b/g

r_gb=r/gb_mean
g_rb=g/rb_mean
b_rg=b/rg_mean

ratios=np.vstack((r,g,b,bw,rg_mean,rb_mean,gb_mean,r_g,r_b,g_r,g_b,b_r,b_g,r_gb,g_rb,b_rg))

if pictures>1:

    # Plot RGB
    fig=plt.figure()
    ylabel="RGB mean value"
    ymins=[r.min(),g.min(),b.min()]
    ymaxs=[r.max(),g.max(),b.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,r,color="r",linewidth=linew)
    plt.plot(xs,g,color="g",linewidth=linew)
    plt.plot(xs,b,color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"1_RGB.png",dpi=300)
    plt.close(fig)

    # Plot R
    fig=plt.figure()
    ylabel="R mean value"
    ymins=[r.min()]
    ymaxs=[r.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,r,color="r",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"2_R.png",dpi=300)
    plt.close(fig)

    # Plot G
    fig=plt.figure()
    ylabel="G mean value"
    ymins=[g.min()]
    ymaxs=[g.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,g,color="g",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"2_G.png",dpi=300)
    plt.close(fig)

    # Plot B
    fig=plt.figure()
    ylabel="B mean value"
    ymins=[b.min()]
    ymaxs=[b.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,b,color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"2_B.png",dpi=300)
    plt.close(fig)
    
    # Plot BW
    fig=plt.figure()
    ylabel="BW mean value"
    ymins=[bw.min()]
    ymaxs=[bw.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,bw,color="k",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"3_BW.png",dpi=300)
    plt.close(fig)

    # Plot RG, RB and GB means
    fig=plt.figure()
    ylabel="RG, RB, GB means"
    ymins=[rg_mean.min(),rb_mean.min(),gb_mean.min()]
    ymaxs=[rg_mean.max(),rb_mean.max(),gb_mean.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,rg_mean,color="y",linewidth=linew)
    plt.plot(xs,rb_mean,color="m",linewidth=linew)
    plt.plot(xs,gb_mean,color="c",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"4_RG_RB_GB.png",dpi=300)
    plt.close(fig)

    # Plot R/C ratios
    fig=plt.figure()
    ylabel="R/G, R/B ratios"
    ymins=[r_g.min(),r_b.min()]
    ymaxs=[r_g.max(),r_b.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,r_g,color="g",linewidth=linew)
    plt.plot(xs,r_b,color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"5_RG_RB.png",dpi=300)
    plt.close(fig)

    # Plot G/C ratios
    fig=plt.figure()
    ylabel="G/R, G/B ratios"
    ymins=[g_r.min(),g_b.min()]
    ymaxs=[g_r.max(),g_b.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,g_r,color="r",linewidth=linew)
    plt.plot(xs,g_b,color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"5_GR_GB.png",dpi=300)
    plt.close(fig)

    # Plot B/C ratios
    fig=plt.figure()
    ylabel="B/R, B/G ratios"
    ymins=[b_r.min(),b_r.min()]
    ymaxs=[b_g.max(),b_r.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,b_r,color="r",linewidth=linew)
    plt.plot(xs,b_g,color="g",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"5_BR_BG.png",dpi=300)
    plt.close(fig)

    # Plot C1/C2C3mean ratios
    fig=plt.figure()
    ylabel="R/GB, G/RB, B/RG ratios"
    ymins=[r_gb.min(),g_rb.min(),b_rg.min()]
    ymaxs=[r_gb.max(),g_rb.max(),b_rg.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,r_gb,color="r",linewidth=linew)
    plt.plot(xs,g_rb,color="g",linewidth=linew)
    plt.plot(xs,b_rg,color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"6_RGB_GBR_BRG.png",dpi=300)
    plt.close(fig)

    # Plot R/GB ratio
    fig=plt.figure()
    ylabel="R / GB ratio"
    ymins=[r_gb.min()]
    ymaxs=[r_gb.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,r_gb,color="r",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"7_R_GB.png",dpi=300)
    plt.close(fig)

    # Plot G/RB ratio
    fig=plt.figure()
    ylabel="G / RB ratio"
    ymins=[g_rb.min()]
    ymaxs=[g_rb.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,g_rb,color="g",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"7_G_RB.png",dpi=300)
    plt.close(fig)

    # Plot B/RG ratio
    fig=plt.figure()
    ylabel="B / RG ratio"
    ymins=[b_rg.min()]
    ymaxs=[b_rg.max()]
    ymin=min(ymins)
    ymax=max(ymaxs)
    if not scale_y:
        ymin=0
    if is_clip_y:
        if ymax>clipy:
            ymax=clipy
    plt.xlim(min(xs),max(xs))
    plt.ylim(ymin,ymax)
    plt.plot(xs,b_rg,color="b",linewidth=linew)
    plt.xlabel(xaxis_label)
    plt.ylabel(ylabel)
    if grid:
        plt.grid()
    plt.savefig(adir+"7_B_RG.png",dpi=300)
    plt.close(fig)

if pictures>0:    
    # Save rgbratio.csv 
    header="picture_name"+delimiter
    header+=xaxis_label+delimiter
    header+="R"+delimiter
    header+="G"+delimiter
    header+="B"+delimiter
    header+="BW"+delimiter
    header+="RGmean"+delimiter
    header+="RBmean"+delimiter
    header+="GBmean"+delimiter
    header+="R/G"+delimiter
    header+="R/B"+delimiter
    header+="G/R"+delimiter
    header+="G/B"+delimiter
    header+="B/R"+delimiter
    header+="B/G"+delimiter
    header+="R/GB"+delimiter
    header+="G/RB"+delimiter
    header+="B/RG"
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
