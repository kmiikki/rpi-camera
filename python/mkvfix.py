#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 19 11:01:01 2021

@author: Kim Miikki

Prerequisite:
ffmpeg

Fix Raspberry Pi palyback issue by converting mkv to h264 using this template:
ffmpeg -i video.mkv -c:v libx264 -profile:v high444 -level:v 4.0 -pix_fmt yuv420p video.h264

Convert h264 video to mp4:
vid2mp4.py video-rgb.h264

"""

import argparse
import os
import sys
from pathlib import Path

# Read and parse program arguments
parser=argparse.ArgumentParser()
parser.add_argument("file", type=Path, help="mkv video file name")
args = parser.parse_args()
fname=args.file
videoname=fname.name

print("Fix mkv playback issue on Raspberry Pi")

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

h264_file=fname.stem+".h264"

# Genereate ffmpeg command
cmd="ffmpeg "
cmd+="-i "+videoname+" "
cmd+="-c:v libx264 "
cmd+="-profile:v high444 "
cmd+="-level:v 4.0 "
cmd+="-pix_fmt yuv420p "
cmd+=h264_file

# Execute the command
os.system(cmd)

