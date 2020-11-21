#!/usr/bin/python3

# Arguments:
# -rgb -bw -x -y
# -s -i -rgb -bw -x -y
# -s

import argparse
import os
import sys
from pathlib import Path
import cv2        
import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime

t1=0
t2=0
fname=""
pictures=0
xresults=[]
yresults=[]

separateDirs=False
showOriginal=False
showChannels=False
showBW=False
showXs=False
showYs=False

adir="rgb"
xdir="rgbx"
ydir="rgby"

parser=argparse.ArgumentParser()
parser.add_argument("-s", action="store_true", help="X and Y figures in separate directories")
parser.add_argument("-i", action="store_true", help="display original image")
parser.add_argument("-rgb", action="store_true", help="display RGB channel means")
parser.add_argument("-bw", action="store_true", help="display black and white means")
parser.add_argument("-x", action="store_true", help="display RGB means in x direction")
parser.add_argument("-y", action="store_true", help="display RGB means in y direction")
args = parser.parse_args()

if args.s:
    separateDirs=True
if args.i:
    showOriginal=True
if args.rgb:
    showChannels=True
if args.bw:
    showBW=True
if args.x:
    showXs=True
if args.y:
    showYs=True
if showXs==False and showYs==False:
    if showChannels==True or showBW==True:
        showXs==True
        showYs=True

print("RGBXY 1.0, (c) Kim Miikki 2020")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

try:
  if not os.path.exists(adir):
    os.mkdir(adir)
  if not os.path.exists(xdir) and separateDirs:
    os.mkdir(xdir)
  if not os.path.exists(ydir) and separateDirs:
    os.mkdir(ydir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)
  
if args.s:
    xdir=curdir+"/"+xdir+"/"
    ydir=curdir+"/"+ydir+"/"
else:
    xdir=curdir+"/"+adir+"/"
    ydir=curdir+"/"+adir+"/"
adir=curdir+"/"+adir+"/"

# Create a log file
file=open(adir+"analysis.log","w")
file.write("RGBXY parameters:\n")
file.write("Analysis directory: "+curdir+"\n")
file.write("Create separate X and Y directories: ")
if separateDirs:
    file.write("Yes")
else:
    file.write("No")
file.write("\n")
    
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
    pictures+=1

    if pictures==1:
      print("Analyze:")
      file.write("\nAnalyze: \n")
    print(fname+": "+str(w)+"x"+str(h))
    file.write(fname+": "+str(w)+"x"+str(h)+"\n")

    fig=plt.figure()
    plt.xlabel("X coordinate")
    plt.ylabel("Y coordinate")
    plt.imshow(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
    plt.savefig(adir+p.stem+"-img.png",dpi=300)
    if showOriginal:
        plt.show()
    plt.close(fig)

    xrgbs=img.mean(axis=0)
    xs=np.array(list(range(0,w)))
    xs=xs.reshape((-1,1))

    yrgbs=img.mean(axis=1)
    ys=np.array(list(range(0,h)))
    ys=ys.reshape((-1,1))

    # Plot RGB means in x direction
    fig=plt.figure()
    plt.xlim(0,w)
    plt.ylim(0,255)
    plt.plot(xrgbs[:,2],color="r")
    plt.plot(xrgbs[:,1],color="g")
    plt.plot(xrgbs[:,0],color="b")
    plt.xlabel("Column (X) coordinate")
    plt.ylabel("RGB mean")
    plt.savefig(xdir+p.stem+"-xRGB.png",dpi=300)
    if showXs and showChannels:
        plt.show()
    plt.close(fig)

    # Plot BW means in x direction
    fig=plt.figure()
    plt.xlim(0,w)
    plt.ylim(0,255)
    xbws=xrgbs.mean(axis=1)
    plt.plot(xbws,color="k")
    plt.xlabel("Column (X) coordinate")
    plt.ylabel("BW mean")
    plt.savefig(xdir+p.stem+"-xBW.png",dpi=300)
    if showXs and showBW:
        plt.show()
    plt.close(fig)

    # Plot RGB means in y direction
    fig=plt.figure()
    plt.xlim(0,h)
    plt.ylim(0,255)
    plt.plot(yrgbs[:,2],color="r")
    plt.plot(yrgbs[:,1],color="g")
    plt.plot(yrgbs[:,0],color="b")
    plt.xlabel("Row (Y) coodinate")
    plt.ylabel("RGB mean")
    plt.savefig(ydir+p.stem+"-yRGB.png",dpi=300)
    if showYs and showChannels:
        plt.show()
    plt.close(fig)

    # Plot BW means in y direction
    fig=plt.figure()
    plt.xlim(0,h)
    plt.ylim(0,255)
    ybws=yrgbs.mean(axis=1)
    plt.plot(ybws,color="k")
    plt.xlabel("Row (Y) coordinate")
    plt.ylabel("BW mean")
    plt.savefig(ydir+p.stem+"-yBW.png",dpi=300)
    if showYs and showBW:
        plt.show()
    plt.close(fig)
    
    xresults=np.column_stack((xs,xrgbs,xbws))
    yresults=np.column_stack((ys,yrgbs,ybws))
    fmt="%d","%1.3f","%1.3f","%1.3f","%1.3f"
    np.savetxt(xdir+p.stem+"-x.csv", xresults, fmt=fmt, delimiter=",")
    np.savetxt(ydir+p.stem+"-y.csv", yresults, fmt=fmt, delimiter=",")
t2=datetime.now()

print("\nPictures analyzed: "+str(pictures))
file.write("\nPictures analyzed: "+str(pictures)+"\n")
print("Time elapsed: "+str(t2-t1))
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
