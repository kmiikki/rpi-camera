#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 09:32:28 2020

@author: Kim Miikki

Arguments example:
-bp 0 -wp 100 -gamma .9 -obp 2 -owp 253 -png

"""
import cv2
import numpy as np
import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from rpi.inputs2 import *

def newFilename(oldname,ext):
  newname=re.sub("\s+", "_", oldname.strip())
  if convert_to_png:
      newname+=".png"
  else:
      newname+=ext
  return newname

def levels(image,black_point,white_point,gamma=1.0,out_bp=0,out_wp=255):
    inBlack  = np.array([black_point,black_point,black_point],dtype=np.float32)
    inWhite  = np.array([white_point,white_point,white_point],dtype=np.float32)
    inGamma  = np.array([gamma, gamma, gamma], dtype=np.float32)
    outBlack = np.array([out_bp, out_bp, out_bp], dtype=np.float32)
    outWhite = np.array([out_wp, out_wp, out_wp], dtype=np.float32)
    
    image = np.clip((image - inBlack) / (inWhite - inBlack), 0, 255)
    image = (image ** (1/inGamma)) * (outWhite - outBlack) + outBlack
    image = np.clip(image, 0, 255).astype(np.uint8)
    return image

# Global variables
fname=""
pictures=0
in_bp=0
in_wp=255
in_gamma=1.0
out_bp=0
out_wp=255
convert_to_png=False

print("Levels batch tool for images")
print("")

# Get current directory
curdir=os.getcwd()
levelsdir=curdir+"/levels"
path=Path(curdir)
print("Current directory:")
print(curdir)
print("")

parser = argparse.ArgumentParser()
parser.add_argument("-bp",type=int,help="in: black point (0...255) as integer",required=False)
parser.add_argument("-wp",type=int,help="in: white point (0...255) as integer",required=False)
parser.add_argument("-gamma",type=float,help="in: gamma (default=1.0) as float",required=False)
parser.add_argument("-obp",type=int,help="out: black point (0...255) as integer",required=False)
parser.add_argument("-owp",type=int,help="out: white point (0...255) as integer",required=False)
parser.add_argument("-png", action="store_true", help="convert images to PNG format")
parser.add_argument("-i", action="store_true", help="interactive mode")
args=parser.parse_args()

interactive=False
if args.i:
    interactive=True
if args.png:
    convert_to_png=True
if args.bp is not None:
    in_bp=args.bp
if args.wp is not None:
    in_wp=args.wp
if args.gamma is not None:
    in_gamma=args.gamma
if args.obp is not None:
    out_bp=args.obp
if args.owp is not None:
    out_wp=args.owp

error_list=[]
if in_bp<0 or in_bp>255:
    error_list.append("In black point out of range")
    in_bp=0
if in_wp<0 or in_wp>255:
    error_list.append("In white point out of range")
    in_wp=255
if in_gamma<=0:
    error_list.append("Gamma out of range (<= 0)")
    in_gamma=1.0
if out_bp<0 or out_bp>255:
    error_list.append("Out black point out of range")
    out_bp=0
if out_wp<0 or out_wp>255:
    error_list.append("Out white point out of range")
    out_wp=255
if in_bp>=in_wp:
    error_list.append("In black point >= in white point")
    in_bp=0
    in_wp=255
if out_bp>=out_wp:
    error_list.append("Out black point >= out white point")
    out_bp=0
    out_wp=255

errors=False
if len(error_list)>0:
    errors=True
    print("Argument errors:")
    for s in error_list:
        print(s)
    print("")
    print("Auto corrected level values:")
    print("In black point:  "+str(in_bp))
    print("In white point:  "+str(in_wp))
    print("In gamma:        "+str(in_gamma))
    print("Out black point: "+str(out_bp))
    print("Out white point: "+str(out_wp))

if interactive:
    default_bp=in_bp
    default_wp=in_wp
    default_gamma=in_gamma
    default_obp=out_bp
    default_owp=out_wp
    default_png=convert_to_png
    in_bp=inputValue("in black point",0,in_wp-1,default_bp,"","Black point is out of range!",True)
    if in_wp<=in_bp:
        in_wp=255
        default_wp=in_wp
    in_wp=inputValue("in white point",in_bp+1,255,default_wp,"","White point is out of range!",True)
    in_gamma=inputValue("in gamma",0.001,1000-1,default_gamma,"","Gamma is out of range!",False)
    out_bp=inputValue("out black point",0,out_wp-1,default_obp,"","Black point is out of range!",True)
    if out_wp<=out_bp:
        out_wp=255
        default_wp=out_wp
    out_wp=inputValue("out white point",out_bp+1,255,default_owp,"","White point is out of range!",True)
    convert_to_png=inputYesNo("Convert images to PNG","PNG conversion enabled",default_png)
    errors=False

if not errors:
    print("")
    print("Summary of level values:")
    print("In black point:  "+str(in_bp))
    print("In white point:  "+str(in_wp))
    print("In gamma:        "+str(in_gamma))
    print("Out black point: "+str(out_bp))
    print("Out white point: "+str(out_wp))
    print("PNG conversion:  ",end="")
    if convert_to_png:
        print("Enabled")
    else:
        print("Disabled")
  
try:
  if not os.path.exists(levelsdir):
    os.mkdir(levelsdir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# Create a log file
path=Path(curdir)
foldername=os.path.basename(curdir)
outname="levels-"+foldername+".log"

t1=datetime.now()
dt_string = t1.strftime("%Y.%m.%d-%H:%M:%S")
# Test if a log file can be created
try:
  file=open(str(path)+"/"+outname,"w")
except OSError:
  print("Unable to create a log file in the following directory:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

file.write("Log created on "+dt_string+"\n\n")
file.write("Summary of level values:"+"\n")
file.write("In black point:  "+str(in_bp)+"\n")
file.write("In white point:  "+str(in_wp)+"\n")
file.write("In gamma:        "+str(in_gamma)+"\n")
file.write("Out black point: "+str(out_bp)+"\n")
file.write("Out white point: "+str(out_wp)+"\n")
file.write("PNG conversion:  ")
if convert_to_png:
    file.write("Enabled")
else:
    file.write("Disabled")

print("")
print("Processing:")
file.write("\n\n")
file.write("Processing:\n")
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    fname=p.name
    try:
      img = cv2.imread(str(path)+"/"+fname)
      # Get image dimensions
      w=img.shape[1]
      h=img.shape[0]
    except:
      print("Skip: "+fname)
      file.write("Skip: "+fname+"\n")
      continue
    else:
      try:
        newname=newFilename(p.stem,p.suffix)
        fullpath=levelsdir+"/"+newname
        img=levels(img,in_bp,in_wp,in_gamma,
                   out_bp,out_wp)
        cv2.imwrite(fullpath,img)
        pictures+=1
      except:
        print("Unable to save: "+newname)
        continue
      else:
        tmp=fname+" ("+str(w)+"x"+str(h)+")"
        if convert_to_png and p.suffix.lower()!=".png":
            tmp+=" -> "
            tmp+=newname
        else:
            tmp+=": done"
        print(tmp)
        file.write(tmp+"\n")
        
t2=datetime.now()

print("\nPictures processed: "+str(pictures))
print("Time elapsed:       "+str(t2-t1))
file.write("\nPictures processed: "+str(pictures)+"\n")
file.write("Time elapsed:       "+str(t2-t1)+"\n")
file.close()