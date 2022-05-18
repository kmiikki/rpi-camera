#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 17 08:40:12 2022

@author: Kim Miikki

Calculate RGB and BW histograms of all images in current directory

Low threshold: 0 < High threshold (default 0)
High threshold: Low threshold < High threshold <=255 (default 255)

prefixes:
RGB: histrgb-
BW:  histbw-

suffixes:
.png (histogram plot)
.csv (histogram data)

Text stems for csv files:
data    (histogram data)
results (series)

"""

import argparse
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import cv2
import numpy as np

np.set_printoptions(suppress=True)

extensions=['.png','.jpg','.bmp','.tif','.tiff','.dib','.jpeg','.jpe',',pbm','.pgm','.ppm','.sr','.ras']

stem=''
filename=''
minThreshold=0
maxThreshold=255
outdir="rgb"
defaultExt=".png"
results=[]
decimals=2

parser=argparse.ArgumentParser()
parser.add_argument('-low',type=int,help='low threshold (0-254, default 0)',required=False)
parser.add_argument('-high',type=int,help='high threshold (1-255, default 255)',required=False)
args = parser.parse_args()

if args.low != None:
    v=int(args.low)
    if v<0:
        minThreshold=0
    elif v>254:
        minThreshold=254
    else:
        minThreshold=v

if args.high != None:
    v=int(args.high)
    if v<1:
        maxThreshold=255
    elif v>255:
        maxThreshold=255
    elif v<=minThreshold:
        maxThreshold=255
    else:
        maxThreshold=v

print('RGB histograms 1.0, (c) Kim Miikki 2022')
print('')
print('Current directory:')
curdir=os.getcwd()
print(curdir)
print('')
path=Path(curdir)
adir=str(path)+'/'+outdir+'/'

try:
  if not os.path.exists(outdir):
    os.mkdir(outdir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)
  
# Generate a list of input files ond output file stems
infiles=[]
outstems=[]
for p in sorted(path.iterdir()):
    suffix=p.suffix.lower()
    if p.is_file() and suffix in extensions:
        fname=p.name
        infiles.append(fname)
        outstems.append(p.stem+'-'+p.suffix[1:])

# Process all image files
num=0
vals=np.linspace(0,255,256)
colors=('r','g','b')
t1=datetime.now()                
if len(infiles)>0:
    print("Processing:")
for name in infiles:
    try:
        img=cv2.imread(name)
        h,w,ch=img.shape
    except:
        print(' - Unable to open: '+name)
        continue
    print(str(num+1)+'/'+str(len(infiles))+': '+name+', size '+str(w)+'x'+str(h))
    
    # Get color channels
    b,g,r=cv2.split(img)
    bw=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    # Calculate R, G, B and BW histograms
    hr=cv2.calcHist([r],[0],None,[256],[0, 256])
    hg=cv2.calcHist([g],[0],None,[256],[0, 256])
    hb=cv2.calcHist([b],[0],None,[256],[0, 256])
    hist=cv2.calcHist([bw],[0],None,[256],[0, 256])
    histograms=np.hstack((hist,hr,hg,hb)).astype(int)

    # Count low threshold values
    lowr=int(hr[:minThreshold+1].sum())
    lowg=int(hg[:minThreshold+1].sum())
    lowb=int(hb[:minThreshold+1].sum())
    lowbw=int(hist[:minThreshold+1].sum())

    # Count high threshold values
    highr=int(hr[maxThreshold:].sum())
    highg=int(hg[maxThreshold:].sum())
    highb=int(hb[maxThreshold:].sum())
    highbw=int(hist[maxThreshold:].sum())
    
    # Weights
    bw_weights=(hist/hist.sum()).T[0]
    rweights=(hr/hr.sum()).T[0]
    gweights=(hg/hg.sum()).T[0]
    bweights=(hb/hb.sum()).T[0]

    bw_mean=round(np.average(vals,weights=bw_weights),decimals)
    r_mean=round(np.average(vals,weights=rweights),decimals)
    g_mean=round(np.average(vals,weights=gweights),decimals)
    b_mean=round(np.average(vals,weights=bweights),decimals)

    # Write histograms to a file
    #np.savetxt(adir+'data-'+outstems[num]+'.csv',histograms,delimiter=',')
    with open(adir+'data-'+outstems[num]+'.csv','w',newline='') as csvfile:
        csvwriter=csv.writer(csvfile,delimiter=',')
        csvwriter.writerows(histograms)
    

    # result row:
    # filename, minThreshold, maxThreshold,  lowbw, highbw, r_mean, lowr, highr, g_mean, lowg, highg, b_mean, lowb, highb
    results.append([name, minThreshold, maxThreshold,  lowbw, highbw, r_mean, lowr, highr, g_mean, lowg, highg, b_mean, lowb, highb])
    
    # Plot BW and RGB figures
    fig=plt.figure()
    plt.xlabel('Color value')
    plt.ylabel('Pixel count')
    plt.plot(hr, color='r')
    plt.plot(hg, color='g')
    plt.plot(hb, color='b')
    plt.xlim([0, 256])
    if minThreshold>0:
        plt.axvline(x=minThreshold,color='0.8',linestyle='--')
    if maxThreshold<255:
        plt.axvline(x=maxThreshold,color='0.8',linestyle='--')
    plt.grid()
    plt.savefig(adir+'histrgb-'+outstems[num]+'.png',dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    fig=plt.figure()
    plt.xlabel('Gray value')
    plt.ylabel('Pixel count')
    plt.plot(hist, color='k')
    plt.xlim([0, 256])
    if minThreshold>0:
        plt.axvline(x=minThreshold,color='0.8',linestyle='--')
    if maxThreshold<255:
        plt.axvline(x=maxThreshold,color='0.8',linestyle='--')
    plt.grid()        
    plt.savefig(adir+'histbw-'+outstems[num]+'.png',dpi=300,bbox_inches='tight')
    plt.close(fig)
    
    num+=1

header=['filename','minThreshold','maxThreshold','low_bw','high_bw','r_mean','low_r','high_r','g_mean','low_g','high_g','b_mean','low_b','high_b']
if len(results)>0:
    with open(adir+'results.csv','w',newline='') as csvfile:
        csvwriter=csv.writer(csvfile,delimiter=",")
        csvwriter.writerow(header)
        for row in results:
            csvwriter.writerow(row)

t2=datetime.now()

print("")
print("Files processed: "+str(num))
print("Time elapsed: "+str(t2-t1))
