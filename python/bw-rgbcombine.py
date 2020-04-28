#!/usr/bin/python3
  
import os
import sys
from pathlib import Path
import numpy as np  # sudo pip3 install numpy
import cv2          # sudo pip3 install opencv-python
from datetime import datetime

# Global variables
t1=0
t2=0
fname=""
pictures=0
rfiles=list()
gfiles=list()
bfiles=list()
newfiles=list()
filelist=[]

print("BW-RGBcombine 1.0, (c) Kim Miikki 2020")
print("")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
newpath=str(path)+"/"+"img"
foldername=os.path.basename(curdir)
outname="bw-rgbcombine-"+foldername+".txt"
t1=datetime.now()

# Test if picture directory is present or can be created
try:
  if not os.path.exists(newpath):
    os.mkdir(newpath)
except OSError:
  print("Unable to create a directory under following path: "+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# List all BWR, BWG and BWB pictures and generate new filenames
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file() and (suffix==".png" or suffix==".jpg"):
    fname=p.name
    isRGBch=False
    if fname.startswith("BWR-"):
      rfiles.append(fname)
      isRGBch=True
    elif fname.startswith("BWG-"):
      gfiles.append(fname)
      isRGBch=True
    elif fname.startswith("BWB-"):
      bfiles.append(fname)
      isRGBch=True
    if isRGBch==True:
      fname=fname[4:]
      if not fname in newfiles:
        newfiles.append(fname)

# Combine RGB channels and save pictures
skipped_files=list()
for p in sorted(newfiles):
    img=[]
    height=0
    width=0
    heights=[]
    widths=[]
    isRed=True
    isGreen=True
    isBlue=True
    h_r=0
    w_r=0
    h_g=0
    w_g=0
    h_b=0
    w_b=0
    pictures+=1
    if pictures==1:
      print("Combining color channels:")  
    filepath=newpath+"/"+p
    rfile="BWR-"+p
    gfile="BWG-"+p
    bfile="BWB-"+p
    imgr=cv2.imread(str(path)+"/"+rfile,cv2.IMREAD_UNCHANGED)
    imgg=cv2.imread(str(path)+"/"+gfile,cv2.IMREAD_UNCHANGED)
    imgb=cv2.imread(str(path)+"/"+bfile,cv2.IMREAD_UNCHANGED)
    errorlist=[]
    try:
      h_r, w_r = imgr.shape
      heights.append(h_r)
      widths.append(w_r)
    except AttributeError:
        errorlist.append(" Unable to process: "+rfile)
        skipped_files.append(rfile)
        isRed=False
    try:
      h_g, w_g = imgg.shape
      heights.append(h_g)
      widths.append(w_g)
    except AttributeError:
        errorlist.append(" Unable to process: "+gfile)
        skipped_files.append(gfile)
        isGreen=False
    try:
      h_b, w_b = imgb.shape
      heights.append(h_b)
      widths.append(w_b)
    except AttributeError:
        errorlist.append(" Unable to process: "+bfile)
        skipped_files.append(bfile)
        isBlue=False
    width=sorted(widths,reverse=True)[0]
    height=sorted(heights,reverse=True)[0]
    print(p+": "+str(width)+"x"+str(height))
    if len(errorlist)>0:
        for err in errorlist:
            print(err)
    if not isRed:
      imgr=np.zeros((height, width),np.uint8)
    if not isGreen:
      imgg=np.zeros((height, width),np.uint8)
    if not isBlue:
      imgb=np.zeros((height, width),np.uint8)
    img=cv2.merge([imgb,imgg,imgr])
    cv2.imwrite(filepath,img)
    filelist.append(p+": "+str(width)+"x"+str(height))

file=open(str(path)+"/"+outname,"w")
if len(filelist)>0:
    file.write("List of pictures merged from RGB color channels:\n")
    print("")
    for i in filelist:
        file.write(i+"\n")
    file.write("\n")
if len(skipped_files)>0:
    print("Skipped or missing files:")
    file.write("Skipped or missing files:\n")
    for f in skipped_files:
        print(f)
        file.write(f+"\n")
    print("")
    file.write("\n")
t2=datetime.now()
print("Pictures processed: "+str(pictures))
print("Time elapsed: "+str(t2-t1))
file.write("Pictures processed: "+str(pictures)+"\n")
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
