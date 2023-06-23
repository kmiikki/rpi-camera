#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Kim Miikki 2023

import argparse
import cv2
import glob
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import os
import pandas as pd
import sys
from scipy.optimize import minimize
import scipy.stats as st
from datetime import datetime
from time import sleep
from pathlib import Path
from rpi.camerainfo import *
from rpi.roi import *
import picamera.array
from picamera import PiCamera

res=[[320,240],[640,480],[800,600],[1024,768],[1280,1024]]
mode=0

# Camera settings
exposure=20000 # µs
exp_mode="off"
awb_mode="auto"
iso=100
width=320
height=240

# R and B gains ranges
rs=[0.01,8]
bs=[0.01,8]

r_initial=2
b_initial=2

decimals=10
rgb_decimals=3

previewImage=True
count=0

series=[]
rgains=[]
bgains=[]
dists=[]
#iterations=20 # Default= 20

min_trials=2
max_trials=10000
trials=5
p=0.95
isTrials=False
#isFigs=True

#csv_files=[]
#in_row=0
#startpass_filter='awbgains-trials'
#isAnalysis=False

class Log:
    def __init__(self, filename):
        self.filename=filename
        self.lines=[]

    def add(self, line):
        self.lines.append(line)
    
    def print_lines(self):
        for line in self.lines:
            print(line)
    
    def save_to_file(self):
        with open(self.filename, 'w') as file:
            for line in self.lines:
                file.write(line+'\n')
    
    def clear_log(self):
        self.lines=[]

print('Optimal AWB MSE - (C) Kim Miikki 2023')
print('')

parser=argparse.ArgumentParser()
parser.add_argument('-m',type=int,help='mode (0-'+str(len(res))+')',required=False)
parser.add_argument('-ss', type=int, help='shutter speed in µs',required=False)
#parser.add_argument('-i', type=int, help='iterations (default='+str(iterations)+')',required=False)
parser.add_argument('-n', type=int, help='number of repetition trials ('+str(min_trials)+'-'+str(max_trials)+')',required=False)
#parser.add_argument('-figs',action='store_true',help='create all figures')
#parser.add_argument('-a',nargs='?', type=str, help='analysis mode: optional start filter for the csv file(s)', required=False)
args = parser.parse_args()

if args.m!=None:
    try:
        mode=int(args.m)
    except:
        print('Illegal mode value!')
        sys.exit(0)
    if mode<0:
        mode=0
    elif mode>=len(res):
        mode=len(res)-1

# Validate shutter speed
if args.ss != None:
    tmp=int(args.ss)
    if tmp<1 or tmp>camera_max_exposure:
        print('Invalid shutter speed. Using default: '+str(exposure)+' µs')
        print('')
    else:
        exposure=tmp
# Validate number of repetition
if args.n != None:
    tmp=int(args.n)
    if tmp<min_trials or tmp>max_trials:
        print('Number of trials out of range. Using default value: '+str(trials))
        print('')
    else:
        trials=tmp
        isTrials=True
        isFigs=False
  
print('Current directory:')
curdir=os.getcwd()
path=Path(curdir)
print(curdir)
if curdir[-1] != '/':
    curdir+='/'

ct0=datetime.now()

width=res[mode][0]
height=res[mode][1]
pip=(0,0,width,height)    

roi_result=validate_roi_values()

if roi_result:
    print('')
    display_roi_status()
else:
    roi_x0=0.5-width/(2*camera_maxx)
    roi_y0=0.5-height/(2*camera_maxy)
    roi_w=width/camera_maxx
    roi_h=height/camera_maxy
print('')
zoom=(roi_x0,roi_y0,roi_w,roi_h)

count=0
dists=[]
rgains=[]
bgains=[]
series=[]

# Set camera options
camera=PiCamera(resolution=(width,height))
camera.iso=iso


# Now fix the values
camera.exposure_mode=exp_mode
camera.awb_mode=awb_mode
camera.shutter_speed=int(exposure)
camera.zoom=zoom

print('AWB readings')
ct1=datetime.now()
dt_part=ct1.strftime('%Y%m%d-%H%M%S')

digits=len(str(trials))
for trial in range(1,trials+1):
    camera.start_preview(fullscreen=False,window=pip)
    # Wait for the automatic gain control to settle
    sleep(2)
    g = camera.awb_gains
    rgain=float(g[0])
    bgain=float(g[1])
    rgains.append(rgain)
    bgains.append(bgain)
    print(str(trial).zfill(digits)+':',rgain,bgain)
    # calibration, rgain_opt, bgain_opt
    series.append([trial,rgain,bgain])
       
ct2=datetime.now()
camera.close()

# Calculate the optimal gains
dists=np.array(dists)
rgains=np.array(rgains)
bgains=np.array(bgains)
optimal_rgain=np.mean(rgains)
optimal_bgain=np.mean(bgains)
calibrations=np.arange(1,trials+1)

disp_rgain=round(optimal_rgain,rgb_decimals)
disp_bgain=round(optimal_bgain,rgb_decimals)
optimal_rgain=round(optimal_rgain,decimals)
optimal_bgain=round(optimal_bgain,decimals)

print('')
print('Optimal rgain: '+str(disp_rgain))
print('Optimal bgain: '+str(disp_bgain))
print('Trials       : '+str(trials))
print('')
print('Time elapsed: '+str(ct2-ct1))
if trial<trials:
    print('')

# Save calibration series data to a csv file
m=np.array((calibrations,rgains,bgains)).T
with open(curdir+'awbgains-trials-'+dt_part+'.csv', 'w') as f:
    writer = csv.writer(f,delimiter=',')
    header=['calibration','rgain_opt','bgain_opt']
    writer.writerow(header)
    for row in m:
        writer.writerow([int(row[0]),row[1],row[2]])


xs=np.arange(1,trials+1)
xlabel='Trial'
  
fig=plt.figure()
plt.title("Red gain")
plt.ylabel("Gain value")
plt.xlabel(xlabel)
plt.xlim(1,trials)
plt.plot(xs,rgains,color="red")
plt.grid()
#plt.show()
plt.savefig(curdir+'awbgains-rgain-'+dt_part+'.png',dpi=300)
plt.close(fig)    

fig=plt.figure()
plt.title("Blue gain")
plt.ylabel("Gain value")
plt.xlabel(xlabel)
plt.xlim(1,trials)
plt.plot(xs,bgains,color="blue")
plt.grid()
#plt.show()
plt.savefig(curdir+'awbgains-bgain'+dt_part+'.png',dpi=300)
plt.close(fig) 
    
series=np.array(series).T
   
# Calculate CI for rgain and bgain mean values
r_gains=series[1]
b_gains=series[2]
N=trials

method=''
if N>1 and N<=30:
    # Use Student-t distribution
    method="Student's t-distribution"
    ci_rgain=st.t.interval(p, df=N-1,
              loc=np.mean(r_gains),
              scale=st.sem(r_gains))
    ci_bgain=st.t.interval(p, df=N-1,
              loc=np.mean(b_gains),
              scale=st.sem(b_gains))
elif N>30:
    # Use normal distribution
    method='Normal distribution'
    ci_rgain=st.norm.interval(alpha=p,
              loc=np.mean(r_gains),
              scale=st.sem(r_gains))
    ci_bgain=st.norm.interval(alpha=p,
              loc=np.mean(b_gains),
              scale=st.sem(b_gains))

# Add results to a log
logfile=curdir+'awbgains-'+dt_part+'.log'
log=Log(logfile)

log.add('AWBgains log file created on '+str(ct0))
log.add('')
log.add('Shutter speed: '+str(exposure)+' µs')
log.add('')

rmean=np.mean(r_gains)
bmean=np.mean(b_gains)
cir_half=(ci_rgain[1]-ci_rgain[0])/2
cib_half=(ci_bgain[1]-ci_bgain[0])/2

frmean=round(np.mean(r_gains),rgb_decimals)
fbmean=round(np.mean(b_gains),rgb_decimals)
fcir_half=round((ci_rgain[1]-ci_rgain[0])/2,rgb_decimals)
fcib_half=round((ci_bgain[1]-ci_bgain[0])/2,rgb_decimals)

ptext=str(int(p*100))+'%'    
log.add('Trials: '+str(trials))
log.add('p     : '+str(p))
log.add('Method: '+method)
log.add('')
    
log.add('rgain= '+str(frmean)+'±'+str(fcir_half))
log.add('bgain= '+str(fbmean)+'±'+str(fcib_half))
log.add('')

# Template: rgain= 1.2 [95% CI: 1.1–1.3]
log.add('rgain= '+str(frmean)+' ['+ptext+' CI: '+str(round(ci_rgain[0],rgb_decimals))+','+str(round(ci_rgain[1],rgb_decimals))+']')
log.add('bgain= '+str(fbmean)+' ['+ptext+' CI: '+str(round(ci_bgain[0],rgb_decimals))+','+str(round(ci_bgain[1],rgb_decimals))+']')
    
log.add('')
log.add('Time elapsed: '+str(ct2-ct1))
if N>1:
    print('')
    log.print_lines()
log.save_to_file()

def generate_xlist(number):
    n=int(number)
    xlist=[]
    if number<=10:
        xlist=list(range(0,n+1)) 
    elif number<=50:
        i=n
        while i % 5 != 0:
            i+=1
        xlist=list(range(0,i+1,5))
    elif number<=100:
        i=n
        while i % 10 != 0:
            i+=1
        xlist=list(range(0,i+1,10))
    return xlist[1:]

# Plot a rgain,bgain figure when N>1
if N>1:
    
    # Generate a series rgain, bgain scatter plot with CI
    fig=plt.figure()
    ax=fig.add_subplot(111)
    tmp='Red and blue gains with '+ptext+' CI'+'\n'
    tmp+='N= '+str(N)+', '+method
    plt.title(tmp)
    plt.ylabel('rgain')
    plt.xlabel('bgain')
    
    # Calculate series limits for x and y axes
    factor=1

    xmin=np.min(b_gains)
    xmax=np.max(b_gains)
    ymin=np.min(r_gains)
    ymax=np.max(r_gains)
    xhalf=xmax-xmin
    yhalf=ymax-ymin
    xmin-=xhalf*factor
    xmax+=xhalf*factor
    ymin-=yhalf*factor
    ymax+=yhalf*factor

    plt.xlim(xmin,xmax)
    plt.ylim(ymin,ymax)
    
    # Plot a series optimal gains
    plt.plot(b_gains,r_gains,'ko')
    
    # Draw CI rectangle
    rect=matplotlib.patches.Rectangle((ci_bgain[0],ci_rgain[0]),
                                      ci_bgain[1]-ci_bgain[0],
                                      ci_rgain[1]-ci_rgain[0],
                                      facecolor='red',
                                      alpha=0.1)
    ax.add_patch(rect)
    plt.plot(np.mean(b_gains),np.mean(r_gains),marker='D',color='red')
    
    plt.grid()
    plt.savefig(curdir+'awbgains-trials-'+dt_part+'.png',dpi=300)
    plt.close(fig)

    # Plot a series rgain figure
    fig=plt.figure()
    tmp='Red gain with '+ptext+' CI'+'\n'
    tmp+='N= '+str(N)+', '+method
    plt.title(tmp)
    plt.ylabel('rgain')
    plt.xlabel('Trial')
    plt.xlim(1,N)
    
    ymin=np.min(r_gains)
    ymax=np.max(r_gains)
    xhalf=xmax-xmin
    yhalf=ymax-ymin
    xmin-=xhalf*factor
    xmax+=xhalf*factor
    ymin-=yhalf*factor
    ymax+=yhalf*factor
    
    plt.ylim(ymin,ymax)
    plt.axhline(ci_rgain[0],color='k',linestyle=':')
    plt.axhline(rmean,color='k')
    plt.axhline(ci_rgain[1],color='k',linestyle=':')
    xs=generate_xlist(N)
    plt.xticks(xs)
    plt.plot(range(1,N+1),r_gains,'ro')
    plt.grid()
    plt.savefig(curdir+'awbgains-trials-rgain-'+dt_part+'.png',dpi=300)
    plt.close(fig)

    # Plot a series bgain figure
    fig=plt.figure()
    tmp='Blue gain with '+ptext+' CI'+'\n'
    tmp+='N= '+str(N)+', '+method
    plt.title(tmp)
    plt.ylabel('bgain')
    plt.xlabel('Trial')
    plt.xlim(1,N)
    
    ymin=np.min(b_gains)
    ymax=np.max(b_gains)
    xhalf=xmax-xmin
    yhalf=ymax-ymin
    xmin-=xhalf*factor
    xmax+=xhalf*factor
    ymin-=yhalf*factor
    ymax+=yhalf*factor
    
    plt.ylim(ymin,ymax)
    plt.axhline(ci_bgain[0],color='k',linestyle=':')
    plt.axhline(bmean,color='k')
    plt.axhline(ci_bgain[1],color='k',linestyle=':')
    xs=generate_xlist(N)
    plt.xticks(xs)
    plt.plot(range(1,N+1),b_gains,'bo')
    plt.grid()
    plt.savefig(curdir+'awbgains-trials-bgain-'+dt_part+'.png',dpi=300)
    plt.close(fig)
