#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Live video preview with blur detection
Method: Variance of the Laplacian

Server mode
===========
Requirements: Client and server has to be ran in the same directory
Role:         Server
Server:       capture-sharpness.py
Execute:      capture-sharpness.py -s

Created on Thu Oct 21 2020

@author: Kim Miikki
"""

import os
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import cv2
import csv

SERVER_MODE=False
ENABLE_TEMP_VAR=True
DELETE_LAST_TEMP_VAR=True
MAX_VALUES=50

def variance_of_laplacian(image):
	# compute the Laplacian of the image and then return the focus
	# measure, which is simply the variance of the Laplacian
	return cv2.Laplacian(image, cv2.CV_64F).var()

def new_varfile(i,v):
    global varfile
    global varfile_old
    varfile=varfile_base+";"+str(i)+";"+str(v)
    if varfile_old=="":
        varfile_old=varfile
    else:
        if os.path.exists(varfile_old):
            os.remove(varfile_old)
    varfile_old=varfile
    open(varfile,"w").close()

TAB=9
ESC=27
SPACE=32
c=ord("c")
C=ord("C")
s=ord("s")
S=ord("S")

subdir="sharpness"
name="var"
digits=4
varfile_base="_var"
varfile=""
varfile_old=""
delimiter=";"

# Colors: black, white, red, blue, green
colors=[(0,0,0),
        (255,255,255),
        (0,0,255),
        (255,0,0),
        (0,255,0)]
color=2

Enable_HD=False
Enable_Temp_var_default=ENABLE_TEMP_VAR
arguments=len(sys.argv)

print("Monitor sharpness") # ... and capture pictures
print("")

alist=[]
if arguments==2:
    alist.append(sys.argv[1].upper())
elif arguments==3:
    alist.append(sys.argv[1].upper())
    alist.append(sys.argv[2].upper())

if arguments==1:
    print("Default capture mode enabled.")
    print("HD mode    : -HD")
    print("Server mode: -S")
if "-HD" in alist:    
        print("HD capture mode enabled")
        Enable_HD=True
if "-S" in alist:
        print("Server mode enabled")
        ENABLE_TEMP_VAR=True
        SERVER_MODE=True
print("")
print("Capture image: C")
print("Toggle server: S")
print("Text color   : TAB")
print("Exit program : ESC")

# Open video capture
cap = cv2.VideoCapture(0)
if Enable_HD:
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
if not cap.isOpened():
    print("Cannot open camera")
    exit(0)

# Create figure for monitoring sharpness
fig=plt.figure()
ax=fig.add_subplot(1,1,1)
xs=[]
ys=[]
var=0
oldvar=0

i=1
oldi=i
varlist=[]
varlist.append(["File","Number","Variance"])
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    var = variance_of_laplacian(gray)
    cv2.putText(frame, "Sharpness: {:d}".format(int(var)), (10, 60),
		cv2.FONT_HERSHEY_SIMPLEX, 2, colors[color], 3)
    # Display the resulting frame
    cv2.imshow('Camera live preview',frame)

    key=0
    key=cv2.waitKey(1)
    if key in [s,S]:
        SERVER_MODE=not SERVER_MODE
        if SERVER_MODE:
            ENABLE_TEMP_VAR=True
        else:
            ENABLE_TEMP_VAR=Enable_Temp_var_default
    if key in [c,C]:
        basename=name+str(i).zfill(4)+".png"
        filename=subdir+"/"+basename
        if i==1:
            if not os.path.exists(subdir):
                os.mkdir(subdir)
            print("\nCapture:")
        print(filename)
        cv2.imwrite(filename,gray)
        xs.append(i)
        ys.append(var)
        varlist.append([basename,i,var])
        i+=1        
    elif key==ESC:
        break
    elif key==TAB:
        color+=1
        if color>len(colors)-1:
            color=0
    if ENABLE_TEMP_VAR:
        if i>oldi:
            new_varfile(oldi,var)
            oldi=i
        elif SERVER_MODE:
            if int(var)!=int(oldvar):
                new_varfile(oldi,var)
                oldvar=var

# When everything done, release the capture
if not varfile=="" and DELETE_LAST_TEMP_VAR:
    if os.path.exists(varfile):
        os.remove(varfile)    
cap.release()
cv2.destroyAllWindows()
if len(xs)>0:
    with open("var.txt","w",newline="") as csvfile:
        csvwriter=csv.writer(csvfile,delimiter=delimiter)
        for s in varlist:
            csvwriter.writerow(s)

    figname="varfig.png"
    plt.title("Variance of the Laplacian")
    plt.xlabel("Image number")
    plt.ylabel("Variance")
    ax.plot(xs,ys)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.savefig(figname,dpi=(300))
    plt.show()
plt.close("all")

