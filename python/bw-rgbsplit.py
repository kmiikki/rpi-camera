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

print("BW-RGBsplit 1.0, (c) Kim Miikki 2020")
print("")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
outname="bw-rgbsplit-"+foldername+".txt"

# Test if a log file can be created
try:
  file=open(str(path)+"/"+outname,"w")
except OSError:
  print("Unable to create a log file in the following directory:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

skipped=0
t1=datetime.now()
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file() and (suffix==".png" or suffix==".jpg"):
    fname=p.name
    img=cv2.imread(str(path)+"/"+fname,cv2.IMREAD_UNCHANGED)
    if img.ndim>=3:
        h, w, ch = img.shape
    elif img.ndim==2:
      print(fname+" has only 1 channel. Skipping file.")
      skipped+=1
      continue
    
    # Extract blue channel
    b=img[:,:,0]
    
    # Extract green channel
    g=img[:,:,1]
    
    # Extract red channel
    r=img[:,:,2]
 
    cv2.imwrite(str(path)+"/"+"BWR-"+fname,r)
    cv2.imwrite(str(path)+"/"+"BWG-"+fname,g)
    cv2.imwrite(str(path)+"/"+"BWB-"+fname,b)
    
    pictures+=1
    if pictures==1:
      print("Splitting color channels:")
    print(fname+": "+str(w)+"x"+str(h))
    filelist.append(fname+": "+str(w)+"x"+str(h))
t2=datetime.now()

if len(filelist)>0:
    file.write("List of processed pictures:\n")
    for i in filelist:
        file.write(i+"\n")
    print("")
    file.write("\n")
elif skipped>0:
    print("")
print("Pictures processed: "+str(pictures))
print("Time elapsed: "+str(t2-t1))
file.write("Pictures processed: "+str(pictures)+"\n")
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
