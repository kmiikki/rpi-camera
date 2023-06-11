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
#import picamera.array
#from picamera import PiCamera

res=[[320,240],[640,480],[800,600],[1024,768],[1280,1024]]
mode=0

# Camera settings
exposure=20000 # µs
exp_mode="off"
awb_mode="off"
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
iterations=20 # Default= 20

min_trials=2
max_trials=100
trials=5
p=0.95
isTrials=False
isFigs=True

csv_files=[]
in_row=0
startpass_filter='awbgains-trials'
isAnalysis=False

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

print('Optimal AWB - (C) Kim Miikki 2023')
print('')

parser=argparse.ArgumentParser()
parser.add_argument('-m',type=int,help='mode (0-'+str(len(res))+')',required=False)
parser.add_argument('-ss', type=int, help='shutter speed in µs',required=False)
parser.add_argument('-i', type=int, help='iterations (default='+str(iterations)+')',required=False)
parser.add_argument('-n', type=int, help='number of repetition trials ('+str(min_trials)+'-'+str(max_trials)+')',required=False)
parser.add_argument('-figs',action='store_true',help='create all figures')
parser.add_argument('-a',nargs='?', type=str, help='analysis mode: optional start filter for the csv file(s)', required=False)
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

# Validate iterations
if args.i != None:
    tmp=int(args.i)
    if tmp<1:
        print('A positive number of iterations is required. Using default number: '+str(iterations))
        print('')
    else:
        iterations=tmp

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
else:
    trials=1

if args.figs:
    isFigs=True

if args.a == None and '-a' in sys.argv:
    isAnalysis=True
elif args.a != None:
    startpass_filter=args.a
    isAnalysis=True
      
print('Current directory:')
curdir=os.getcwd()
path=Path(curdir)
print(curdir)
if curdir[-1] != '/':
    curdir+='/'

def parse_csv(filename):
    global series
    global in_row
    result=False
    # Template 1: calibration, rgain(0), bgain(0), rgain_opt, bgain_opt, distance, evaluations, position, time (s)
    # Template 1: columns: 9
    # Template 2: Iteration, rgain, bgain, R mean, G mean, B mean, ABS(RG), ABS(RB), ABS(GR), mdist
    # Template 2 columns: 10
    # Template 3: calibration,rgain,bgain
    
    try:
        df=pd.read_csv(filename)
    except:
        pass
    
    r=-1
    c=-1
    try:
        r,c=df.shape
    except:
        pass
    
    required_keys=True
    # Template 1
    if c==9:
        keys=['calibration', 'rgain(0)', 'bgain(0)','rgain_opt','bgain_opt','distance','evaluations','position','time (s)']
        for key in keys:
            if key not in df.keys():
                required_keys=False
                break
        if required_keys:
            try:
                i=0
                while i<len(df):
                    lst=df.iloc[i].to_list()
                    in_row+=1
                    lst[0]=in_row
                    series.append(lst)
                    i+=1
                result=True
            except:
                pass
    # Template 2
    elif c==10:
        keys=['Iteration', 'rgain', 'bgain', 'R mean', 'G mean', 'B mean', 'ABS(RG)', 'ABS(RB)', 'ABS(GB)', 'mdist']
        for key in keys:
            if key not in df.keys():
                print(key)
                print(df.keys())
                required_keys=False
                break
        if required_keys:
            try:
                # Read the first calibration row
                lst=df.iloc[0].to_list()
                
                # Get start calibration values
                rgain0=lst[1]
                bgain0=lst[2]
                
                # Read the last calibration row
                lst=df.iloc[-1].to_list()              
                
                # Get the number of calibration
                in_row+=1
                cal_number=in_row
                
                rgain_opt=lst[1]
                bgain_opt=lst[2]
                
                # Calculate the RGB distance
                r=lst[3]
                g=lst[4]
                b=lst[5]
                distance=(abs(r-g)+abs(r-b)+abs(g-b))/3
                
                # Fill the rest of fields with 0
                evaluations=0
                position=0
                t=0
                
                row=[cal_number,rgain0,bgain0,rgain_opt,bgain_opt,distance,evaluations,position,t]                
                series.append(row)
                # i+=1
                result=True
            except:
                pass
    elif c==3:
        keys=['calibration','rgain','bgain']
        for key in keys:
            if key not in df.keys():
                required_keys=False
                break
        if required_keys:
            try:
                i=0
                while i<len(df):
                    lst=df.iloc[i].to_list()
                    in_row+=1
                    cal_number=in_row
                    rgain0=0
                    bgain0=0
                    rgain_opt=lst[1]
                    bgain_opt=lst[2]
                    
                    # Fill the rest of fields with 0
                    distance=0
                    evaluations=0
                    position=0
                    t=0
                    
                    row=[cal_number,rgain0,bgain0,rgain_opt,bgain_opt,distance,evaluations,position,t]                
                    series.append(row)
                    i+=1
                result=True
            except:
                pass
    return result

ct0=datetime.now()
dt_part_all=ct0.strftime("%Y%m%d-%H%M%S")

if isAnalysis:
    csv_files=sorted(glob.glob(startpass_filter+'*.csv'))
    for name in csv_files:
        result=parse_csv(name)
        if not result:
            print (name+': invalid data file')
    if len(series):
        trials=len(series)
    else:
        trials=0
            
if not isAnalysis:
    import picamera.array
    from picamera import PiCamera
    
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
    
    def objective_function(x):
        global count
        global rgains
        global bgains
        
        rgain, bgain = x
        # capture an image
        camera.awb_gains=(rgain,bgain)
        camera.capture(output,"rgb")
        rgb_means=np.array(output.array).mean(axis=(0,1))
        output.truncate(0)
        r=rgb_means[0]
        g=rgb_means[1]
        b=rgb_means[2]
        distance=(abs(r-g)+abs(r-b)+abs(g-b))/3
        count+=1
        # print(count,distance)
        if count % 5 == 0:
            print(".",end="")
        rgains.append(rgain)
        bgains.append(bgain)
        dists.append(distance)
        return distance
    
    # ct0=datetime.now()
    # dt_part_all=ct0.strftime("%Y%m%d-%H%M%S")
    
    for trial in range(1,trials+1):
        count=0
        dists=[]
        rgains=[]
        bgains=[]
    
        # Set camera options
        camera=PiCamera(resolution=(width,height))
        camera.iso=iso
        if previewImage:
            camera.start_preview(fullscreen=False,window=pip)
        # Wait for the automatic gain control to settle
        sleep(2)
    
        # Read the camera awb values
        awb=camera.awb_gains
        awb_red=float(awb[0])
        awb_blue=float(awb[1])
        
        # Now fix the values
        camera.exposure_mode=exp_mode
        camera.awb_mode=awb_mode
        camera.shutter_speed=int(exposure)
        camera.zoom=zoom
        
        print('Calibration '+str(trial)+'/'+str(trials))
        print('Optimizing: ',end='')
        ct1=datetime.now()
        dt_part=ct1.strftime('%Y%m%d-%H%M%S')
        
        with picamera.array.PiRGBArray(camera) as output:
            # Define bounds for the optimization region
            bounds=[tuple(bs),tuple(rs)]
        
            # Initial guess for rgain and bgain values
            initial_guess=[awb_red,awb_blue]
            #initial_guess=[r_initial,b_initial]
        
            # Perform optimization using Nelder-Mead algorithm
            result=minimize(objective_function,initial_guess,bounds=bounds,method='Nelder-Mead',options={'maxiter':iterations})
            optimal_rgain, optimal_bgain=result.x
        
        
            # Capture a sample image
            camera.awb_gains=(optimal_rgain,optimal_bgain)
            if isFigs:
                with picamera.array.PiRGBArray(camera) as output:
                    camera.capture(output,'rgb')
                    cv2.imwrite(curdir+'awbgains-cal-image-'+dt_part+'.png',np.array(output.array))
                    output.truncate(0)
            camera.close()
        
        ct2=datetime.now()
        
        # Find the index of color minimum distance
        dists=np.array(dists)
        pos=np.argmin(dists)
        evaluations=np.arange(1,count+1)
        rgains=np.array(rgains)
        bgains=np.array(bgains)
        
        disp_dist=round(dists[pos],rgb_decimals)
        dist=round(dists[pos],decimals)
        
        disp_rgain=round(optimal_rgain,rgb_decimals)
        disp_bgain=round(optimal_bgain,rgb_decimals)        
        optimal_rgain=round(optimal_rgain,decimals)
        optimal_bgain=round(optimal_bgain,decimals)
        
        print('\n')
        print('Optimal rgain: '+str(disp_rgain))
        print('Optimal bgain: '+str(disp_bgain))
        print('Mean distance: '+str(disp_dist))
        print('')
        print('Time elapsed: '+str(ct2-ct1))
        if trial<trials:
            print('')
        
        # Save calibration series data to a csv file
        m=np.array((evaluations,rgains,bgains,dists)).T
        with open(curdir+'awbgains-data-'+dt_part+'.csv', 'w') as f:
            writer = csv.writer(f,delimiter=',')
            header=['evaluation','rgain','bgain','mdist']
            writer.writerow(header)
            for row in m:
                writer.writerow([int(row[0]),row[1],row[2],row[3]])
        
        xlabel='Evaluation'
        xs=np.arange(1,count+1)
        
        if isFigs:
            # Create a calibration series for ABS(gray)
            fig=plt.figure()
            plt.title('Gray mean absolute distance')
            plt.ylabel('Gray mean absolute distance value')
            plt.xlabel(xlabel)
            plt.xlim(1,count)
            ymin=0
            ymax=np.max(dists)
            plt.ylim(ymin,ymax)
            plt.plot(xs,dists,color="k")
            plt.plot(pos+1,dist,'ro')
            plt.grid()
            plt.savefig(curdir+'awbgains-graydist-'+dt_part+'.png',dpi=300)
            plt.close(fig)
            
            fig=plt.figure()
            plt.title("Red gain")
            plt.ylabel("Gain value")
            plt.xlabel(xlabel)
            plt.xlim(1,count)
            plt.plot(xs,rgains,color="red")
            plt.grid()
            plt.savefig(curdir+'awbgains-rgain-'+dt_part+'.png',dpi=300)
            plt.close(fig)    
            
            fig=plt.figure()
            plt.title("Blue gain")
            plt.ylabel("Gain value")
            plt.xlabel(xlabel)
            plt.xlim(1,count)
            plt.plot(xs,bgains,color="blue")
            plt.grid()
            plt.savefig(curdir+'awbgains-bgain'+dt_part+'.png',dpi=300)
            plt.close(fig) 
    
        # calibration, rgain(0), bgain(0), rgain_opt, bgain_opt, distance, evaluations, position, time
        series.append([trial,
                       rgains[0],bgains[0],
                       optimal_rgain,optimal_bgain,
                       dist, count, pos+1, (ct2-ct1).total_seconds()])

# sys.exit(0)
    
series=np.array(series).T
ct3=datetime.now()
total_time=str(ct3-ct0)
   
# Calculate CI for rgain and bgain mean values
r_gains=series[3]
b_gains=series[4]
opt_dists=series[5]
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
logfile=curdir+'awbgains-'+dt_part_all+'.log'
log=Log(logfile)

log.add('AWBgains log file created on '+str(ct0))
log.add('')
if not isAnalysis:
    log.add('Shutter speed: '+str(exposure)+' µs')
    log.add('Iterations: '+str(iterations))
else:
    log.add('Analysis mode')
    log.add('-------------')
    log.add('Files included in the analysis:')
    for name in csv_files:
        log.add(name)
log.add('')

if N==1:
    log.add('Optimal rgain: '+str(optimal_rgain))
    log.add('Optimal bgain: '+str(optimal_bgain))
    log.add('Mean distance: '+str(dist))
    log.add('')
    log.add('Time elapsed: '+str(ct2-ct1))
elif N>1:
    rmean=np.mean(r_gains)
    bmean=np.mean(b_gains)
    dists_mean=np.mean(opt_dists)
    cir_half=(ci_rgain[1]-ci_rgain[0])/2
    cib_half=(ci_bgain[1]-ci_bgain[0])/2
    opt_dist_min=np.min(opt_dists)
    opt_dist_max=np.max(opt_dists)
    opt_dist_mean=np.mean(opt_dists)
    opt_dist_median=np.median(opt_dists)
    opt_dist_sem=st.sem(opt_dists)

    frmean=round(np.mean(r_gains),rgb_decimals)
    fbmean=round(np.mean(b_gains),rgb_decimals)
    fdists_mean=round(np.mean(opt_dists),rgb_decimals)
    fcir_half=round((ci_rgain[1]-ci_rgain[0])/2,rgb_decimals)
    fcib_half=round((ci_bgain[1]-ci_bgain[0])/2,rgb_decimals)
    fopt_dist_min=round(np.min(opt_dists),rgb_decimals)
    fopt_dist_max=round(np.max(opt_dists),rgb_decimals)
    fopt_dist_mean=round(np.mean(opt_dists),rgb_decimals)
    fopt_dist_median=round(np.median(opt_dists),rgb_decimals)
    fopt_dist_sem=round(st.sem(opt_dists),rgb_decimals)
    
    ptext=str(int(p*100))+'%'    
    log.add('Trials: '+str(N))
    log.add('p     : '+str(p))
    log.add('Method: '+method)
    log.add('')
    
    log.add('Optimal distances:')
    log.add('Min   : '+str(fopt_dist_min))
    log.add('Max   : '+str(fopt_dist_max))
    log.add('Mean  : '+str(fopt_dist_mean))
    log.add('Median: '+str(fopt_dist_median))
    log.add('SEM   : '+str(fopt_dist_sem))
    log.add('')
    
    log.add('rgain= '+str(frmean)+'±'+str(fcir_half))
    log.add('bgain= '+str(fbmean)+'±'+str(fcib_half))
    log.add('')
    
    # Template: rgain= 1.2 [95% CI: 1.1–1.3]
    log.add('rgain= '+str(frmean)+' ['+ptext+' CI: '+str(round(ci_rgain[0],rgb_decimals))+','+str(round(ci_rgain[1],rgb_decimals))+']')
    log.add('bgain= '+str(fbmean)+' ['+ptext+' CI: '+str(round(ci_bgain[0],rgb_decimals))+','+str(round(ci_bgain[1],rgb_decimals))+']')
    
log.add('')
log.add('Total time elapsed: '+total_time)
if N>1:
    print('')
    log.print_lines()
log.save_to_file()

#sys.exit(0)

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
    # Save series calibration series data to a csv file
    with open(curdir+'awbgains-trials-'+dt_part_all+'.csv', 'w') as f:
        writer = csv.writer(f,delimiter=',')
        header=['calibration', 'rgain(0)', 'bgain(0)', 'rgain_opt', 'bgain_opt',
                'distance', 'evaluations', 'position', 'time (s)']
        writer.writerow(header)
        for row in series.T:
            tmp=[]
            tmp.append(int(row[0]))    # calibration
            tmp.append(row[1])         # rgain(0)
            tmp.append(row[2])         # bgain(0)
            tmp.append(row[3])         # rgain_opt
            tmp.append(row[4])         # bgain_opt
            tmp.append(row[5])         # distance
            tmp.append(int(row[6]))    # evaluations
            tmp.append(int(row[7]))    # position
            tmp.append(row[8])         # distance
            writer.writerow(tmp)
    
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
    plt.savefig(curdir+'awbgains-trials-'+dt_part_all+'.png',dpi=300)
    plt.close(fig)

    # Plot a series rgain figure
    fig=plt.figure()
    tmp='Red gain with '+ptext+' CI'+'\n'
    tmp+='N= '+str(N)+', '+method
    plt.title(tmp)
    plt.ylabel('rgain')
    plt.xlabel('Calibration')
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
    plt.savefig(curdir+'awbgains-trials-rgain-'+dt_part_all+'.png',dpi=300)
    plt.close(fig)

    # Plot a series bgain figure
    fig=plt.figure()
    tmp='Blue gain with '+ptext+' CI'+'\n'
    tmp+='N= '+str(N)+', '+method
    plt.title(tmp)
    plt.ylabel('bgain')
    plt.xlabel('Calibration')
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
    plt.savefig(curdir+'awbgains-trials-bgain-'+dt_part_all+'.png',dpi=300)
    plt.close(fig)
