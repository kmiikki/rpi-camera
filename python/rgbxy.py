#!/usr/bin/python3
# (C) Kim Miikki 2022

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
saveImage=False
analyzeChannels=False
analyzeBW=False
analyzeXs=False
analyzeYs=False
csvFiles=True

adir="rgb"
xdir="rgbx"
ydir="rgby"
version="2.1"

def option_str(option,selected,end="\n"):
    s=option+": "
    if selected:
        s+="Yes"
    else:
        s+="No"
    s+=end
    return s
    
parser=argparse.ArgumentParser()
parser.add_argument("-s", action="store_true", help="X and Y figures in separate directories")
parser.add_argument("-i", action="store_true", help="save images with coordinates")
parser.add_argument("-rgb", action="store_true", help="analyze RGB channel means")
parser.add_argument("-bw", action="store_true", help="analyze BW means")
parser.add_argument("-x", action="store_true", help="analyze RGB means in x direction")
parser.add_argument("-y", action="store_true", help="analyze RGB means in y direction")
parser.add_argument("-n", action="store_true", help="no CSV files")
args = parser.parse_args()

if args.s:
    separateDirs=True
if args.i:
    saveImage=True
if args.rgb:
    analyzeChannels=True
if args.bw:
    analyzeBW=True
if args.x:
    analyzeXs=True
if args.y:
    analyzeYs=True
if args.n:
    csvFiles=False

# Enable all analysis if no analyze parameters selected
if not saveImage:
    if not True in [analyzeBW,analyzeChannels,analyzeXs,analyzeYs]:    
        analyzeBW=True
        analyzeChannels=True
        analyzeXs=True
        analyzeYs=True
    
    if not True in [analyzeXs,analyzeYs]:
        analyzeXs=True
        analyzeYs=True
    
    if not True in [analyzeChannels,analyzeBW]:
        analyzeChannels=True
        analyzeBW=True
else:
    if True in [analyzeBW,analyzeChannels,analyzeXs,analyzeYs]:  
        if not True in [analyzeXs,analyzeYs]:
            analyzeXs=True
            analyzeYs=True    
        if not True in [analyzeChannels,analyzeBW]:
            analyzeChannels=True
            analyzeBW=True
        
print("RGBXY "+version+", (c) Kim Miikki 2022")

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
file.write("RGBXY version 2.0\n")
file.write("Analysis directory: "+curdir+"\n")
file.write("\nOptions\n")
file.write("-------\n")
file.write(option_str("Create separate X and Y directories",separateDirs))
file.write(option_str("Save images with coordinates",saveImage))
file.write(option_str("Analyze RGB channel means",analyzeChannels))
file.write(option_str("Analyze BW means",analyzeBW))
file.write(option_str("Analyze RGB means in x direction",analyzeXs))
file.write(option_str("Analyze RGB means in y direction",analyzeYs))
file.write(option_str("Write CSV files",csvFiles))

file.write("\nCommand:\n")
file.write("rgbxy.py")
# Build options string
tmp=""
if separateDirs:
    tmp+=" -s"
if saveImage:
    tmp+=" -i"
if analyzeChannels:
    tmp+=" -rgb"
if analyzeBW:
    tmp+=" -bw"
if analyzeXs:
    tmp+=" -x"
if analyzeYs:
    tmp+=" -y"
if not csvFiles:
    tmp+=" -n"
if len(tmp)>0:
    file.write(tmp)
file.write("\n")



fmt_bw="%d","%1.3f"
fmt_rgb="%d","%1.3f","%1.3f","%1.3f"
fmt_rgb_bw="%d","%1.3f","%1.3f","%1.3f","%1.3f"
bw_str="BW"
rgb_str="R,G,B"
rgb_bw_str=rgb_str+",BW"

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

    if saveImage:
        fig=plt.figure()
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        plt.imshow(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
        plt.savefig(adir+"img-"+p.stem+".png",dpi=300)
        plt.close(fig)

    if analyzeXs:
        xrgbs=img.mean(axis=0)
        xs=np.array(list(range(0,w)))
        xs=xs.reshape((-1,1))

    if analyzeYs:
        yrgbs=img.mean(axis=1)
        ys=np.array(list(range(0,h)))
        ys=ys.reshape((-1,1))

    # Plot RGB means in x direction
    if analyzeXs and analyzeChannels:
        fig=plt.figure()
        plt.xlim(0,w)
        plt.ylim(0,255)
        plt.plot(xrgbs[:,2],color="r")
        plt.plot(xrgbs[:,1],color="g")
        plt.plot(xrgbs[:,0],color="b")
        plt.xlabel("Column (X) coordinate")
        plt.ylabel("RGB mean")
        plt.savefig(xdir+"xRGB-"+p.stem+".png",dpi=300)
        plt.close(fig)

    # Plot BW means in x direction
    if analyzeXs and analyzeBW:
        fig=plt.figure()
        plt.xlim(0,w)
        plt.ylim(0,255)
        xbws=xrgbs.mean(axis=1)
        plt.plot(xbws,color="k")
        plt.xlabel("Column (X) coordinate")
        plt.ylabel("BW mean")
        plt.savefig(xdir+"xBW-"+p.stem+".png",dpi=300)
        plt.close(fig)

    # Plot RGB means in y direction
    if analyzeYs and analyzeChannels:
        fig=plt.figure()
        plt.xlim(0,h)
        plt.ylim(0,255)
        plt.plot(yrgbs[:,2],color="r")
        plt.plot(yrgbs[:,1],color="g")
        plt.plot(yrgbs[:,0],color="b")
        plt.xlabel("Row (Y) coodinate")
        plt.ylabel("RGB mean")
        plt.savefig(ydir+"yRGB-"+p.stem+".png",dpi=300)
        plt.close(fig)

    # Plot BW means in y direction
    if analyzeYs and analyzeBW:
        fig=plt.figure()
        plt.xlim(0,h)
        plt.ylim(0,255)
        ybws=yrgbs.mean(axis=1)
        plt.plot(ybws,color="k")
        plt.xlabel("Row (Y) coordinate")
        plt.ylabel("BW mean")
        plt.savefig(ydir+"yBW-"+p.stem+".png",dpi=300)
        plt.close(fig)
    
    if analyzeXs and csvFiles:
        # BGR to RGB
        xrgbs[:,[0,2]]=xrgbs[:,[2,0]]
        if analyzeChannels and analyzeBW:
            xresults=np.column_stack((xs,xrgbs,xbws))
            fmt=fmt_rgb_bw
            header_str=rgb_bw_str
        elif analyzeChannels:
            xresults=np.column_stack((xs,xrgbs))
            fmt=fmt_rgb
            header_str=rgb_str
        else:
            xresults=np.column_stack((xs,xbws))
            fmt=fmt_bw
            header_str=bw_str
        header_str="x,"+header_str
        np.savetxt(xdir+"x-"+p.stem+".csv", xresults, fmt=fmt, delimiter=",", header=header_str, comments="")

    if analyzeYs and csvFiles:
        # BGR to RGB
        yrgbs[:,[0,2]]=yrgbs[:,[2,0]]
        if analyzeChannels and analyzeBW:
            yresults=np.column_stack((ys,yrgbs,ybws))
            fmt=fmt_rgb_bw
            header_str=rgb_bw_str
        elif analyzeChannels:
            yresults=np.column_stack((ys,yrgbs))
            fmt=fmt_rgb
            header_str=rgb_str
        else:
            yresults=np.column_stack((ys,ybws))
            fmt=fmt_bw
            header_str=bw_str
        header_str="y,"+header_str
        np.savetxt(ydir+"y-"+p.stem+".csv", yresults, fmt=fmt, delimiter=",", header=header_str, comments="")
        
t2=datetime.now()

print("\nPictures analyzed: "+str(pictures))
file.write("\nPictures analyzed: "+str(pictures)+"\n")
print("Time elapsed: "+str(t2-t1))
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
