#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 16 12:31:59 2021

@author: Kim Miikki
"""
import csv
import cv2
import numpy as np
import os
import sys
from datetime import datetime
from pathlib import Path
from rpi.inputs2 import *

pt_dir="pt"
dst_dir=""
ptm_file="ptmdata.csv" # Perspective transformation matrix and data
src_format=""
dst_format=".jpg"
isJPG=False
isPNG=False
isAll=False
M=[]
tx=0
ty=0

def parse_ptmdata():  
    #result=False
    #posList=[]
    ptList=[]
    eptList=[]
    m=[]
    w=0
    h=0
    ptm=[]
    eptm=[]
    ptm_score=0
    eptm_score=0
    filename=""
    search=["# Perspective transformation matrix","# PTS2",
            "# Extended perspective transformation matrix","# EPTS2"]
    index=0
    try:
        with open(ptm_file, "r") as file:
            reader = csv.reader(file, delimiter = ",")
            for row in reader:
                if search[index] in row:

                    # Perspective transformation matrix
                    if index==0:
                        for i in range(3):
                            line=next(reader)
                            if len(line)==3:
                                try:
                                    a1=float(line[0])
                                    a2=float(line[1])
                                    a3=float(line[2])
                                    ptm.append([a1,a2,a3])
                                except:
                                    pass
                                else:
                                    ptm_score+=1
                    
                    # PTS2
                    if index==1:
                        for i in range(4):
                            line=next(reader)
                            if len(line)==2:
                                try:
                                    x=int(line[0])
                                    y=int(line[1])
                                    ptList.append([x,y])
                                except:
                                    pass
                                else:
                                    ptm_score+=1

                    # Extended perspective transformation matrix
                    if index==2:
                        for i in range(3):
                            line=next(reader)
                            if len(line)==3:
                                try:
                                    a1=float(line[0])
                                    a2=float(line[1])
                                    a3=float(line[2])
                                    eptm.append([a1,a2,a3])
                                except:
                                    pass
                                else:
                                    eptm_score+=1
                    
                    # EPTS2
                    if index==3:
                        for i in range(4):
                            line=next(reader)
                            if len(line)==2:
                                try:
                                    x=int(line[0])
                                    y=int(line[1])
                                    eptList.append([x,y])
                                except:
                                    pass
                                else:
                                    eptm_score+=1

                    index+=1
                if index==len(search):
                    break
    except:
        pass

    if eptm_score==7:
        print("Extended transformation matrix found:")
        m=np.float32(eptm)
        matprint(m)
        print("")
        print("Transformed image size:")
        w=eptList[3][0]
        h=eptList[3][1]
        print(str(w)+"x"+str(h))
        print("")
    elif ptm_score==7:
        print("Transformation matrix found:")
        m=np.float32(ptm)
        matprint(m)
        print("")
        print("Transformed image size:")
        w=ptList[3][0]
        h=ptList[3][1]
        print(str(w)+"x"+str(h))
        print("")
        
    return m,w,h

def matprint(mat, fmt="g"):
    col_maxes = [max([len(("{:"+fmt+"}").format(x)) for x in col]) for col in mat.T]
    for x in mat:
        for i, y in enumerate(x):
            print(("{:"+str(col_maxes[i])+fmt+"}").format(y), end="  ")
        print("")

print("Perspective transformation batch tool for images")
print("")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
print("Current directory:")
print(curdir)
print("")

try:
    if not os.path.exists(pt_dir):
        os.mkdir(pt_dir)
except OSError:
    print("Unable to create a directory or directories under following path:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)
dst_dir=curdir+"/"+pt_dir+"/"

M,tx,ty=parse_ptmdata()
if len(M)==0:
    print("Perspective transformation matrix not found!")
    print("The program is terminated.")
    sys.exit(1)

# Open the ptdata.csv file
isJPG=inputYesNo("jpg format","Input file format JPG",True)
if not isJPG:
    isPNG=inputYesNo("png format","Input file format PNG",True)
    if not isPNG:
        isAll=inputYesNo("* format","Input file format *",True)
        if not isAll:
            ask=True
            while ask:
                try:
                    src_format=input("Enter input file extension: ")
                    src_format=src_format.strip()
                    src_format=src_format.lower()
                    if not src_format[0]==".":
                        src_format="."+src_format
                    if len(src_format)<=1:
                        raise Exception("Not a valid extension.")
                    ask=False
                except:
                    print("Select a valid extension: .ext or ext")

if isJPG:
    src_format=".jpg"
elif isPNG:
    src_format=".png"

# Create a log file
file=open("ptbatch.log","w")
file.write("PTBatch - Perspective Transformation Batch Tool\n\n")
file.write("Source directory: "+curdir+"\n")
file.write("Sample directory: "+dst_dir+"\n\n")
writer=csv.writer(file,delimiter=",")
file.write("# Perspective transformation matrix\n")
writer.writerows(M)
file.write("\n")
file.write("# Transformed images size\n")
file.write(str(tx)+"x"+str(ty))
file.write("\n\n")

transformed=0
t1=datetime.now()
for p in sorted(path.iterdir()):
    if p.is_file():
        # Skip the ptmdata.csv file
        if p.name==ptm_file:
            continue
        if not isAll:
            ext=p.suffix.lower()
            if isJPG and ext!=src_format:
                continue
            if isPNG and ext!=src_format:
                continue
        if transformed==0:
            print("\nProcessing:")
        try:
            print(p.name)
            img=cv2.imread(p.name)
        except:
            print("Unable to open: "+p.name)
        finally:
            # Perspective tranformation
            if img is None:
                print("-> skip file")
            else:
                try:
                    img=cv2.warpPerspective(img,M,(tx,ty))
                    cv2.imwrite(dst_dir+"pt-"+p.name,img)
                finally:
                    transformed+=1
t2=datetime.now()
file.write("Files transformed: "+str(transformed)+"\n")
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
print("\nFiles transformed: "+str(transformed))
print("Time elapsed: "+str(t2-t1))