#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 08:47:10 2023

@author: Kim Miikki
@authors for functions: Kim Miikki and ChatGPT

Sub directories:
hhmmss-NAME,
NAME=figures,data,results

figures:
    - if isRotate: each curve plotted at 0° by end points, otherwise without rotation
    - if isRotate: title: θ= 12.30°, otherwise None
    - if not rotated: draw line with θ from curve start x to start y, display angle on graph
    - if isCalibration ylablel: calibrated length + unit, otherwise ylabel: Y coordinate
    - if isCalibration xlablel: calibrated length + unit, otherwise ylabel: Y coordinate
data:
    - csv data of each series: stem(name)+.'.csv'
results:
    - csv summary data of each series as function of time

Test arguments: -g * -o -r -sca
                -g 1 -r
                -g 100,200,300,400,500,600,700,800,900,1000 -type -ps -bsp 50 -endc -crop 100
"""

import argparse
import cv2
import csv
import math
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from scipy.signal import medfilt
from sklearn.metrics import auc
from scipy.interpolate import splrep, splev, splder, splprep
from math import atan2, degrees

# Set the print options to suppress scientific notation
np.set_printoptions(suppress=True)

# Supported image formats:
exts=['.png','.jpg']
primary='.png'
secondary=list(set(exts)-set([primary]))[0]
pts=[]
ptsfile=''
isPTS=False
isPTSfile=False
isPTSarg=False
isHeader=False
isCalibration=False

threshold=20
pixels_th=1
pixels_ymargin=10
origin_zero=False
isRotate=False
isNumSort=True
isGrid=True
isLimits=False
isWidths=False
isCrop=False
endCrop=True
startCrop=False

tstart=0
interval=1
tunit='s'
tfactor=1
cal=1
unit='mm'

# B-spline points
num_points=100

crop_points=50

dpi=300

isDebug=False

def unique(arglist):
    x = np.array(arglist)
    return np.unique(x)

def get_ranges(argstr):
    nums=[]
    s=argstr.strip()
    # Find character ','
    list1=s.split(',')
    list1=unique(list1)

    # Find ranges and add all numbers into a list
    for element in list1:
        isNumeric=element.isnumeric()
        # Test if element is a range
        error=False
        if not isNumeric:
            tmp=element.split('-')
            if len(tmp) != 2:
                error=True
            else:
                isFirst=True
                a=-1
                b=-1
                for n in tmp:
                    if not n.isnumeric():
                        error=True
                    else:
                        if isFirst:
                            a=int(n)
                            isFirst=False
                        else:
                            b=int(n)
                if not error:
                    if b<=a:
                        error=True
                if not error:
                    i=a
                    while i<=b:                                           
                        nums.append(i)
                        i+=1
        else:
            nums.append(int(element))
    return unique(nums)

def rotate_points(points, pivot, angle):
    angle = np.deg2rad(angle)
    rotation_matrix = np.array([[np.cos(angle), -np.sin(angle)],
                                [np.sin(angle), np.cos(angle)]])
    rotated_points = np.dot(points - pivot, rotation_matrix) + pivot
    return rotated_points

def first_digit_pos(s):
    for i, c in enumerate(s):
        if c.isdigit():
            return i
    return -1

def swap(a,b):
    return b,a

def most_abundant_string_length(strings):
    lengths = [len(s) for s in strings]
    length_counts = {}
    for length in lengths:
        if length in length_counts:
            length_counts[length] += 1
        else:
            length_counts[length] = 1
    return max(length_counts, key=length_counts.get)

def get_ranges_over_threshold(arr, threshold):
    # Get the indices where values are over the threshold
    over_threshold = np.where(arr >= threshold)[0]
    
    # Initialize the start and end indices to None
    start_index = end_index = None
    
    ranges = []
    
    # Iterate over the indices where values are over the threshold
    for index in over_threshold:
        if start_index is None:
            # If this is the first index, set start_index
            start_index = index
        elif index - end_index > 1:
            # If there is a gap between the current index and the end_index,
            # set the end_index, append the range to the ranges list, and
            # reset the start_index
            end_index = index - 1
            ranges.append((start_index, end_index))
            start_index = index
        end_index = index
    
    # Add the last range
    if start_index is not None:
        ranges.append((start_index, end_index))
    
    return ranges

def length(arr):
    diff = np.diff(arr, axis=0)
    return np.sum(np.sqrt(np.sum(diff**2, axis=1)))

def get_time(tstart, pos, interval):
    return tstart+pos*interval

def plot_graph(path_name, ts, ys, time_unit, ylabel, cal=isCalibration, grid=isGrid, dpi=dpi):
    fig=plt.figure()
    plt.xlim(ts.min(),ts.max())
    ymin=ys.min()
    ymax=ys.max()
    if ymin==ymax:
        if ymin==0:
            dy=0.1
        else:
            dy=abs(ymin)/10
        ymin-=dy
        ymax+=dy
    plt.ylim(ymin,ymax)
    plt.plot(ts,ys,color="k")
    plt.xlabel('Time ('+time_unit+')')
    if not cal:        
        plt.ylabel(ylabel)
    else:
        plt.ylabel('Y coordinate')
    if grid:
        plt.grid()
    plt.tight_layout()
    plt.savefig(path_name,dpi=dpi)
    plt.close(fig)

def fit_cubic_bspline(x_coords, y_coords, num_points):
    # Fit a quadratic B-spline to the data
    tck, u = splprep([x_coords, y_coords], k=3, s=0)
    
    # Evaluate the B-spline at  num_points
    u_new = np.linspace(u.min(), u.max(), num_points)
    x_bspline, y_bspline = splev(u_new, tck)
    
    # Return the x and y values of the B-spline
    return x_bspline, y_bspline

def spline_properties(x, x_coords, y_coords, num_points):
    tck = splrep(x_coords, y_coords, k=3, s=num_points)
    y = splev(x, tck)
    k = splev(x, splder(tck, n=1))
    angle = degrees(atan2(splev(x, splder(tck, n=1)), 1))
    return y, k, angle

def tangent_line_coords(slope, x, y, d):
    # Step 1: Determine the slope-intercept form of the tangent line
    b = y - slope * x
    # Step 2: Calculate the x-coordinates of the start and end points of the line
    x0 = x - d
    x1 = x + d
    # Step 3: Calculate the corresponding y-coordinates for the start and end points
    y0 = slope * x0 + b
    y1 = slope * x1 + b
    # Step 4: Return arrays of coordinates for the tangent line
    xs=[x0,x,x1]
    ys=[y0,y,y1]
    return xs, ys


print("Fiber angle measurement program - (C) Kim Miikki 2023")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print('')
if curdir!='/':
    curdir+='/'

isTFactor=False
isPSeries=False
isNoSeries=False
isBeta=False
parser=argparse.ArgumentParser()
# Scan thresholds START
parser.add_argument('-th',type=int,help='threshold color value (1-255)',required=False)
parser.add_argument('-px',type=int,help='pixels threshold (>=1)',required=False)
parser.add_argument('-ext',type=int,help='extend Y scan margins by pixels (>=0, default: '+str(pixels_ymargin)+')',required=False)                    
# Scan thresholds END
parser.add_argument('-pts', type=str, help='pts file name',required=False)
parser.add_argument('-s',type=float,help="start time for first frame",required=False)
parser.add_argument('-i',type=float,help="interval between two frames",required=False)
parser.add_argument("-t",type=str,help="time unit",required=False)
parser.add_argument("-f",type=float,help="time factor (only for PTS files)",required=False)
parser.add_argument('-g', help='create graphs based on numbered image positions (a = all or num1, num2-num3, ...)', type=str, required=False)
parser.add_argument('-c',type=float,help="calibration value (pixels/unit)",required=False)
parser.add_argument('-u',type=str,help='length unit',required=False)
parser.add_argument('-crop',type=int,help='crop scanned curve width in pixels (min. 2, default direction: from end)',required=False)
parser.add_argument('-endc',action='store_true',help='normal crop mode (= from end)',required=False)
parser.add_argument('-revc',action='store_true',help='reverse crop mode (= from start)',required=False)
parser.add_argument('-bsp',type=int,help='b-spline points (default='+str(num_points)+')',required=False)
parser.add_argument('-o',action='store_true',help='adjust start point to (0,0)',required=False)
parser.add_argument('-r',action='store_true',help='rotate curve',required=False)
parser.add_argument('-ps',action='store_true',help='plot series (all types)',required=False)
parser.add_argument('-beta',action='store_true',help='plot graphs with beta angle',required=False)
parser.add_argument('-li',action='store_true',help='plot graphs with limits',required=False)
parser.add_argument('-wi',action='store_true',help='plot graphs with widths',required=False)
parser.add_argument('-sca',action='store_true',help='plot profiles with scan area',required=False)
parser.add_argument('-type',action='store_true',help='start file name with type (default= number)',required=False)
parser.add_argument('-n',action='store_true',help='do not store series data',required=False)
args = parser.parse_args()

if args.th != None:
    tmp=int(args.th)
    if tmp>0 and tmp<256:
        threshold=tmp

if args.px != None:
    tmp=int(args.px)
    if tmp>=0:
        pixels_th=tmp

if args.ext != None:
    tmp=int(args.ext)
    if tmp>=0:
        pixels_ymargin=tmp


if args.pts != None:
    ptsfile=args.pts
    isPTSarg=True

if args.s != None:
    tstart=float(args.s)

if args.i != None:
    tmp=float(args.i)
    if interval>0:
        interval=tmp

if args.t != None:
    tmp=args.t
    if len(tmp)>0:
        tunit=tmp

if args.f != None:
    isTFactor=True
    tmp=float(args.f)
    if tmp.is_integer():
        tfactor=int(round(tmp,0))
    else:
        tfactor=float(tmp)

if args.c != None:
    isCalibration=True
    cal=float(args.c)
    if cal.is_integer():
        cal=int(round(cal,0))

if args.u != None:
    tmp=args.u
    if len(tmp)>0:
        unit=tmp

if args.crop != None:
    tmp=int(args.crop)
    if tmp>1 and tmp<=1000000:
        crop_points=tmp
        isCrop=True

if args.endc:
    endCrop=True
    startCrop=False
    isCrop=True
elif args.revc:
    endCrop=False
    startCrop=True
    isCrop=True
    
if args.bsp != None:
    tmp=int(args.bsp)
    if tmp>0 and tmp<=1000000:
        num_points=tmp
  
if not None in [args.c,args.u]:
    isCalibration=True

if args.o:
    origin_zero=True  

if args.r:
    isRotate=True  
    
if args.ps:
    isBeta=True
    isLimits=True
    isWidths=True
    isPSeries=True  

if args.beta:
    isBeta=True    
    isPSeries=True

if args.li:
    isLimits=True    
    isPSeries=True

if args.wi:
    isWidths=True    
    isPSeries=True

if args.sca:
    isDebug=True
    isLimits=True
    isWidths=True
    isPSeries=True  

if args.type:
    isNumSort=False

if args.n:
    isNoSeries=True  

# Determine which file format is the most abundant
pris=[]
secs=[]
prinums=[]
secnums=[]
for name in sorted(path.iterdir()):
    if name.is_file() and name.suffix in exts:
        tmp=name.stem
        pos=first_digit_pos(tmp)
        if pos>=0:
            num=tmp[pos:]
            if num.isdigit():
                if name.suffix==primary:
                    pris.append(tmp+primary)
                    prinums.append(num)
                elif name.suffix==secondary:
                    secs.append(tmp+secondary)
                    secnums.append(num)
countpris=len(pris)
countsecs=len(secs)

if countpris>=countsecs:
    frames=pris
    nums=prinums
else:
    primary,secondary=swap(primary,secondary)
    countpris,countsecs=swap(countpris,countsecs)
    frames=secs
    nums=secnums

if countpris==0:
    print('No suitable PNG or JPG pictures found in current directory.')
    print('Program is terminated.')
    print('')
    sys.exit(0)

namelen=most_abundant_string_length(frames)
numlen=most_abundant_string_length(nums)

# Remove all strings that do not belong the time-lapse set
i=0
reminds=[]
for s in frames:
    remove=False
    if len(s) != namelen:
        remove=True
    if not remove:
        pos=first_digit_pos(s)
        if len(s[pos:-len(primary)]) != numlen:
            remove=True
    if remove:
        reminds.append(i)
    i+=1
for idx in sorted(reminds,reverse=True):
    frames.pop(idx)
    nums.pop(idx)
    
# The stem is assumed to be same => not checked

# Create an integer list of the number strings
nums_int=list(map(int,nums))
nums_graph=[]

# Create a list of the images from which graphs will be created
if args.g!= None:
    tmp=args.g
    if tmp.lower() == 'a':
        nums_graph = nums_int
    else:
        nums_range=get_ranges(tmp)
        nums_graph=sorted(list(set(nums_range).intersection(nums_int)))
    if len(nums_graph)>0:
        isPSeries=True
        
# Find a PTS file, if it exists
if isPTSarg:
    if os.path.isfile(curdir+ptsfile):
        ptsfile=Path(curdir+ptsfile)
        isPTSfile=True
else:
    ptslst=[]
    for f in sorted(path.iterdir()):
      suffix=f.suffix.lower()
      if f.is_file():
        if suffix=='.pts':
            ptslst.append(f)
    
    
    if len(ptslst)>0:
        ptsfile=ptslst
        isPTSfile=True
        if len(ptslst)>1:
            print('Found more than 1 pts file!',)
        ptsfile=ptslst[0]
    
if isPTSfile:
    with open(ptsfile) as file:
        reader = csv.reader(file)
        header=next(file)
        for row in reader: 
            try:
                pts.append(float(row[0]))
            except:
                pass
    if len(pts) != len(nums):
        print('PTS count differs from image count. PTS disabled.')
        isPTS=False
    else:
        print('PTS file found: '+ptsfile.name)
        isPTS=True
    print('')

print('Digits in images    : '+str(numlen))
print('Valid images found  : '+str(len(nums)))
print('Image extension type: '+primary)
print('')

# Multiply PTS values with the factor
if  isPTS:
    if len(pts)>0:
        if not isTFactor:
            tfactor=1/1000
        pts=np.array(pts)
        pts=pts*tfactor

## Start time uses the final unit
##if isTFactor:
##    tstart=tstart*tfactor

# Create project name and sub directories
ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M%S')
figdir=dt_part+'figures'
#datadir=dt_part+'data'
#resultsdir=dt_part+'results'

print('Creating directories:')
dirs=['figures','data','results']
for name in dirs:
    newdir=dt_part+'-'+name
    if name=='figures' and (not isPSeries):
        continue
    if name=='data' and isNoSeries:
        continue
    print(newdir)
    try:
        if not os.path.exists(curdir+newdir):
            os.mkdir(curdir+newdir)
        
    except OSError:
        print("Unable to create a directory or directories under following path:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)
print('')

# Process all images
i=0
images=0
results=[]
#degs=[]

t1=datetime.now()
for name in frames:
    if images==0:
        print('Processing:')
    print(name,end='')
    
    # Open image from file
    img=cv2.imread(name)
    h,w,ch=img.shape
    
    # Convert a RGB image to gray
    if ch==3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        print(': incorrect format, skipped')
        i+=1
        continue

    # Determine plot mode: normal=1, inverse=-1
    mean=np.mean(img)
    median=np.median(img)
    if mean>median:
        invert=False
    else:
        invert=True
    
    if invert:
        img=cv2.bitwise_not(img)
        mean=np.mean(img)
        median=np.median(img)
    
    # Calculate x and y mean profiles
    xprofile=img.mean(axis=0)
    xs=np.array(list(range(0,w)))
    xmean=np.mean(xprofile)
    xmedian=np.median(xprofile)
    
    yprofile=img.mean(axis=1)
    ys=np.array(list(range(0,h)))
    ymean=np.mean(yprofile)
    ymedian=np.median(yprofile)
       
    # Search for y bands
    
    # Step 1: smooth yprofile
    window=51
    if h<window:
        window=h-1
        if window % 2 == 0:
            window-=1
        if window<3:
            window=3
    ymedian_profile=medfilt(yprofile,window)
    yuniq_profile=np.unique(ymedian_profile)
    yranges=get_ranges_over_threshold(ymedian_profile,ymean)
    
    # Find y range with maximum median value  
    yi=-1
    value=-1
    l=0
    for a,b in yranges:
        tmp=ymedian_profile[a:b].max()
        if tmp>value:
            value=tmp
            yi=l
        l+=1

    # Determine yregion
    yreg0=yranges[yi][0]
    yreg1=yranges[yi][1]
   
    # Search for x bands
    
    # Step 1: smooth xprofile
    window=51
    if w<window:
        window=w-1
        if window % 2 == 0:
            window-=1
        if window<3:
            window=3
    xmedian_profile=medfilt(xprofile,window)
    xuniq_profile=np.unique(xmedian_profile)
    xranges=get_ranges_over_threshold(xmedian_profile,xmean)
    
    # Find x range with maximum median value  
    xi=-1
    value=-1
    l=0
    for a,b in xranges:
        tmp=xmedian_profile[a:b].max()
        if tmp>value:
            value=tmp
            xi=l
        l+=1

    # Determine yregion
    xreg0=xranges[xi][0]
    xreg1=xranges[xi][1]

    print(' sc: ('+str(xreg0)+','+str(yreg0)+')-('+str(xreg1)+','+str(yreg1)+')', end=''    )
    
    # Calculate x and y mean profiles of the scan area
    xscan_profile=img[yreg0:yreg1,xreg0:xreg1].mean(axis=0)
    xscan_xs=np.array(list(range(0,xreg1-xreg0)))
    xscan_mean=np.mean(xscan_profile)
    xscan_median=np.median(xscan_profile)
    
    yscan_profile=img[yreg0:yreg1,xreg0:xreg1].mean(axis=1)
    yscan_ys=np.array(list(range(0,yreg1-yreg0)))
    yscan_mean=np.mean(yscan_profile)
    yscan_median=np.median(yscan_profile)

    # Find the start x and y
    j=xreg0
    #ys0=img[yreg0:yreg1,j]
    
    # Loop through x-axis in 1 pixel wide slices
    # Find upper and lower y values in y direction
    
    ymean_min=-1
    ymean_max=-1
    ymean=-1
    
    yscan_min=-1
    yscan_max=-1
    
    xarr=[]
    ymins=[]
    ymeans=[]
    ymaxs=[]
    
    if isDebug:
        # ysmins ysmaxs: image coordinates
        ysmins=[]
        ysmaxs=[]
    

    # Search for curve in the scan region
    curve_found=False
    while j<=xreg1:
        # Set min and max values for the sliced scan region
        # All y values are in image coordinate system
        if ymean_min<0:
            yscan_min=yreg0
        if ymean_max<0:
            yscan_max=yreg1

        xcol=img[yscan_min:yscan_max,j]      
        yvals_ind=np.where(xcol>threshold)[0]
        yvals_len=len(yvals_ind)
        
        if yvals_len<pixels_th and curve_found:
            break
        
        if yvals_len>=pixels_th:
            curve_found=True
            ymean_min=yvals_ind[0]+yscan_min
            ymean_max=yvals_ind[-1]+yscan_min
            ymean=round(np.mean([ymean_min,ymean_max]),1)
            
            yscan_min=ymean_min-pixels_ymargin
            if yscan_min<0:
                yscan_min=0
            
            yscan_max=ymean_max+pixels_ymargin
            if yscan_max>h+1:
                yscan_max=h-1
            
            # Convert y coordinate values to normal coordinates,
            # hence min->max and max->min
            xarr.append(j)
            ymins.append(h-ymean_max)
            ymaxs.append(h-ymean_min)
            ymeans.append(h-ymean)

            if isDebug:
                ysmins.append(yscan_min)
                ysmaxs.append(yscan_max)
        else:
            yscan_min=yreg0
            yscan_max=yreg1
        j+=1
    if isDebug:
        # Convert coordinate system from image to normal
        ysmins=h-np.array(ysmins)
        ysmaxs=h-np.array(ysmaxs)
        ysmins,ysmaxs = ysmaxs,ysmins
        
    
    # Create NumPy arrays of the line data
    xarr=np.array(xarr)
    ymins=np.array(ymins)
    ymaxs=np.array(ymaxs)
    ymeans=np.array(ymeans)
    if isCrop:
        if endCrop:
            xarr=xarr[-crop_points:]
            ymins=ymins[-crop_points:]
            ymaxs=ymaxs[-crop_points:]
            ymeans=ymeans[-crop_points:]
        else:
            xarr=xarr[:crop_points]
            ymins=ymins[:crop_points]
            ymaxs=ymaxs[:crop_points]
            ymeans=ymeans[:crop_points]
    ydiff=ymaxs-ymins
    
    # Adjust orgin to zero
    if origin_zero:
        xarr=xarr-xarr[0]
        dy=-ymeans[0]
        ymins=ymins+dy
        ymaxs=ymaxs+dy
        ymeans=ymeans+dy
        if isDebug:
            ysmins=ysmins+dy
            ysmaxs=ysmaxs+dy

    # Calibration
    if isCalibration:
        xarr=xarr/cal
        ymins=ymins/cal
        ymaxs=ymaxs/cal
        ymeans=ymeans/cal
        if isDebug:
            ysmins=ysmins/cal
            ysmaxs=ysmaxs/cal
        
    x0=xarr[0]
    x1=xarr[-1]
    y0=ymeans[0]
    y1=ymeans[-1]

    # Calculate the angle for end points
    th=math.degrees(math.atan2(y1-y0, x1-x0))
    #degs.append(th)
    print(' θ: '+format(round(th,2),'.2f')+'°',end='')

    # Calculate the end point angle β
    y, slope, beta = spline_properties(x1, xarr, ymeans, num_points)
    print(' β: '+format(round(beta,2),'.2f')+'°',end='')
    
    # Calculate the length of the curve
    xylen=length(np.column_stack((xarr,ymeans)))
    print(' len: '+str(int(round(xylen,0))),end='')
    
    # Calculate the length between curve endpoints, then Δl = curve - line
    xyline=x1-x0
    xy_delta=xylen-xyline
    print(' Δl: '+str(int(round(xy_delta,0))),end='')
    
    # Calculate curve width statistics
    width_mean=np.mean(ydiff)
    width_median=np.median(ydiff)
    print(' w: '+str(round(width_mean,1)).rjust(4),end='')
    
    # Calucalte areas under curve
    xy_auc=auc(xarr,ymeans)
    xy_absauc=auc(xarr,abs(ymeans))
    print(' auc: '+str(int(round(xy_auc,0))),end='')
    
    # Calculate time for current curve
    if isPTS:
        tcurve=tstart+pts[i]
    else:
        tcurve=tstart+i*interval
    
    if isRotate:
        pivot=[x0,y0]
        xy_rmins=rotate_points(np.column_stack((xarr,ymins)),pivot,th)
        xy_rmeans=rotate_points(np.column_stack((xarr,ymeans)),pivot,th)
        xy_rmaxs=rotate_points(np.column_stack((xarr,ymaxs)),pivot,th)
        if isDebug:
            xy_rsmins=rotate_points(np.column_stack((xarr,ysmins)),pivot,th)
            xy_rsmaxs=rotate_points(np.column_stack((xarr,ysmaxs)),pivot,th)

    # Save csv data of each curve
    if not isNoSeries:
        fname=Path(name).stem+'.csv'
        header=['N','Time ('+tunit+')']
        if not isCalibration:
            header.append('X')
            header.append('Ymin')
            header.append('Ymean')
            header.append('Ymax')
            header.append('ΔY')
        else:
            header.append('X ('+unit+')')
            header.append('Ymin ('+unit+')')
            header.append('Ymean ('+unit+')')
            header.append('Ymax ('+unit+')')
            header.append('ΔY ('+unit+')')
        header.append('θ (°)')
        header.append('β (°)')
        if isRotate:
            header.append('Xrot,min')
            header.append('Yrot,min')
            header.append('Xrot,mean')
            header.append('Yrot,mean')
            header.append('Xrot,max')
            header.append('Yrot,max') 
        with open(curdir+dt_part+"-data/"+fname,"w",newline="\n") as csvfile:
            writer=csv.writer(csvfile,delimiter=',',quotechar='"')
            writer.writerow(header)
            k=0
            while k<len(xarr):
                row=[i,tcurve,xarr[k],ymins[k],ymeans[k],ymaxs[k],ydiff[k],round(th,3),round(beta,3)]
                if isRotate:
                    row.append(xy_rmins.T[0][k])
                    row.append(xy_rmins.T[1][k])
                    row.append(xy_rmeans.T[0][k])
                    row.append(xy_rmeans.T[1][k])
                    row.append(xy_rmaxs.T[0][k])
                    row.append(xy_rmaxs.T[1][k])
                writer.writerow(row)
                k+=1
    
    # Create graphs from selected images
    if nums_int[i] in nums_graph:
        
        #Create file names for the  plots  
        fstem=frames[i][:-4]
        if isNumSort==True:
            file1=dt_part+'-figures/'+fstem+'-pixels.png'
            file2=dt_part+'-figures/'+fstem+'-pixels-limits.png'
            file3=dt_part+'-figures/'+fstem+'-width.png'
            file4=dt_part+'-figures/'+fstem+'-beta.png'
        else:
            file1=dt_part+'-figures/'+'length-'+fstem+'.png'
            file2=dt_part+'-figures/'+'length-limits-'+fstem+'.png'
            file3=dt_part+'-figures/'+'width-'+fstem+'.png'
            file4=dt_part+'-figures/'+'beta-'+fstem+'.png'

        yfirst=ymeans[0]
        ylast=ymeans[-1]        
        if ylast>yfirst:
            thpos=True
        elif yfirst>ylast:
            thpos=False

        # Series curve plot section START
        if not isRotate:
                        
            # Draw non-rotated curves
            fig=plt.figure()
            plt.xlim(xarr[0],xarr[-1])
            '''
            yfirst=ymeans[0]
            ylast=ymeans[-1]
            
            thpos=True
            '''
            if thpos:
                plt.ylim(yfirst,ylast)
            else:
                plt.ylim(ylast,yfirst)

            # Draw scan lines
            if isDebug:
                k=0
                while k<len(xarr):
                    plt.plot([xarr[k],xarr[k]],[ysmins[k],ysmaxs[k]],color='#c0c0c0')
                    k+=1

            plt.plot(xarr,ymeans,color="k")
            
            # Draw line between endpoints
            xl=[xarr[0],xarr[-1]]
            yl=[ymeans[0],ymeans[-1]]
            
            # Draw baseline
            plt.hlines(y=ymeans[0],xmin=xarr[0],xmax=xarr[-1],color='g')
            plt.plot(xl,yl,color="g")
            
            # Draw the anlge as an arc
            r=(xarr[-1]-xarr[0])/5 # Arc radius
            theta=th*(math.pi/180) # theta in radians
            arc_angles=np.linspace(0,theta,20)
            arc_xs=xarr[0]+r*np.cos(arc_angles)
            arc_ys=ymeans[0]+r*np.sin(arc_angles)
            plt.plot(arc_xs,arc_ys,color='g')
            
            dy=ymeans[-1]-ymeans[0]
            if thpos:
                plt.gca().annotate(r'$\theta$= '+str(round(th,2))+'°',xy=(xarr[0]+r*1.1,ymeans[0]+dy/16),fontsize=14)
            else:
                plt.gca().annotate(r'$\theta$= '+str(round(th,2))+'°',xy=(xarr[0]+r*1.1,ymeans[0]+dy/10),fontsize=14)
                
            if not isCalibration:
                plt.xlabel("X coordinate")
                plt.ylabel("Y coordinate")
            else:
                plt.xlabel('X ('+unit+')')
                plt.ylabel('Y ('+unit+')')
            if isGrid:
                plt.grid()
            
            plt.savefig(curdir+file1,dpi=dpi)
            
            if isLimits:
                # Draw bottom and upper limits curves
                plt.plot(xarr,ymins,color="b",linewidth=0.5)
                plt.plot(xarr,ymaxs,color="r",linewidth=0.5)
                plt.savefig(curdir+file2,dpi=dpi)
            
            # plt.show()
            plt.close(fig)
        else:
            
            # Draw rotated curves
            fig=plt.figure()
            plt.xlim(xy_rmeans.T[0][0],xy_rmeans.T[0][-1])
            plt.ylim(xy_rmins.T[1].min(),xy_rmaxs.T[1].max())
            if isDebug:
                plt.ylim(min(xy_rsmins.T[1]),max(xy_rsmaxs.T[1]))
            
            # Draw scan lines
            if isDebug:
                k=0
                while k<len(xarr):
                    plt.plot([xy_rsmins.T[0][k],xy_rsmaxs.T[0][k]],
                             [xy_rsmins.T[1][k],xy_rsmaxs.T[1][k]],color='#c0c0c0')
                    k+=1
            
            # Draw mean curve
            plt.plot(xy_rmeans.T[0],xy_rmeans.T[1],color="k")

            # Draw line between endpoints
            xl=[xy_rmeans.T[0][0],xy_rmeans.T[0][-1]]
            yl=[xy_rmeans.T[1][0],xy_rmeans.T[1][-1]]

            # Draw baseline
            plt.hlines(y=ymeans[0],xmin=xarr[0],xmax=xarr[-1],color='g')
            plt.plot(xl,yl,color="g")

            # Print theta
            r=(xarr[-1]-xarr[0])/5
            if not isDebug:
                dy=(xy_rmaxs.T[1].max()-xy_rmins.T[1].min())/10
                ytop=xy_rmaxs.T[1].max()
            else:
                dy=(max(xy_rsmaxs.T[1])-min(xy_rsmins.T[1]))/10
                ytop=max(xy_rsmaxs.T[1])
            
            # xth=(xy_rmeans.T[0][-1]-xy_rmins.T[0].min())/50
            # yth=(xy_rmaxs.T[1].max()-xy_rmins.T[1].min())
            # yth=xy_rmaxs.T[1].max()-yth/10
            plt.gca().annotate(r'$\theta$= '+str(round(th,2))+'°',xy=(xarr[0]+r*1.1,ytop-dy),fontsize=14)
            if not isCalibration:
                plt.xlabel("X coordinate")
                plt.ylabel("Y coordinate")
            else:
                plt.xlabel('X ('+unit+')')
                plt.ylabel('Y ('+unit+')')
            if isGrid:
                plt.grid()
            plt.savefig(curdir+file1,dpi=dpi)
            
            if isLimits:
                # Draw bottom and upper limits curves
                plt.plot(xy_rmins.T[0],xy_rmins.T[1],color="b",linewidth=0.5)
                plt.plot(xy_rmaxs.T[0],xy_rmaxs.T[1],color="r",linewidth=0.5)
                plt.savefig(curdir+file2,dpi=dpi)
            
            plt.close(fig)
        
        # Draw width curves
        if isWidths:
            fig=plt.figure()
            plt.xlim(xarr[0],xarr[-1])
            plt.ylim(ydiff.min(),ydiff.max())
            plt.plot(xarr,ydiff,color="k")
            if not isCalibration:
                plt.xlabel("X coordinate")
                plt.ylabel("ΔY (pixels)")
            else:
                plt.xlabel('X ('+unit+')')
                plt.ylabel('ΔY ('+unit+')')
            if isGrid:
                plt.grid()
            plt.savefig(curdir+file3,dpi=dpi)
            plt.close(fig)
            
        if isBeta:
            # Draw beta curves
            fig=plt.figure()
            plt.xlim(xarr[0],xarr[-1])
            plt.ylim(ymeans.min(),ymeans.max())
            plt.plot(xarr,ymeans,color="k")
            x_bspline, y_bspline = fit_cubic_bspline(xarr,ymeans,num_points)
            plt.scatter(x_bspline,y_bspline,marker='.',color='r')
            d=(xarr[-1]-xarr[0])/2
            x=xarr[-1]
            y=np.ravel(y)[0]
            xts,yts=tangent_line_coords(slope, x, y, int(d))
            plt.plot(xts,yts,color='0.5',linestyle='--')
            if not isCalibration:
                plt.xlabel("X coordinate")
                plt.ylabel("Y coordinate")
            else:
                plt.xlabel('X ('+unit+')')
                plt.ylabel('Y ('+unit+')')
            if isGrid:
                plt.grid()
            lstr=['β = '+str(round(beta,2))+'°']
            plt.legend(lstr, loc='upper left')
            plt.savefig(curdir+file4,dpi=dpi)
            plt.close(fig)
                   
        # Series curve plot section END
    
    if isPTS:
        t=pts[i]
    else:
        t=get_time(tstart,i,interval)
    results.append([i,t,th,xylen,xy_delta,width_mean,xy_auc,xy_absauc,beta])
    print('')
    images+=1
    i+=1

# Save and plot summary data
if isCalibration:
    lenunit=' ('+unit+')'
    squnit=' ('+unit+'²)'
else:
    lenunit=''
    squnit=''
header=['Name','N','Time ('+tunit+')','θ (°)','Length'+lenunit,'Δl'+lenunit,'Width'+lenunit,
        'auc'+squnit,'|auc|'+squnit,'β (°)']

# Write a summary CSV file
base=curdir+dt_part+'-results/'
fname=base+'data.csv'
with open(fname,'w',newline='\n') as csvfile:
    writer=csv.writer(csvfile,delimiter=',',quotechar='"')
    writer.writerow(header)
    k=0
    for row in results:
        tmp=[frames[k]]
        tmp.extend(row)
        writer.writerow(tmp)
        k+=1

results=np.array(results).T
ts=results[1]
ths=results[2]
lens=results[3]
dls=results[4]
ws=results[5]
aucs=results[6]
auc_abs=results[7]
betas=results[8]

if images > 1:
    # Plot theta=f(t)
    fname=base+'theta.png'
    plot_graph(fname,ts,np.round(ths,decimals=2),tunit,'θ (°)')
    
    # Plot Length=f(t)
    fname=base+'length.png'
    plot_graph(fname,ts,lens,tunit,'Length'+lenunit)
    
    # Plot Δl=f(t)
    fname=base+'dl.png'
    plot_graph(fname,ts,dls,tunit,'Δl'+lenunit)
    
    # Plot Width=f(t)
    fname=base+'width.png'
    plot_graph(fname,ts,np.round(ws,decimals=2),tunit,'Width'+lenunit)
    
    # Plot auc=f(t)
    fname=base+'auc.png'
    plot_graph(fname,ts,aucs,tunit,'auc'+squnit)
    
    # Plot |auc|=f(t)
    fname=base+'auc_abs.png'
    plot_graph(fname,ts,auc_abs,tunit,'|auc|'+squnit)
    
    # Plot beta=f(t)
    fname=base+'beta.png'
    plot_graph(fname,ts,betas,tunit,'β (°)'+squnit)

# Create and save a log file
log=[]
adict=vars(args)
for key in adict.keys():
    log.append([key,adict[key]])
with open(base+'arguments.log', 'w') as f:
    writer = csv.writer(f)   
    writer.writerows(log)
    
t2=datetime.now()
print("")
print("Time elapsed: "+str(t2-t1))
