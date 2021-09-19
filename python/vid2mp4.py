#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:04:09 2021

@author: Kim Miikki

Prerequisite:
MP4Box
- install: sudo apt install -y gpac

Convert mkv to h264:
ffmpeg -i video.mkv -c:v libx264 -profile:v high444 -level:v 4.0 -pix_fmt yuv420p video.h264

"""

import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

fps_ref=25.0
fps_rec=0.0
fps_out=0.0
fps=0
min_value=1e-9
max_value=1e+9
isREC=False
isFPS=False
noGraphs=False
isPTS=False
saveIntervals=True
fname=""
videoname=""

bins=20
stat_decimals=2

# Read and parse program arguments
parser=argparse.ArgumentParser()
parser.add_argument("file", type=Path, help="video file name")
parser.add_argument("-rec",type=float,help="recorded FPS as float",required=False)
parser.add_argument("-fps",type=float,help="playback FPS as float",required=False)
parser.add_argument("-n", action="store_true", help="do not create graphs",required=False)
args = parser.parse_args()
fname=args.file
videoname=fname.name

if args.rec != None:
    fps_rec=float(args.rec)
    isREC=True
else:
    fps_rec=fps_ref

if args.fps != None:
    fps_out=float(args.fps)
    isFPS=True
else:
    fps_out=fps_ref
    
if args.n:
    noGraphs=True

print("Convert video to mp4 format")

curdir=os.getcwd()
path=Path(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

# Check if video file exists
try:
    ifile=open(fname,"r")
    ifile.close()
except:
    print("Unable to open: "+str(fname))
    sys.exit(0)

pts_file=fname.stem+".pts"
ar=np.array([])
if os.path.isfile(pts_file):
    print("PTS file found: "+pts_file)
    # Count frames        
    frames=0
    firstLine=True
    for line in open(pts_file):
        if firstLine:
            firstLine=False
            continue
        frames+=1
        if frames==1:
            start_value=float(line)
            continue
        end_value=float(line)
        ar=np.append(ar,end_value-start_value)
        start_value=end_value
    # Calculate interval statistics
    if len(ar)>0:
        # Auto adjust bins count
        n=len(ar)
        b=int(n/4)
        if b<1:
            b=1
        bins=b
        
        isPTS=True
        # Probability distribution and cumalative distribution functions
        count, bins_count = np.histogram(ar, bins=bins)
        pdf=count/sum(count)
        cdf=np.cumsum(pdf)
        # Statistical values
        mean=np.mean(ar)
        median=round(np.median(ar),stat_decimals)
        variance=round(np.var(ar),stat_decimals)
        
        # Plot graphs
        if noGraphs==False:
            # Histogram
            fig=plt.figure()
            plt.xlabel("Interval (ms)")
            plt.ylabel("Count")
            plt.hist(ar)
            plt.savefig(fname.stem+"-histogram.png",dpi=300)
            plt.close(fig)
            # PDF and CDF
            fig=plt.figure()
            plt.xlabel("Interval (ms)")
            plt.ylabel("Density")
            plt.plot(bins_count[1:], pdf, color="red", label="PDF")
            plt.plot(bins_count[1:], cdf, color="blue", label="CDF")
            plt.legend()
            plt.savefig(fname.stem+"-distribution.png",dpi=300)
            plt.close(fig)
        # Save interval data
        if saveIntervals:
            with open(fname.stem+"-intervals.txt", "w") as f:
                for s in ar:
                    f.write(str(s) +"\n")
    else:
        print("No intervals in the PTS file!")
 
# Calculate FPS for the mp4 file
speed=fps_out/fps_rec
if not isPTS:
    #speed=fps_out/fps_rec
    fps=speed*fps_ref
else:
    #tvideo=(end_value+mean)/1000
    #tframe=(fps_rec/fps_ref)*(tvideo/frames)
    # tvideo/frames == mean
    #tframe=(fps_rec/fps_ref)*(mean/1000)
    tframe=(mean/1000)/speed
    fps=1/tframe

    mean=round(mean,stat_decimals)
    
fps=round(fps,3)
if fps_rec.is_integer():
    fps_rec=int(fps_rec)
if fps_out.is_integer():
    fps_out=int(fps_out)

# Generate MP4Box command
cmd="MP4Box "
cmd+="-add "
cmd+=videoname+" "
cmd+="-new "
cmd+=fname.stem+".mp4"+" "
cmd+="-fps "
cmd+=str(fps)

# Execute the command
os.system(cmd)

# Write a log file
logname=fname.stem+"-mp4.log"
now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")
f=open(logname,"w")
f.write("vid2mp4.py log file"+"\n\n")
f.write("Log created on "+dt_string+"\n\n")
# Store used arguments
f.write("Program arguments: "+"\n\n")
f.write("FPS recorded: "+str(fps_rec)+"\n")
f.write("FPS playback: "+str(fps_out)+"\n")
if noGraphs:
    f.write("Graphs: disabled"+"\n")
f.write("\n")

f.write("FPS: "+str(fps)+"\n")
if speed<1:
    v=round(1/speed,1)
    f.write("Slowdown: "+str(v)+"x\n")
else:
    v=round(speed,1)
    f.write("Speedup: "+str(v)+"x\n")
f.write("\n")

if len(ar)>0:
    f.write("Statistics:"+"\n")
    f.write("Intervals: "+str(len(ar))+"\n")
    f.write("Frames   : "+str(frames)+"\n")
    f.write("Mean     : "+str(mean)+"\n")
    f.write("Median   : "+str(median)+"\n")
    f.write("Variance : "+str(variance)+"\n\n")

f.write("MP4 command:\n"+cmd+"\n")
f.close()
