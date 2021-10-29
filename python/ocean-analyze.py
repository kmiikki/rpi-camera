#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 26 09:42:35 2021

@author: Kim Miikki

"""
import argparse
import csv
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc
from pathlib import Path
from rpi.inputs2 import *

thres_min=0.01
thres_max=0.99
thres_def=0.67
transmission_threshold=5
threshold=thres_def
transmission_label="Transmission (%)"
#max_counts=62145.17
max_y=65535
min_y=0
max_ymarginal=1.05
spectrum=[]
areas=[]

file_format="CSV with a header line"
data_dir="analysis"
ext=".csv"

in_files=[]
in_count=0

write_headers=True

# Default argument values
isPlots=False
isThreshold=True
isGrid=False
isAutoY=False
isTransmission=False
firstAnalyze=True

def transmission_score(ar):
    # Calculate the occurance of 100 in the array
    y=abs(ar.round(0)).astype(int)
    count=np.bincount(y)[100]
    score=100*count/len(y)
    return score

def max_means(ar,threshold=threshold):
    res=[]
    if len(ar)<1:
        return res
    ar.sort(key = lambda i: i[1],reverse=True)
    res=np.array(ar[0])
    mean=ar[0][1]
    i=1
    while (i<len(ar)):       
        if isThreshold:
            if abs(ar[i][1]/mean)<threshold:
                break
        res=np.vstack((res,ar[i]))
        mean=res[:,1].mean()
        i+=1
    return res

def analyze(xs,ys,auc_list):
    global firstAnalyze
    global isTransmission
    
    auc_included=max_means(auc_list,threshold)
    if interval>1:
        if auc_included.ndim==1:
            num=1
        else:
            num=len(auc_included)
    else:
        num=1
    isFirst=True
    spectrum=[]
    if interval>1:
        if auc_included.ndim>1:
            for row in auc_included:            
                idx=int(row[0])
                if isFirst:
                    spectrum=np.array(ys[idx])
                    isFirst=False
                else:
                    spectrum+=ys[idx]
            spectrum/=num
        else:
            if len(auc_included)>0:
                spectrum=ys[int(auc_included[0])]
            else:
                return
    else:
        if auc_included.ndim==1:
            spectrum=ys
        else:
            return
    
    level=transmission_score(spectrum)
    if (not isTransmission) and (firstAnalyze and level>=transmission_threshold):
        print("")
        answer=inputYesNo("transmission mode","Is the spectrum type transmission?",True)
        isTransmission=answer
    if (isTransmission) and (firstAnalyze and level<transmission_threshold):
        print("")
        answer=inputYesNo("normal mode","Is the spectrum type normal?",True)
        isTransmission=not answer
    firstAnalyze=False

    sname="spectrum"    
    if isTransmission:
        sname="transmission-"+sname
        maxy=spectrum.max()
        if level<transmission_threshold:
            print("Low transmission level")
            tsp=spectrum
            #tsp=100*spectrum/maxy
        else:
            tsp=spectrum
    tmp=str(currentFirst).rjust(digits,"0")+"-"+sname+"-mean_("+str(num)+"#"+str(interval)+").csv"
    a=xs.round(3)
    b=spectrum.round(3)
    c=np.vstack((a,b)).T
    with open(data_dir+"/"+tmp, 'w') as file:
        writer = csv.writer(file, delimiter=',')
        if write_headers:
            if not isTransmission:
                writer.writerow([data.columns[0],data.columns[1]])
            else:
                writer.writerow([data.columns[0],transmission_label])
        writer.writerows(c)
    print(tmp)

    if not isTransmission:
        # Plot I=f(wavelength)
        fig=plt.figure()
        plt.xlabel(data.columns[0])
        plt.ylabel(data.columns[1])    
        plt.xlim(xs[0],xs[-1])
        if isAutoY:
            plt.ylim(spectrum.min(),max_ymarginal*spectrum.max())
        else:
            plt.ylim(0,max_y)
        if isGrid:
            plt.grid()
        plt.plot(xs,spectrum)
        tmp=str(currentFirst).rjust(digits,"0")+"-"+sname+"-mean_("+str(num)+"#"+str(interval)+").png"
        plt.savefig(data_dir+"/"+tmp,dpi=300)
        if isPlots:
            plt.show()
        plt.close(fig)

    if isTransmission:
        # Plot T-%=f(wavelength)
        fig=plt.figure()
        plt.xlabel(data.columns[0])
        plt.ylabel(transmission_label)    
        plt.xlim(xs[0],xs[-1])
        if isAutoY:
            plt.ylim((1-max_ymarginal)*100,max_ymarginal*100)
        else:
            plt.ylim(0,102)
        if isGrid:
            plt.grid()
        plt.plot(xs,tsp)
        tmp=str(currentFirst).rjust(digits,"0")+"-"+sname+"-mean_("+str(num)+"#"+str(interval)+").png"
        plt.savefig(data_dir+"/"+tmp,dpi=300)
        if isPlots:
            plt.show()
        plt.close(fig)

    return

parser=argparse.ArgumentParser()
parser.add_argument("-s", type=int, help="scans/spectrum", required=False)
parser.add_argument("-t", type=float, help="threshold value: 0.01-0.99", required=False) # 0.01-0.99
parser.add_argument("-d", action="store_true", help="display images on screen",required=False)
parser.add_argument("-i", action="store_true", help="ignore threshold",required=False)
parser.add_argument("-g", action="store_true", help="enable grid",required=False)
parser.add_argument("-y", action="store_true", help="auto y axis",required=False)
parser.add_argument("-ts", action="store_true", help="transmission spectra",required=False)
args = parser.parse_args()

print("Ocean spectrometer CSV spectra analyzer")
print("File format: ",end="")
print(file_format)

if args.s != None:
    interval=int(args.s)
    if interval<1:
        print("Interval set to: 1")
        interval=1
if args.t != None:
    if args.i != None:
        threshold=float(args.t)
        if threshold<thres_min:
            print("Threshold set to: "+str(thres_min))
            threshold=thres_min
        elif threshold>thres_max:
            print("Threshold set to: "+str(thres_max))
            threshold=thres_max
if args.d:
    isPlots=True
if args.i:
    print("Threshold disabled")
    isThreshold=False
if args.g:
    isGrid=True
if args.y:
    isAutoY=True
if args.ts:
    isTransmission=True

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

# Calculate data files
# --------------------
# File template:
# 00-20211021_FLMT044961__0__16.csv
firstFound=False
firstVal=-1
digits=0
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    if suffix==ext:
        fname=p.name
        pos=fname.find("-")
        if not firstFound:
            if pos<1:
                continue
            try:
                firstVal=int(fname[:pos])
            except:
                continue
            if firstVal<0:
                continue
            digits=pos
            firstFound=True
        else:
            if pos != digits:
                continue
            try:
                tmp=int(fname[:pos])
            except:
                continue
        in_files.append(fname)
in_count=len(in_files)
if args.s != None:
    if interval>in_count:
        print("Interval set to: "+str(in_count))
        interval=in_count

if in_count==0:
    print("No data files found!")
    sys.exit(0)

try:
  if not os.path.exists(data_dir):
    os.mkdir(data_dir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

if args.s == None:  
    interval=inputValue("scans/spectrum:",1,in_count,1,"","Interval is out of range!",True)

i=0
filenum=0
ar=[]
auc_list=[]
firstFile=True
currentFirst=-1
print("")
print("Processing:")
while (i<in_count):
    data=pd.read_csv(in_files[i], dtype=float, delimiter=",")

    if len(data.columns) != 2:
        print("! "+in_files[i]+": skipped, columns != 2")
        i+=1
        continue

    if firstFile:
        filenum=0
        currentFirst=i
        firstFile=False
        xs=np.array(data.iloc[:,0])
        ys=np.array(data.iloc[:,1])
        area=auc(xs,ys)
        auc_list.append([filenum,area])
        areas.append([i,area])
    else:
        filenum+=1
        yvals=np.array(data.iloc[:,1])
        area=auc(xs,yvals)
        auc_list.append([filenum,area])
        areas.append([i,area])
        ys=np.vstack((ys,yvals))
        
    print(in_files[i])
    if (i+1) % interval==0:
        analyze(xs,ys,auc_list)
        firstFile=True
        currentFirst=-1
        auc_list=[]
        if (i+1)<in_count:
            print("")
        
    i+=1
if filenum+1 < interval:
    analyze(xs,ys,auc_list)

# Write spectra areas files
print("")
print("Saving area files")
tmp="spectra-areas.csv"
with open(data_dir+"/"+tmp, 'w') as file:
    writer = csv.writer(file, delimiter=',')
    if write_headers:
        writer.writerow(["spectrum","area"])
        for row in areas:
            writer.writerow([row[0],int(round(row[1]))])
if i>0:
    tmp="spectra-areas.png"
    areas=np.array(areas)
    areas=areas.T
    fig=plt.figure()
    plt.xlabel("Spectrum")
    plt.ylabel("Area")    
    plt.xlim(areas[0][0],areas[0][-1])
    plt.plot(areas[0],areas[1])
    if isGrid:
        plt.grid()
    plt.savefig(data_dir+"/"+tmp,dpi=300)
    if isPlots:
        plt.show()
    plt.close(fig)
