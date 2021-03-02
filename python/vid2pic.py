#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 15 22:08:12 2020

@author: Kim Miikki
"""

# To use the imageio ffmpeg plugin you need to 'pip install imageio-ffmpeg'
# sudo pip3 install imageio-ffmpeg

import cv2
import imageio
import argparse
import io
from datetime import datetime
import os
import pathlib
import sys

frames_dir="img"
ext=".jpg"

parser=argparse.ArgumentParser()
parser.add_argument("file", type=pathlib.Path, help="video file")
parser.add_argument("-png", action="store_true", help="extract frames to PNG format")
args = parser.parse_args()

if args.png:
    ext=".png"

curdir=os.getcwd()
try:
  if not os.path.exists(frames_dir):
    os.mkdir(frames_dir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

print("Extract frames from a video")
print("")
print("Current directory:")
print(curdir)
print("")

file=args.file
with open(file,"rb") as file:
    content=file.read()
vid=imageio.get_reader(io.BytesIO(content),"ffmpeg")

meta=vid.get_meta_data()
fps=meta["fps"]
time=meta["duration"]
frames=int(fps*time)
digits=len(str(frames))

print("Frames: "+str(frames))
print("Digits: "+str(digits))
print("FPS:    "+str(fps))
print("Time:   "+str(time))
print("Ext:    "+ext)

if frames<1:
    print("No frames found!")
    sys.exit(0)
else:
    print("\nExtracting frames:")

t1=datetime.now()
for idx,frame in enumerate(vid):
    name="frame"+str(idx+1).zfill(digits)+ext
    if ext==".jpg":
        imageio.imsave(frames_dir+"/"+name,frame)
    elif ext==".png":
        # OpenCV: use BGR
        img_bgr=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)
        cv2.imwrite(frames_dir+"/"+name,img_bgr)
    print(name)

t2=datetime.now()
print("\nPictures extracted: "+str(idx))
print("Time elapsed: "+str(t2-t1))
