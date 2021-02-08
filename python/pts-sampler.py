#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 12:36:44 2021

@author: Kim Miikki

Usage:
pts-sampler filename interval
filename = file.pts
interval = time stamps interval as integer

"""

import sys

filename=""
interval=0

outfile="timelabels.pts"
displayHelp=False
error=False

print("PTS-sampler\n")
if len(sys.argv)==1:
    displayHelp=True
elif len(sys.argv)==2:
    if sys.argv[1].lower()=="-h":
        displayHelp=True
    else:
        error=True
        displayError=True
elif len(sys.argv)==3:
    try:
        filename=sys.argv[1]
        interval=int(sys.argv[2])
    except:
        print("Invalid arguments")
        error=True
elif len(sys.argv)>3:
    print("Too many arguments!")
    error=True

if displayHelp or error:
    print("Usage:")
    print("pts-sampler filename interval")
else:
    i=0
    firstLine=True
    samples=[]
    with open(filename) as reader:
        for line in reader:
            if firstLine:
                firstLine=False
                continue
            r=i % interval
            if r==0:
                samples.append(line)
            i+=1
    if len(samples)>0:
        try:
            with open(outfile,"w") as fp:
                fp.writelines(samples)
            print(str(len(samples))+" of "+str(i)+" presentation time stamps sampled.")
        except:
            print("Unable to write: "+outfile)