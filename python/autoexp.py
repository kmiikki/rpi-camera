#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Thu May  5 11:10:24 2022

@author: Kim Miikki
'''
import argparse
import os
from pathlib import Path
import cv2
import matplotlib.pyplot as plt
import numpy as np
from picamera import PiCamera
import picamera.array
import sys
from datetime import datetime
from time import sleep
from rpi.camerainfo import *
from rpi.roi import *

np.set_printoptions(suppress=True)

res=[[320,240],[640,480],[800,600],[1024,768]]

# Camera settings
exposure=20000 # µs
exp_max=1000000
ss=-1
rgain=-1
bgain=-1
exp_mode='off'
awb_mode='auto'
iso=100
red=1.0
blue=1.0
mode=0 # 1024x768

if camera_revision=='imx477':
    min_ss=250
    max_ss=camera_max_exposure
elif camera_revision=='imx219':
    min_ss=1
    max_ss=camera_max_exposure
    
# Thresholds
uthreshold=0
othreshold=0
thres=255

singleImage=False
previewImage=True
showFigures=False
createFigures=True

log=[]

print('Auto Exposure Bracketing Utility - (C) Kim Miikki 2022')
log.append('Auto Exposure Bracketing Utility - (C) Kim Miikki 2022')

# Parse arguments
parser=argparse.ArgumentParser()
parser.add_argument('-m',type=int,help='mode (0-'+str(len(res))+')',required=False)
parser.add_argument('-t',type=int,help='high threshold value (1-255)',required=False)
parser.add_argument('-ss',type=int,help='shutter speed in µs',required=False)
parser.add_argument('-awbg',type=str,help='awbg r_gain,b_gain',required=False)
parser.add_argument('-show', action='store_true', help='show figures on screen')
parser.add_argument('-n', action='store_true', help='do not create figures')
args = parser.parse_args()

if args.m!=None:
    try:
        mode=int(args.m)
    except:
        print('Illegal mode value!')
        sys.exit(0)
    if mode<0:
        mode=0
    elif mode>len(res):
        mode=len(res)

if args.t!=None:
    try:
        thres=int(args.t)
    except:
        print('Illegal threshold value!')
        sys.exit(0)
    if thres<1:
        thres=1
    elif thres>255:
        thres=255

if args.ss!=None:
    singleImage=True
    try:
        ss=str(args.ss)
        ss=int(ss)
    except:
        print('Illegal shutter speed!')
        sys.exit(0)
    
if args.awbg!=None:
    awb_mode='off'
    result=True
    awbg=args.awbg
    awbg=awbg.strip()
    if awbg.count(',')!=1:
        result=False
    pos=awbg.find(',')
    if pos==0 or len(awbg)==pos+1:
        result=False
    if result:
        rgain,bgain=awbg.split(',')
        try:
            red=float(rgain)
            blue=float(bgain)
        except:
            result=False
    if not result:
        print('Illegal awbg value!')
        sys.exit(0)

if args.show:
    showFigures=True

if args.n:
    createFigures=False
    showFigures=False

width=res[mode][0]
height=res[mode][1]
pip=(0,0,width,height)

roi_result=validate_roi_values()
if not roi_result:
    roi_x0=0.5-width/(2*camera_maxx)
    roi_y0=0.5-height/(2*camera_maxy)
    roi_w=width/camera_maxx
    roi_h=height/camera_maxy
else:
    print('')
    display_roi_status()
    log.append('')
    log.append('ROI file found in '+roi_dir+' directory: '+str(roi_x0)+','+str(roi_y0)+','+str(roi_w)+','+str(roi_h))
zoom=(roi_x0,roi_y0,roi_w,roi_h)

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
print('')
print('Current directory:')
print(curdir)
print('')
log.append('')
log.append('Current directory:')
log.append(curdir)
log.append('')
curdir+='/'

# Set camera options
camera=PiCamera(resolution=(width,height))
camera.iso=iso
if previewImage:
    camera.start_preview(fullscreen=False,window=pip)
# Wait for the automatic gain control to settle
sleep(2)

# Now fix the values
camera.exposure_mode=exp_mode
camera.awb_mode=awb_mode
camera.shutter_speed=int(exposure)
camera.zoom=zoom
camera.awb_gains=(red,blue)
camera.framerate = 0.005

a=min_ss
b=exposure
uexp=0
oexp=0
direction=1
lastUp=False
lastDown=False

def step(minval,maxval,steps=2):
    minval=int(minval)
    maxval=int(maxval)
    steps=int(steps)
    if steps<2:
        steps=2
    return int(round((maxval-minval)/steps))

st=step(a,b,5)
if not singleImage:
    ss=a
exposures=[]
uexps=[]
oexps=[]
rgb=[]
rgb_last=[]
out= 'Exp (µs)'.rjust(10)
out+='Low'.rjust(10)
out+='High'.rjust(10)
out+='Step'.rjust(10)
print(out)
log.append(out)
out=(' '+'-'*9)*4
print(out)
log.append(out)

t1=datetime.now()
with picamera.array.PiRGBArray(camera) as output:
    while True:
        camera.shutter_speed=ss
        camera.capture(output,'rgb')
        if len(rgb)>0:
            rgb_last=np.copy(rgb)
        rgb=np.array(output.array)
        bw=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
        hist=cv2.calcHist([bw],[0],None,[256],[0, 256])
        uexp=int(hist[0][0])
        oexp=int(hist[thres:].sum())
        
        # Right direction
        if direction==1:
            if oexp<=othreshold:
                a=ss
                if uexp>=10:
                    st*=2
            else:
                b=ss
                st=step(a,b,10)
                direction=-1

        # Left direction
        elif direction==-1:
            if oexp>othreshold:
                b=ss-st
            else:
                a=ss-st
                st=step(a,b,10)
                direction=1

        out= str(ss).rjust(10)
        out+=str(uexp).rjust(10)
        out+=str(oexp).rjust(10)
        out+=str(st).rjust(10)
        print(out)
        log.append(out)
        output.truncate(0)
        exposures.append(ss)
        uexps.append(uexp)
        oexps.append(oexp)
        if singleImage:
            break
        if st<=1:
            break
        ss=ss+direction*st
        if ss>exp_max:
            break

camera.close()
t2=datetime.now()
print('')
print('Time elapsed: '+str(t2-t1))
log.append('')
log.append('Time elapsed: '+str(t2-t1))

# Compare oexp count values of the two last shutter speeds
if ss<=exp_max and len(exposures)>=2:
    if oexps[-1]>oexps[-2]:
        ss=exposures[-2]
        exposures=exposures[:-1]
        uexp=uexps[-2]
        oexp=oexps[-2]
        rgb=rgb_last

# Calculate BW and RGB histograms, means and medians
bw=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY)
hist=cv2.calcHist([bw],[0],None,[256],[0, 256])
chans=cv2.split(rgb)

rs=cv2.calcHist([chans[0]], [0], None, [256], [0, 256])
gs=cv2.calcHist([chans[1]], [0], None, [256], [0, 256])
bs=cv2.calcHist([chans[2]], [0], None, [256], [0, 256])

bw_weights=(hist/hist.sum()).T[0]
rweights=(rs/rs.sum()).T[0]
gweights=(gs/gs.sum()).T[0]
bweights=(bs/bs.sum()).T[0]

vals=np.linspace(0,255,256)
bw_mean=np.average(vals,weights=bw_weights)
r_mean=np.average(vals,weights=rweights)
g_mean=np.average(vals,weights=gweights)
b_mean=np.average(vals,weights=bweights)
ch_means=[bw_mean,r_mean,g_mean,b_mean]
colors=('r','g','b')

print('')
log.append('')
if ss<=exp_max:
    print('Shutter speed: '+str(round(ss/1000,1))+' ms')
    print('Shutter speed: '+str(ss)+' µs')
    print('Threshold    : '+str(thres))
    print('Low count    : '+str(uexp))
    print('High count   : '+str(oexp))
    print('')
    out='Ch  Mean (weighted)'
    print(out)
    chs=['BW','R','G','B']
    i=0
    for ch in chs:
        out=ch.ljust(2)
        out+=str(round(ch_means[i],1)).rjust(7)
        print(out)
        i+=1
    # Append resuklts to log
    log.append('Shutter speed: '+str(round(ss/1000,1))+' ms')
    log.append('Shutter speed: '+str(ss)+' µs')
    log.append('Threshold    : '+str(thres))
    log.append('Low count    : '+str(uexp))
    log.append('High count   : '+str(oexp))
    log.append('')
    out='Ch  Mean (weighted)'
    log.append(out)
    i=0
    for ch in chs:
        out=ch.ljust(2)
        out+=str(round(ch_means[i],1)).rjust(7)
        log.append(out)
        i+=1
    
else:
    print('Shutter speed > 1 s')
    log.append('Shutter speed > 1 s')

# File name prefixes
# exp-hist
# exp-histbw
# exp-iter
# exp-imap
# exp-img
# Post part of stem: -yyyy-mm-dd-hhmmss
#
# Log file name: 
# exp-yyyy-mm-dd-hhmmss.log

ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M%S')

if createFigures:
    # Plot BW and RGB figures
    fig=plt.figure()
    plt.xlabel('Color value')
    plt.ylabel('Pixel count')
    for (chan,color) in zip(chans,colors):
        hist_rgb = cv2.calcHist([chan], [0], None, [256], [0, 256])
        plt.plot(hist_rgb, color=color)
        plt.xlim([0, 256])
    if thres<255:
        plt.axvline(x=thres,color='0.8',linestyle='--')    
    plt.savefig(curdir+'exp-hist-'+dt_part+'.png',dpi=300)
    if showFigures:
        plt.show()
    plt.close(fig)
    
    fig=plt.figure()
    plt.xlabel('Gray value')
    plt.ylabel('Pixel count')
    plt.xlim([0, 256])
    plt.plot(hist, color='k')
    if thres<255:
        plt.axvline(x=thres,color='0.8',linestyle='--')
    plt.savefig(curdir+'exp-histbw-'+dt_part+'.png',dpi=300)
    if showFigures:
        plt.show()
    plt.close(fig)
    
    if not singleImage:
        # Plot ss=f(exp)
        xs=np.linspace(1,len(exposures),len(exposures)).astype(int)
        fig=plt.figure()
        plt.xlabel('Exposure number')
        plt.ylabel('Shutter speed (ms)')
        plt.xlim([1,len(exposures)])
        plt.plot(xs,np.array(exposures)/1000,color='k',marker='s')
        plt.grid()
        plt.savefig(curdir+'exp-iter-'+dt_part+'.png',dpi=300)
        if showFigures:
            plt.show()
        plt.close(fig)
    
    # Save image with optimal exposure as an image map, and bare image
    fig=plt.figure()
    plt.xlabel('X coordinate')
    plt.ylabel('Y coordinate')
    plt.imshow(rgb)
    plt.savefig(curdir+'exp-imap-'+dt_part+'.png',dpi=300)
    if showFigures:
        plt.show()
    plt.close(fig)
    
    cv2.imwrite(curdir+'exp-img-'+dt_part+'.png',cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    
# Create a log file
file=open(curdir+'exp-'+dt_part+'.log','w')
for line in log:
    file.write(line+'\n')
file.close()

