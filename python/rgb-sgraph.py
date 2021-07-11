#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 18 09:24:37 2021

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
bw_replace=True
xlabel=""
scale_y=True
display_mode=False


title=""
alpha=0.5
linew_min=0.1
linew_max=2.0
linew_default=1.0
bw_plot=True
r_plot=True
g_plot=True
b_plot=True
grid=True

def parseName(name):
    name=name.strip()
    if bw_replace:
        if name=="bw":
            name="gray scale"
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
parser.add_argument("file", type=Path, help="RGB data file (*.csv)")
parser.add_argument("-p", action="store_true", help="plot calibration graphs on screen")
args = parser.parse_args()

if os.path.isfile(args.file):
    stem=args.file.stem
    fname=str(args.file.name)
else:
    print("File "+str(args.file)+" not found!")
    sys.exit(0)

if args.p:
    display_mode=True

print("RGB smooth graph, (C) Kim Miikki 2021")
print("")

# Read a RGB file
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

# Transpose and remove the first line
d=d.T[1:]

# Remove the first column and convert the array to float type
d=d[..., 1:]
d=d.astype(float)

# Get a time array
ts=d[0]

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
customx=inputYesNo("custom label","Custom X axis label",False)
if customx:
    xlabel=input("Enter X axis label: ")
    data[0][1]=xlabel

# Smooth data array
sdata=[data[0]]

# Moving average method
if sel_method==1:
    xmin=2
    xmax=len(data)-1
    window=inputValue("window:",xmin,xmax,2,"","Window size is out of range!",True)
    title="Moving Average (width "+str(window)+")"
    bw=movingaverage(d[1],window)
    r=movingaverage(d[2],window)
    g=movingaverage(d[3],window)
    b=movingaverage(d[4],window)
    
    ts_ma=ts[window-1:]
    bw_ma=bw
    r_ma=r
    g_ma=g
    b_ma=b
    
    i=0
    while i<len(ts_ma):
        sdata.append([ts_ma[i],bw_ma[i],r_ma[i],g_ma[i],b_ma[i]])
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
    bw=savgol_filter(d[1], window_length=window, polyorder=2, deriv=0)
    r=savgol_filter(d[2], window_length=window, polyorder=2, deriv=0)
    g=savgol_filter(d[3], window_length=window, polyorder=2, deriv=0)
    b=savgol_filter(d[4], window_length=window, polyorder=2, deriv=0)

    half_window=(window-1)//2
    ts_sg=ts[half_window:-half_window]
    bw_sg=bw[half_window:-half_window]
    r_sg=r[half_window:-half_window]
    g_sg=g[half_window:-half_window]
    b_sg=b[half_window:-half_window]
    
    i=0
    while i<len(ts_sg):
        sdata.append([ts_sg[i],bw_sg[i],r_sg[i],g_sg[i],b_sg[i]])
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
all_plot=inputYesNo("Grayscale and RGB plots","Plot all channels",True)
if not all_plot:
    bw_plot=inputYesNo("Grayscale plot","Grayscale enabled",bw_plot)
    r_plot=inputYesNo("R channel plot","R channel enabled",r_plot)
    g_plot=inputYesNo("G channel plot","G channel enabled",g_plot)
    b_plot=inputYesNo("B channel plot","B channel enabled",b_plot)
grid=inputYesNo("Grid","Enable grid",grid)

basename=stem+".png"
sd=sd.T
bw_mind=d[1].min()
bw_maxd=d[1].max()
bw_mins=sd[1].min()
bw_maxs=sd[1].max()

rgb_mind=[]
rgb_maxd=[]
rgb_mins=[]
rgb_maxs=[]

if r_plot:
    rgb_mind.append(d[2].min())
    rgb_maxd.append(d[2].max())
    rgb_mins.append(sd[2].min())
    rgb_maxs.append(sd[2].max())

if g_plot:
    rgb_mind.append(d[3].min())
    rgb_maxd.append(d[3].max())
    rgb_mins.append(sd[3].min())
    rgb_maxs.append(sd[3].max())

if b_plot:
    rgb_mind.append(d[4].min())
    rgb_maxd.append(d[4].max())
    rgb_mins.append(sd[4].min())
    rgb_maxs.append(sd[4].max())

## Plot RGB mean smooth graph
if True in [r_plot,g_plot,b_plot]:
    fig=plt.figure()
    plt.xlim(sd[0].min(),sd[0].max())
    if scale_y:
        plt.ylim(min(rgb_mins),max(rgb_maxs))
    else:
        plt.ylim(0,255)
    if r_plot:
        plt.plot(sd[0],sd[2],color="r",linewidth=linew)
    if g_plot:
        plt.plot(sd[0],sd[3],color="g",linewidth=linew)
    if b_plot:
        plt.plot(sd[0],sd[4],color="b",linewidth=linew)
    plt.xlabel(sdata[0][1])
    plt.ylabel("RGB mean value")
    if title_on:
        plt.title(title)
    if grid:
        plt.grid()
    plt.savefig("sgRGB-"+basename,dpi=300)
    if display_mode:
        plt.show()        
    plt.close(fig)

## Plot RGB mean smooth graph + original data
if True in [r_plot,g_plot,b_plot]:
    fig=plt.figure()
    plt.xlim(d[0].min(),d[0].max())
    if scale_y:
        plt.ylim(min(rgb_mind),max(rgb_maxd))
    else:
        plt.ylim(0,255)
    if r_plot:
        plt.scatter(d[0],d[2],color="r",s=1,alpha=alpha,marker=",")
    if g_plot:
        plt.scatter(d[0],d[3],color="g",s=1,alpha=alpha,marker=",")
    if b_plot:
        plt.scatter(d[0],d[4],color="b",s=1,alpha=alpha,marker=",")
    if r_plot:
        plt.plot(sd[0],sd[2],color="r",linewidth=linew)
    if g_plot:
        plt.plot(sd[0],sd[3],color="g",linewidth=linew)
    if b_plot:
        plt.plot(sd[0],sd[4],color="b",linewidth=linew)
    plt.xlabel(sdata[0][1])
    plt.ylabel("RGB mean value")
    if title_on:
        plt.title(title)
    if grid:
        plt.grid()
    plt.savefig("sgoRGB-"+basename,dpi=300)
    if display_mode:
        plt.show()        
    plt.close(fig)

if bw_plot:
    ## Plot gray mean smooth graph
    fig=plt.figure()
    plt.xlim(sd[0].min(),sd[0].max())
    if scale_y:
        plt.ylim(bw_mins,bw_maxs)
    else:
        plt.ylim(0,255)
    plt.plot(sd[0],sd[1],color="k",linewidth=linew)
    plt.xlabel(sdata[0][1])
    plt.ylabel("Grayscale mean value")
    if title_on:
        plt.title(title)
    if grid:
        plt.grid()
    plt.savefig("sgBW-"+basename,dpi=300)
    if display_mode:
        plt.show()        
    plt.close(fig)
    
    ## Plot RGB mean smooth graph + original data
    fig=plt.figure()
    plt.xlim(d[0].min(),d[0].max())
    if scale_y:
        plt.ylim(bw_mind,bw_maxd)
    else:
        plt.ylim(0,255)
    plt.scatter(d[0],d[1],color="k",s=1,alpha=alpha,marker=",")
    plt.plot(sd[0],sd[1],color="k",linewidth=linew)
    plt.xlabel(sdata[0][1])
    plt.ylabel("Grayscale mean value")
    if title_on:
        plt.title(title)
    if grid:
        plt.grid()
    plt.savefig("sgoBW-"+basename,dpi=300)
    if display_mode:
        plt.show()        
    plt.close(fig)
