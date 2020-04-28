#!/usr/bin/python3
import os
import sys
from pathlib import Path
import numpy as np  # sudo pip3 install numpy
import cv2          # sudo pip3 install opencv-python
from datetime import datetime

print("RGBinfo 1.0, (c) Kim Miikki 2019")

t1=0
t2=0
fname=""
pictures=0
results=[]
# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
outname="rgb-"+foldername+".txt"
t1=datetime.now()
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
    print(fname+": "+str(w)+"x"+str(h))
    r_avg=rgb_means[2]
    g_avg=rgb_means[1]
    b_avg=rgb_means[0]
    rgb_avg=(r_avg+g_avg+b_avg)/3
    rgb_ratio=rgb_avg/255
    r_ratio=r_avg/255
    g_ratio=g_avg/255
    b_ratio=b_avg/255
    results.append([fname,rgb_avg,r_avg,g_avg,b_avg,rgb_ratio,r_ratio,g_ratio,b_ratio])
t2=datetime.now()

# Test if a RGB file can be created
try:
  file=open(str(path)+"/"+outname,"w")
except OSError:
  print("Unable to create a RGB file in the following directory:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

file.write("picture_name;rgb_avg;r_avg;g_avg;b_avg;rgb_ratio;r_ratio;g_ratio;b_ratio\n")
for value in results:
  s=""
  for i in range(0,9):
    s+=str(value[i])
    if i<8:
      s+=";"
  file.write(s+"\n")
print("\nPictures analyzed: "+str(pictures))
file.write("\nPictures analyzed:;"+str(pictures)+"\n")
print("Time elapsed: "+str(t2-t1))
file.write("Time elapsed:;"+str(t2-t1)+"\n")
file.close()
