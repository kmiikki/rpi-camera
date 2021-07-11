#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 9 11:37:00 2021

@author: Kim Miikki
"""

import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np 
import os
import sys
from pathlib import Path
from rpi.inputs2 import *
from scipy.signal import savgol_filter

decimals=2
cols=0
brtype="()"
#brtype="[]"
capitalnames=True
changebrackets=True
delimiter=","
xlabel=""
scale_y=True
display_mode=False


title=""
alpha=0.5
linew_min=0.1
linew_max=2.0
linew_default=1.0
grid=True

def parseName(name):
    name=name.strip()
    l=len(name)
    if l==0:
        return
    
    if capitalnames:
        if l>1:
            name=name[0].upper()+name[1:]
        else:
            name=name.upper()
        
    if changebrackets:
        if brtype=="()":
            oldbr="[]"
        else:
            oldbr="()"
        oldsbr=oldbr[0]
        oldebr=oldbr[1]
        sbr=brtype[0]
        ebr=brtype[1]
        name=name.replace(oldsbr,sbr)
        name=name.replace(oldebr,ebr)
        
    return name

def movingaverage (values, window):
    weights = np.repeat(1.0, window)/window
    sma = np.convolve(values, weights, "valid")
    return sma

# Read and parse program arguments
parser=argparse.ArgumentParser()
parser.add_argument("file", type=Path, help="XY data file (*.csv)")
parser.add_argument("-p", action="store_true", help="plot graphs on screen")
args = parser.parse_args()

if os.path.isfile(args.file):
    stem=args.file.stem
    fname=str(args.file.name)
else:
    print("File "+str(args.file)+" not found!")
    sys.exit(0)

if args.p:
    display_mode=True

print("XY smooth graph, (C) Kim Miikki 2021")
print("")

# Read a XY file
data=[]
try:
    with open(args.file,"r",newline="") as csvfile:
        csvreader=csv.reader(csvfile,delimiter=delimiter)
        header=next(csvreader)
        ar=[]
        for name in header:
            ar.append(parseName(name))
        cols=len(ar)
        data.append(ar)
        for row in csvreader:
            ar=[]
            i=0
            for element in row:
                if i==0:
                    ar.append(element)
                else:
                    try:
                        ar.append(float(element))
                    except:
                        ar.append(element)
                i+=1
            data.append(ar)

except:
    result=False

# Convert table to a numpy array 
d=np.array(data)

# Transpose the array
d=d.T

# Remove the first column and convert the array to float type
d=d[..., 1:]
d=d.astype(float)

# Get the X array
xs=d[0]

"""
Graph smoothing section

Methods: Savgol and Moving Average
"""

print("Data smoothing method:")
print("1 = Moving average")
print("2 = Savitsky-Golay")
methods=[1,2]
sel_method=inputListValue("smoothing method",methods,2,"Not a valid method selected!")
print("")
title_on=inputYesNo("title mode","Add titles to graphs",True)

# Smooth data array
sdata=[data[0]]

# Moving average method
if sel_method==1:
    xmin=2
    xmax=len(data)-1
    window=inputValue("window:",xmin,xmax,2,"","Window size is out of range!",True)
    title="Moving Average (width "+str(window)+")"
    ys=movingaverage(d[1],window)
    
    xs_ma=xs[window-1:]
    ys_ma=ys
    
    i=0
    while i<len(xs_ma):
        sdata.append([xs_ma[i],ys_ma[i]])
        i+=1

# Savitzky-Golay filtering method
if sel_method==2:
    xmin=3
    xmax=len(data)//4
    if xmax % 2 == 0:
        xmax-=1
    if xmax<xmin:
        xmax=len(data)-1
        if xmax % 2 == 0:
            xmax-=1
    if xmax<xmin:
        print("Too few data points for Savgol smoothing.")
        sys.exit(0)
    
    default=xmin
    while True:
        try:
            window=input("Select window size (odd number "+str(xmin)+"-"+str(xmax)+"; Default="+str(default)+"): ")
            if window=="":
                window=default
                print("default selected")
                break
            window=int(window)
            if window<xmin or window>xmax:
                print("Selection is out of range!")
                continue
            if window%2==0:
                print(str(window)+" is an even number!")
                continue
            break
        except:
            print("Invalid selection!")
    
    title="Savitzky-Golay (width "+str(window)+", quadratic polynomial)"
    ys=savgol_filter(d[1], window_length=window, polyorder=2, deriv=0)

    half_window=(window-1)//2
    xs_sg=xs[half_window:-half_window]
    ys_sg=ys[half_window:-half_window]
    
    i=0
    while i<len(xs_sg):
        sdata.append([xs_sg[i],ys_sg[i]])
        i+=1

# Save smooth data
# sdma = smooth data, moving average
# sdsg = smooth data, savgol
newcsv=""
if sel_method==1:
    newcsv="sdma-"+fname
elif sel_method==2:
    newcsv="sdsg-"+fname
if newcsv!="":
    with open(newcsv, 'w') as file:
        writer = csv.writer(file)
    
        # write the header
        writer.writerow(sdata[0])
    
        sd=np.array(sdata[1:])
        sd=sd.T
        st=sd[0]
        sd=np.around(sd[1:],decimals)
        sd=np.concatenate(([st],sd),axis=0).T
        
        # write multiple rows
        writer.writerows(sd)
    
# Plot parameters
linew=inputValue("Line width",linew_min,linew_max,linew_default,"","Width out of range!",False)
scale_y=inputYesNo("Auto scale","Y axis auto scale",scale_y)
grid=inputYesNo("Grid","Enable grid",grid)

basename=stem+".png"
sd=sd.T
y_mind=d[1].min()
y_maxd=d[1].max()
y_mins=sd[1].min()
y_maxs=sd[1].max()

## Plot XY smooth graph
fig=plt.figure()
plt.xlim(sd[0].min(),sd[0].max())
if scale_y:
    plt.ylim(y_mins,y_maxs)
else:
    plt.ylim(0,y_maxs)
plt.plot(sd[0],sd[1],color="k",linewidth=linew)
plt.xlabel(sdata[0][0])
plt.ylabel(sdata[0][1])
if title_on:
    plt.title(title)
if grid:
    plt.grid()
plt.savefig("sgXY-"+basename,dpi=300)
if display_mode:
    plt.show()        
plt.close(fig)
    
## Plot RGB mean smooth graph + original data
fig=plt.figure()
plt.xlim(d[0].min(),d[0].max())
if scale_y:
    plt.ylim(y_mind,y_maxd)
else:
    plt.ylim(0,y_maxd)
plt.scatter(d[0],d[1],color="k",s=1,alpha=alpha,marker=",")
plt.plot(sd[0],sd[1],color="k",linewidth=linew)
plt.xlabel(sdata[0][0])
plt.ylabel(sdata[0][1])
if title_on:
    plt.title(title)
if grid:
    plt.grid()
plt.savefig("sgoXY-"+basename,dpi=300)
if display_mode:
    plt.show()        
plt.close(fig)
