#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 28 09:51:10 2022

@author: Kim Miikki

"""

import csv
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import cv2

space=20
lineWidth=10
minWidth=1
gradientWidth=5
st=1
rfactor=1.0
gfactor=1.0
bfactor=1.0
minSpace=0
minSt=0

isGradientLeft=False
isGradientRight=False
testR=False
testG=False
testB=False

decreaseNonTestColors=False

# Plot variables
linew=1
grid=True
maxy=False

adir=""
rc=[]
bc=[]
gc=[]

argdict={'Image': '',
         'r': False,
         'g': False,
         'b': False,         
         'dec': False,
         'left': False,
         'right': False,
         'maxy': False,
         'w': False,
         'd': False,
         'grad': False,
         's': False,
         'rf': False,
         'gf': False,
         'bf': False}

parser=argparse.ArgumentParser()
parser.add_argument("Image", help="test image name")
parser.add_argument("-r", action="store_true", help="R test color")
parser.add_argument("-g", action="store_true", help="G test color")
parser.add_argument("-b", action="store_true", help="B test color")
parser.add_argument("-dec", action="store_true", help="enable decreasing of non test color(s)")
parser.add_argument("-left", action="store_true", help="enable left gradient")
parser.add_argument("-right", action="store_true", help="enable right gradient")
parser.add_argument("-maxy", action="store_true", help="Use maximum y axis scale")
parser.add_argument("-w",type=int,help="line width as positive integer")
parser.add_argument("-d",type=int,help="distance between lines as integer")
parser.add_argument("-grad",type=int,help="gradient width as positive integer")
parser.add_argument("-s",type=float,help="increase/decrease step value as positive float")
parser.add_argument("-rf",type=float,help="red factor as positive float")
parser.add_argument("-gf",type=float,help="green factor as positive float")
parser.add_argument("-bf",type=float,help="blue factor as positive float")

args = parser.parse_args()

print("Test lines creator 1.0, (c) Kim Miikki 2022")
print("")

fname=args.Image
stem=Path(args.Image).stem
argdict["Image"]=fname

if args.r:
    testR=True
    argdict["r"]=True
if args.g:
    testG=True
    argdict["g"]=True
if args.b:
    testB=True
    argdict["b"]=True

if args.dec:
    decreaseNonTestColors=True
    argdict["dec"]=True

if (not decreaseNonTestColors) and (not True in [testR,testG,testB]):
    print("No increasing or decreasing colors selected." )
    print("")

if args.left:
    isGradientLeft=True
    argdict["left"]=True
if args.right:
    isGradientRight=True
    argdict["right"]=True
if (args.grad == None) and True in [isGradientLeft,isGradientRight]:
    print("Default gradient set to "+str(gradientWidth))
    print("")
    argdict["grad"]=gradientWidth 

if args.maxy:
    maxy=True
    argdict["maxy"]=True

if (args.grad != None) or True in [isGradientLeft,isGradientRight]:
    if args.grad != None:
        gradientWidth=int(args.grad)
    argdict["grad"]=gradientWidth
    if gradientWidth<1:
        gradientWidth=1
        argdict["grad"]=gradientWidth
        print("Gradient width corrected to "+str(gradientWidth))
        print("")
    if not True in [isGradientLeft,isGradientRight]:
        print("Left and right gradients enabled")
        print("")
        isGradientLeft=True
        isGradientRight=True
        argdict["left"]=True
        argdict["right"]=True

minWidth+=isGradientLeft*gradientWidth
minWidth+=isGradientRight*gradientWidth

if args.w != None:
    lineWidth=int(args.w)
    argdict["w"]=lineWidth
if lineWidth<minWidth:
    print("Minimum width corrected to "+str(minWidth))
    print("")
    lineWidth=minWidth
    argdict["w"]=lineWidth

if args.d != None:
    space=int(args.d)
    argdict["d"]=space
if space<minSpace:
    print("Minimum distance between lines corrected to "+str(minSpace))
    print("")
    space=minSpace
    argdict["d"]=space

if args.s != None:
    st=float(args.s)
    argdict["s"]=st
if st<minSt:
    print("Minimum step corrected to "+str(minSt))
    print("")
    st=minSt
    argdict["st"]=st

if args.rf != None:
    rfactor=float(args.rf)
    argdict["rf"]=rfactor
    if rfactor<=0:
        rfactor=1
        argdict["rf"]=rfactor
        print("Red factor corrected to "+str(rfactor))
        print("")

if args.gf != None:
    gfactor=float(args.gf)
    argdict["gf"]=gfactor
    if gfactor<=0:
        gfactor=1
        argdict["gf"]=gfactor
        print("Green factor corrected to "+str(gfactor))
        print("")

if args.bf != None:
    bfactor=float(args.bf)
    argdict["bf"]=bfactor
    if bfactor<=0:
        bfactor=1
        argdict["bf"]=bfactor
        print("Blue factor corrected to "+str(bfactor))
        print("")

print("Current directory:")
curdir=os.getcwd()
print(curdir)
print("")
path=Path(curdir)
adir=str(path)+"/"+stem+"/"

try:
  if not os.path.exists(adir):
    os.mkdir(adir)
except OSError:
  print("Unable to create a directory under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# Create line strength coefficient lists
nums=0
left=[]
mid=[]
right=[]
if isGradientLeft:
    left=np.linspace(st/gradientWidth,st,gradientWidth)
    nums+=gradientWidth
if isGradientRight:
    right=np.linspace(st,st/gradientWidth,gradientWidth)
    nums+=gradientWidth
mid=[st]*(lineWidth-nums)

rc.extend(left)
rc.extend(mid)
rc.extend(right)
rc=np.array(rc)
if not testR:
    if decreaseNonTestColors:
        rc=rc*-1
    else:
        rc=np.array([0]*lineWidth)

gc.extend(left)
gc.extend(mid)
gc.extend(right)
gc=np.array(gc)
if not testG:
    if decreaseNonTestColors:
        gc=gc*-1
    else:
        gc=np.array([0]*lineWidth)
        
bc.extend(left)
bc.extend(mid)
bc.extend(right)
bc=np.array(bc)
if not testB:
    if decreaseNonTestColors:
        bc=bc*-1
    else:
        bc=np.array([0]*lineWidth)

# Read the image to memory
try:
    img=cv2.imread(str(path)+"/"+fname)
    h,w,ch=img.shape
except:
    print("Unable to open: "+fname)
    sys.exit(0)

# Main loop
lines=0
cursor=space
rdiff=[0]*space
gdiff=[0]*space
bdiff=[0]*space
linespos=[]
print("Generating lines:")
while (cursor<w):
    x0=cursor
    y0=0
    x1=x0+lineWidth
    y1=h
    if x1>w:
        break

    # Read a subimage, split to RGB channels, inc or dec RGB values, merge and patch image
    lines+=1

    subimg=img[y0:y1,x0:x1]
    b,g,r=cv2.split(subimg)

    rorig=r.copy()
    r=np.rint(r+rfactor*rc*lines)
    r[r>255]=255
    r[r<0]=0

    gorig=g.copy()
    g=np.rint(g+gfactor*gc*lines)
    g[g>255]=255
    g[g<0]=0

    borig=b.copy()
    b=np.rint(b+bfactor*bc*lines)
    b[b>255]=255
    b[b<0]=0    

    subimg=cv2.merge((b,g,r))
    img[y0:y1,x0:x1]=subimg
    cursor+=lineWidth
    
    # Calculate mean color differences
    i=0
    rd=r-rorig
    gd=g-gorig
    bd=b-borig
    while i<lineWidth:
        rdiff.append(rd[:,i].mean())
        gdiff.append(gd[:,i].mean())
        bdiff.append(bd[:,i].mean())
        i+=1
    
    rdiff=rdiff+[0]*space
    gdiff=gdiff+[0]*space
    bdiff=bdiff+[0]*space
    print(str(lines).rjust(4)+": "+str(x0)+"-"+str(x1-1))
    linespos.append([x0,x1-1])
    cursor+=space

while cursor<w:
    rdiff.append(0)
    gdiff.append(0)
    bdiff.append(0)
    cursor+=1

print("")
print("Lines created: "+str(lines))

print("Saving graphs and data")

# Trim and convert difference arrays
rdiff=np.array(rdiff[:w])
gdiff=np.array(gdiff[:w])
bdiff=np.array(bdiff[:w])
bwdiff=(rdiff+gdiff+bdiff)/3
xs=np.arange(0,w)

# Create and save a log file
logname=stem+".log"
log=[]
log.append("Testlines Log File")
log.append("")
now=datetime.now()
log.append("Time: "+str(now.strftime("%Y-%m-%d, %H:%M:%S")))
log.append("")
log.append("Current directory:")
log.append(curdir)
log.append("")
keylen=0
argstr=""
for key in argdict:
    if len(key)>keylen:
        keylen=len(key)
    if key=="Image":
        argstr=fname+" "
        continue
    elif key in ["r","g","b","dec","left","right","maxy"] and argdict[key]:
        argstr+="-"+key+" "
        continue
    if argdict[key] != False:
        argstr+="-"+key+" "+str(argdict[key])+" "
keylen+=len(": ")
argstr=argstr.strip()
log.append("Image template")
log.append("--------------")
log.append("Name  : "+fname)
log.append("Width : "+str(w))
log.append("Height: "+str(h))
log.append("")

tmp=""
if testR:
    tmp+="R,"
if testG:
    tmp+="G,"
if testB:
    tmp+="B,"
tmp=tmp[:-1]
tmp="Test colors: "+tmp
log.append(tmp)
log.append("")

log.append("Line properties")
log.append("---------------")
log.append("Lines   : "+str(9))
log.append("Width   : "+str(lineWidth))
log.append("Distance: "+str(space))
log.append("Inc/dec : "+str(st)+"/line")
log.append("R factor: "+str(rfactor))
log.append("G factor: "+str(gfactor))
log.append("B factor: "+str(bfactor))

tmp="Decrease: "
if decreaseNonTestColors:
    tmp+="enabled"
else:
    tmp+="disabled"
log.append(tmp)

if argdict["grad"]:
    log.append("Gradient: "+str(gradientWidth))
    tmp="Left gr : "
    if argdict["left"]:
        tmp+="enabled"
    else:
        tmp+="disabled"
    log.append(tmp)
    tmp="Right gr: "
    if argdict["right"]:
        tmp+="enabled"
    else:
        tmp+="disabled"
    log.append(tmp)

log.append("")
tmp="Use maximum y axis scale: "
if maxy:
    tmp+="Yes"
else:
    tmp+="No"
log.append(tmp)

log.append("")
log.append("Command:")
tmp="testlines.py "+argstr
log.append(tmp)

with open(adir+"/"+logname, "w") as file:
    for row in log:
        file.write("%s\n" % row)

# Save line data as a csv file
header=["Line","Start","End"]
with open(adir+"/"+"lines-"+stem+".csv","w",newline="\n") as csvfile:
    writer=csv.writer(csvfile,delimiter=',',quotechar='"')
    writer.writerow(header)
    i=1
    for line in linespos:
        writer.writerow([i,line[0],line[1]])
        i+=1

# Save color differences data
header=["X","Rdiff","Gdiff","Bdiff","Mean"]
with open(adir+"/"+"diff-RGB-"+stem+".csv","w",newline="\n") as csvfile:
    writer=csv.writer(csvfile,delimiter=',',quotechar='"')
    writer.writerow(header)
    for x in xs:
        writer.writerow([x,int(rdiff[x]),int(gdiff[x]),int(bdiff[x]),round(float(bwdiff[x]),3)])

# Save image
patched_img=cv2.imwrite(adir+stem+".png",img)

# Save image with coordinates
fig=plt.figure()
plt.xlabel("X coordinate")
plt.ylabel("Y coordinate")
plt.imshow(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
plt.savefig(adir+"img-"+stem+".png",dpi=300)
plt.close(fig)

# Plot RGB differences
fig=plt.figure()
xlabel="X coordinate"
ylabel="RGB difference(test,template)"
ymins=[rdiff.min(),gdiff.min(),bdiff.min()]
ymaxs=[rdiff.max(),gdiff.max(),bdiff.max()]
if maxy:
    if decreaseNonTestColors:
        ymin=-255
    else:
        ymin=0
    ymax=255
else:
    ymin=min(ymins)
    ymax=max(ymaxs)
plt.xlim(min(xs),max(xs))
plt.ylim(ymin,ymax)
plt.plot(xs,rdiff,color="r",linewidth=linew)
plt.plot(xs,gdiff,"g--",linewidth=linew)
plt.plot(xs,bdiff,"b:",linewidth=linew)
plt.xlabel(xlabel)
plt.ylabel(ylabel)
if grid:
    plt.grid()
plt.savefig(adir+"diff-RGB-"+stem+".png",dpi=300)
plt.close(fig)

# Plot BW differences
fig=plt.figure()
xlabel="X coordinate"
ylabel="BW difference(test,template)"
if maxy:
    if decreaseNonTestColors:
        ymin=-255
    else:
        ymin=0
    ymax=255
else:
    ymin=min(bwdiff)
    ymax=max(bwdiff)
plt.xlim(min(xs),max(xs))
plt.ylim(ymin,ymax)
plt.plot(xs,bwdiff,color="k",linewidth=linew)
plt.xlabel(xlabel)
plt.ylabel(ylabel)
if grid:
    plt.grid()
plt.savefig(adir+"diff-BW-"+stem+".png",dpi=300)
plt.close(fig)
