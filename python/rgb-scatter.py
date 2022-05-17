#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Mon May 16 11:04:10 2022

@author: Kim Miikki

read rgb.csv file
1. row: default unit (override with option -xlabel)

Create plots:
    BW
    RGB
    
Plot options:
- line
- square
- grid
- auto y-axis
'''

import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np 
import os
import sys
from pathlib import Path

default_name=Path('rgb.csv')
adir='rgb'
linew=1.0
isMarkers=False
isLine=True
isGrid=True
isAutoY=False
isNumber=False
xlabel=''
marker=''
delimiter=','

nums=['0','1','2','3','4','5','6','7','8','9']
firstc=nums.copy()
firstc.append('+')
firstc.append('-')

def getNumber(s):    
    tmp=Path(s)
    tmp=tmp.stem
    result=True

    a=-1
    b=-1
    founda=False
    foundb=False
    v='N/A'

    try:
        v=float(tmp)
    except:
        result=False
    if not result:
        # Search the first valid digit character
        i=0
        for ch in tmp:
            if ch in firstc:
                a=i
                founda=True
                break
            i+=1
        # Search the last digit character
        i=len(tmp)
        while i>=0:
            ch=tmp[i-1]
            if ch in nums:
                b=i
                foundb=True
                break
            i-=1
        if founda==True and foundb==True:
            if b>a:
                try:
                    v=float(tmp[a:b])
                except:
                    v='N/A'
    return v

# Read and parse program arguments
parser=argparse.ArgumentParser()
parser.add_argument('-f', type=Path, help='RGB data file (*.csv)',required=False)
parser.add_argument('-s', action='store_true', help='enable square markes',required=False)
parser.add_argument('-nl', action='store_true', help='disable line (default: on)',required=False)
parser.add_argument('-ng', action='store_true', help='Do not draw grids',required=False)
parser.add_argument('-y', action='store_true', help='auto scale y-axis',required=False)
parser.add_argument('-xlabel', type=str , help='x-axis label string',required=False)
args = parser.parse_args()

#ferror=False
if args.f != None:
    if os.path.isfile(args.f):
        stem=args.f.stem
        fname=str(args.f.name)
    else:
        print('File '+str(args.f)+' not found!')
        sys.exit(0)
else:
    if not os.path.isfile(default_name):
        print('File '+str(default_name)+' not found!')
        sys.exit(0)
    else:
        stem=default_name.stem
        fname=str(default_name)

if args.s:
    marker='s'
    isMarkers=True

if args.nl:
    if isMarkers:
        linew=0
        isLine=False
    else:
        pass

if args.ng:
    isGrid=False

if args.y:
    isAutoY=True

if args.xlabel != None:
    xlabel=args.xlabel

print('RGB scatter plotter 1.0, (c) Kim Miikki 2022')

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
adir=str(path)+'/'+adir+'/'
print("")
print("Current directory:")
print(path)
print("")

try:
  if not os.path.exists(adir):
    os.mkdir(adir)
except OSError:
  print('Unable to create a directory under following path:\n'+curdir)
  print('Program is terminated.')
  print('')
  sys.exit(1)


# Read the csv file into data array
rgb_data=[]
xs=[]
num=[]
i=0
try:
    with open(fname,'r') as reader_obj:    
        csv_reader=csv.reader(reader_obj)
        header_rgb=next(csv_reader)
        if xlabel=='':
            tmp=header_rgb[0]
            if tmp=='':
                tmp='Number'
                isNumber=True
            xlabel=tmp
        for row in csv_reader:
            rgb_data.append(list(map(float,row[2:])))
            if isNumber:
                xs.append(i)
            else:
                x=getNumber(row[0])
                if x=='N/A':
                    xs.append(i)
                else:
                    xs.append(x)
            num.append(row[1])
            i+=1
except OSError:
    print('Unable to open '+fname+' in following directory:\n'+curdir)
    print('Program is terminated.')
    print('')
    sys.exit(1) 

floatValues=False
for v in xs:
    if not float(v).is_integer():
        floatValues=True
        break
if not floatValues:
    xs=np.array(xs,int)
else:
    xs=np.array(xs,float)

# Get y values
ys=np.array(rgb_data,float).T
bw=ys[0]
r=ys[1]
g=ys[2]
b=ys[3]

# Plot RGB
fig=plt.figure()
ylabel='RGB mean value'
ymins=[r.min(),g.min(),b.min()]
ymaxs=[r.max(),g.max(),b.max()]
ymin=min(ymins)
ymax=max(ymaxs)
if not isAutoY:
    ymin=0
    ymax=255
plt.xlim(min(xs),max(xs))
plt.ylim(ymin,ymax)
plt.plot(xs,r,color='r',linewidth=linew,marker=marker)
plt.plot(xs,g,color='g',linewidth=linew,marker=marker)
plt.plot(xs,b,color='b',linewidth=linew,marker=marker)
plt.xlabel(xlabel)
plt.ylabel(ylabel)
if isGrid:
    plt.grid()
plt.savefig(adir+'RGB.png',dpi=300)
plt.close(fig)

# Plot BW
fig=plt.figure()
ylabel='BW mean value'
ymin=min(bw)
ymax=max(bw)
if not isAutoY:
    ymin=0
    ymax=255
plt.xlim(min(xs),max(xs))
plt.ylim(ymin,ymax)
plt.plot(xs,bw,color='k',linewidth=linew,marker=marker)
plt.xlabel(xlabel)
plt.ylabel(ylabel)
if isGrid:
    plt.grid()
plt.savefig(adir+'BW.png',dpi=300)
plt.close(fig)

# Test if a RGB file can be created
try:
    outname=stem+'.csv'
    file=open(adir+outname,'w')
except OSError:
  print('Unable to create a RGB file in following directory:\n'+curdir)
  print('Program is terminated.')
  print('')
  sys.exit(1)
  
# Write a csv data file
header=xlabel+delimiter
header+=header_rgb[1]+delimiter
header+='bw'+delimiter
header+='red'+delimiter
header+='green'+delimiter
header+='blue'
file.write(header+'\n')
columns=len(rgb_data[0])
f=0
for row in rgb_data:
  file.write(str(xs[f])+delimiter)
  file.write(str(num[f])+delimiter)
  f+=1
  s=''
  for i in range(0,columns):
    s+=str(row[i])
    if i<columns-1:
      s+=delimiter
  file.write(s+'\n')
file.close()
