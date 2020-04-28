#!/usr/bin/python3
  
import os
import sys
from pathlib import Path
import cv2          # sudo pip3 install opencv-python
from datetime import datetime

# Global variables
t1=0
t2=0
fname=""
pictures=0
filelist=[]

print("RGBsplit 1.0, (c) Kim Miikki 2019")
print("")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
outname="rgbsplit-"+foldername+".txt"

# Test if a log file can be created
try:
  file=open(str(path)+"/"+outname,"w")
except OSError:
  print("Unable to create a log file in the following directory:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

t1=datetime.now()
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file() and (suffix==".png" or suffix==".jpg"):
    fname=p.name
    img=cv2.imread(str(path)+"/"+fname)
    h, w, ch = img.shape
    if ch==1:
      print(fname+" has only 1 channel. Skipping file.")
      continue
    
    b=img.copy()
    # set green and red channels to 0
    b[:, :, 1] = 0
    b[:, :, 2] = 0
    
    g=img.copy()
    # set blue and red channels to 0
    g[:, :, 0] = 0
    g[:, :, 2] = 0
    
    r=img.copy()
    # set blue and green channels to 0
    r[:, :, 0] = 0
    r[:, :, 1] = 0
    
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    
    cv2.imwrite(str(path)+"/"+"R-"+fname,r)
    cv2.imwrite(str(path)+"/"+"G-"+fname,g)
    cv2.imwrite(str(path)+"/"+"B-"+fname,b)
    cv2.imwrite(str(path)+"/"+"BW-"+fname,gray)
    
    pictures+=1
    if pictures==1:
      print("Splitting color channels:")
    print(fname+": "+str(w)+"x"+str(h))
    filelist.append(fname+": "+str(w)+"x"+str(h))
    all_pixels=[]
t2=datetime.now()

if len(filelist)>0:
    print("")
    file.write("List of processed pictures:\n")
    for i in filelist:
        file.write(i+"\n")
    file.write("\n")
print("Pictures processed: "+str(pictures))
file.write("Pictures processed: "+str(pictures)+"\n")
print("Time elapsed: "+str(t2-t1))
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
