#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 18 00:09:22 2022

@author: kim
"""
import argparse
import glob
import numpy as np
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
#import matplotlib.pyplot as plt
from scipy.signal import medfilt

window=3
threshold=1
digits=4

# Set the print options to suppress scientific notation
np.set_printoptions(suppress=True)

outdir=''
prefix='tdf-'
extpart='-log.csv'

print('Thermal Camera Log File Filter - (C) Kim Miikki 2022')

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print("")
if curdir!='/':
    curdir+='/'

parser=argparse.ArgumentParser()
parser.add_argument('name', type=str, help='input project name: yyyymmdd-HHMM')
parser.add_argument('-v',action='store_true',help='use variance filter')
parser.add_argument('-w', type=int, help='window size (default size is 3-')
args = parser.parse_args()

if args.w:
    value=args.w
    if value % 2 == 1 and value > 0:
        window=abs(args.w)
    else:
        print('Invalid windows size. Using the default value: 3.')

# Log name template:
# yyyymmdd-HHMM-log.csv
# Base part : yyyymmdd-HHMM = Project name
# Type + ext: -log.csv

# Read the log file into a numpy array
# Argument template: yyyymmdd-HHMM-
template='yyyymmdd-HHMM' 
reqLen=len(template)
iLen=len(args.name)
if iLen != reqLen:
    print('Incorrect project name. Correct format is: '+template)
    sys.exit(0)

# Search for the specified log file
log=args.name+extpart
try:
    data = np.genfromtxt(log, delimiter=',', names=True)
except OSError:
    print('Missing or unable to open the log file')
    
# Create an output directory for the filtered data
ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M')
outdir=curdir+prefix+dt_part
try:
  if not os.path.exists(outdir):
    os.mkdir(outdir)
  outdir+='/'
except OSError:
  print("Unable to create a directory under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)
  
# Get log information
names=data.dtype.names
arlen=len(data)

# Matrix size
m=24
n=32

# Create 1-D temperature arrays
ts=data['time']
tmins=data['tmin']
tmaxs=data['tmax']
tvars=data['tvar']

# Filter outliar values with median filters
tmins_flt=medfilt(tmins,window)
ts_min_discard=ts[abs(tmins_flt-tmins)>threshold]
tmaxs_flt=medfilt(tmaxs,window)
ts_max_discard=ts[abs(tmaxs_flt-tmaxs)>threshold]


ts_discard=np.union1d(ts_min_discard, ts_max_discard)
if args.v:
    tvars_flt=medfilt(tvars,window)
    ts_var_discard=ts[abs(tvars_flt-tvars)>threshold]
    ts_discard=np.union1d(ts_discard, ts_var_discard)
ts_in_discard=np.where(np.isin(ts,ts_discard)==True)[0]

# Copy all valid heatmaps to a subdirectory
files=glob.glob(curdir+'/*.txt')
files=sorted(files)
file_copied=np.full(arlen,False)
print('Analyzing and coping valid heatmaps.')
i=0
pr=0
for file in files:
    path,fname=os.path.split(file)
    i+=1
    p=i % round(len(files)/9)
    if p==0:
        pr+=10
        print(str(pr)+' %')
    # Remove the name end extension from fname, and convert it to a number
    try:
        num=int(fname[len(template)+1:-4])
        if num in ts_in_discard:
            continue
        if num>=arlen:
            continue
    except:
        continue
    
    # Copy the file from dir1 to dir2
    try:
        shutil.copy(file, outdir+fname)
    except:
        continue    
    
    file_copied[num]=True
if pr<100:
    print('100 %')
print('')

missing_in=np.where(file_copied==False)[0]

def array_interpolate(ar1,ar2,x1,x2,x):
    if ar1.shape != ar2.shape:
        return []
    m,n=ar1.shape
    ar=np.zeros((m,n))
    dx=x2-x1
    for i in range(0,m):
        for j in range(0,n):
            y1=ar1[i][j]
            y2=ar2[i][j]
            y=y1+(x-x1)*(y2-y1)/dx
            ar[i][j]=y
    return ar  

# Generate and save missing heatmaps

valid_maps=np.full(arlen,True)
for pos in missing_in:
    valid_maps[pos]=False
if np.count_nonzero(valid_maps) < 2:
    print('Too few valid heatmaps for interpolation.')
    exit.sys(1)
if len(missing_in)>0:
    print('Generating missing heatmaps:')
for pos in missing_in:
    
    left=ts[:pos]
    lmask=valid_maps[:pos]
    try:
        lvalue=left[lmask][-1]
    except:
        lvalue=np.nan
    
    right=ts[pos+1:]
    rmask=valid_maps[pos+1:]
    try:
        rvalue=right[rmask][0]
    except:
        rvalue=np.nan

    x0=pos    
    cnt=str(pos).rjust(digits,'0')
    print(cnt+': ',end='')

    # Missing first point(s) section
    if np.isnan(lvalue):
        x1=rvalue
        pos1=np.ravel(np.where(ts==x1))[0]
        x2=right[rmask][1]
        pos2=np.ravel(np.where(ts==x2))[0]
        print('extrapolating t= ',end='')

    # Missing last point(s) section
    elif np.isnan(rvalue):
        x2=lvalue
        pos2=np.ravel(np.where(ts==x2))[0]
        x1=left[lmask][-2]
        pos1=np.ravel(np.where(ts==x1))[0]
        print('extrapolating t= ',end='')

    # Interpolation section
    else:
        x1=lvalue
        pos1=np.ravel(np.where(ts==x1))[0]
        x2=rvalue
        pos2=np.ravel(np.where(ts==x2))[0]
        print('interpolating t= ',end='')
    print(str(round(ts[pos],2))+' s')
    
    # Get two heatmaps for interpolation
    n0=outdir+args.name+'-'+str(pos).rjust(digits,'0')+'.txt'
    n1=curdir+args.name+'-'+str(pos1).rjust(digits,'0')+'.txt'
    n2=curdir+args.name+'-'+str(pos2).rjust(digits,'0')+'.txt'
    a1 = np.genfromtxt(n1, delimiter=',')
    a2 = np.genfromtxt(n2, delimiter=',')
    a0=array_interpolate(a1, a2, x1, x2, x0)
    np.savetxt(n0,a0,delimiter=',',fmt='%.8f')
    
# Extract and save time data
acount=data['count']
atime=data['time']
atimestamp=data['timestamp']
ats=np.vstack((acount,atime,atimestamp)).T
tsdir=outdir+args.name+'-ts.csv'
header='count, time, timestamp'
np.savetxt(tsdir,ats,delimiter=',',fmt='%.8f',header=header)
