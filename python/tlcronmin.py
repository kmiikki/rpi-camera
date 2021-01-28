#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:16:31 2020

@author: Kim Miikki

Usage:
tlcronmin.py   : Setup time-lapse shooting
tlcronmin.py -s: Start time-lapse shooting
tlcronmin.py -e: End time-lapse shooting
tlcronmin.py -c: Capture a time-lapse picture

/tmp/.tlcron.lock
#'path to time-lapse directory':    ready to start time-laps shooting
'path to time-lapse directory':     time-lapse shooting started
-                                   time-lapse shooting stopped

Required moudule installation:
sudo pip3 install python-crontab

"""

import argparse
import ast
import csv
import datetime
import gc
import os
import sys
from crontab import CronTab
from pathlib import Path

user="pi"
python3_dir="/usr/bin/python3"
install_dir="/opt/tools"
curdir=""
lockfile=".tlcronmin.lock"
idfile="TLID"
configfile="time-lapse.csv"
txtfile="time-lapse.txt"
logfile="time-lapse.log"
delimiter=","
digits=6
preview_time=1000 # 1000 ms
project=""
project_path=""

startTL=False
stopTL=False
captureTL=False
firstFrame=False
previewImage=False

minutes_min=1
# Julian year: 1 a = 365.25 d
a=365.25
minutes_max=int(a*24*60)

# Default parameters
params={
        "q"        : 90,
        "t"        : 1000,
        "ISO"      : 100,
        "ss"       : 20000,
        "awb"      : True,
        "ex"       : True,
        "bgain"    : 1.0,
        "rgain"    : 1.0,
        "ag"       : 1.0,
        "f"       : False,
        "digits"   : 4,
        "min"      : 1,
        }

"""
Image and time-lapse parameters

-q          : Quality
-t,         : Time (in ms) before takes picture and shuts down
-ISO, --ISO	: Set capture ISO
-ss, --shutter	: Set shutter speed in microseconds
-awb, --awb	: Set AWB mode (see Notes)
-ex, --exposure	: Set exposure mode (see Notes)
-bgain      : Blue gain
-rgain      : Red gain
(-awbg, --awbgains	: Set AWB gains - AWB mode must be off)
-ag, --analoggain	: Set the analog gain (floating point)
-f,             : Fullscreen preview mode
-d  : Time-lapse frame number digits
-min: time-lapse interval in minutes

"""

def cronstr():
    time_s="* * * * *"    
    command_s=python3_dir+" "
    command_s+=install_dir+"/tlcronmin.py -c"
    return time_s,command_s

def dtime():
    now=datetime.datetime.now()
    return now.strftime("%Y%m%d-%H%M%S")

def swap(a,b):
    return b,a

def time_and_unit(minimum,maximum):
    if minimum>maximum:
        minimum,maximum=swap(minimum,maximum)
    unit="min"
    q=minimum // 60
    divisor=1
    if q>=1:
        unit="h"
        divisor*=60
    q=minimum // (60*24)
    if q>=1:
        unit="d"
        divisor*=24
    q=minimum // (60*24*365.25)
    if q>=1:
        unit="a"
        divisor*=a
    t1=minimum/divisor
    t2=maximum/divisor
    if float(t1).is_integer() and float(t2).is_integer():
        t1=int(t1)
        t2=int(t2)
    else:
        t1=round(t1,1)
        t2=round(t2,1)
    return t1,t2,unit

parser=argparse.ArgumentParser()
parser.add_argument("-s", action="store_true", help="start time-lapse shooting")
parser.add_argument("-e", action="store_true", help="stop time-lapse shooting")
parser.add_argument("-c", action="store_true", help="capture time-lapse image")
parser.add_argument("-p", action="store_true", help="preview image before capture")
args = parser.parse_args()

if args.s:
    startTL=True
if args.e:
    stopTL=True
if args.c:
    captureTL=True
if args.p:
    previewImage=True

if [startTL,stopTL,captureTL].count(True)>1:
    print("Only one argument is allowed!")
    sys.exit(1)

# Setup time-lapse
if not True in [startTL,stopTL,captureTL]:
    from rpi.camerainfo import *
    from rpi.inputs2 import *

    print("Crontab based time-lapse camera ver. 2.0")

    # Get current directory
    curdir=os.getcwd()
    path=Path(curdir)
    lock_exists = os.path.isfile("/tmp/"+lockfile) 
    if lock_exists:
        print("")
        print("Time-lapse lock file exists!")
        print("Terminate time-lapse job with the following command:")
        print("tlcronmin.py -e")
        sys.exit(0)

    print("")
    print("Current directory:")
    print(curdir)
    print("")
    project_dir=curdir
    
    # Time-lapse capture values section start
    #
    # Default values and ranges
    red_gain_min=0.1
    red_gain_max=10.0
    blue_gain_min=0.1
    blue_gain_max=10.0
    ag_min=1.0
    ag_max=12.0
    ag_default=1.0
    awbg_red_default=awbg_red
    awbg_blue_default=awbg_blue

    quality_default=90
    quality=inputValue("image quality",1,100,quality_default,"","Quality is out of range!",True)
    params["q"]=quality    
    
    iso=1
    iso_default=100
    iso_modes=[100,200,320,400,500,640,800]
    iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
    params["ISO"]=iso
    print("")

    autoexp_on=True
    autoexp_default=True
    autoexp_on=inputYesNo("EXP auto","Auto exposure on",autoexp_default)
    params["ex"]=autoexp_on
    print("")

    # Exposure unit: µs
    if not autoexp_on:
        exp_min=1
        exp_max=5000000
        exp_default=20000
        exposure=inputValue("exposure time",exp_min,exp_max,exp_default,"µs","Exposure is out of range!",True)
        params["ss"]=exposure
    else:
        params["ss"]=-1
    
    # Gain value: 1.0 to 12.0 for the IMX219 sensor on Camera Module V2
    awb_on=True
    default_awb=True
    awb_on=inputYesNo("AWB","AWB mode on",default_awb)
    params["awb"]=awb_on
    if not awb_on:
        print("")
        awbg_red=inputValue("red gain",1.0,8.0,awbg_red_default,"","Value out of range!",False)
        params["rgain"]=awbg_red
        awbg_blue=inputValue("blue gain",1.0,8.0,awbg_blue_default,"","Value out of range!",False)
        params["bgain"]=awbg_blue

    analog_gain=0
    analog_gain_default=1.0
    print("")
    analog_gain=inputValue("analog gain",ag_min,ag_max,ag_default,"","Analog gain is out of range!",False)
    params["ag"]=analog_gain
    print("")

    # Digits
    digits_default=4
    min_digits=1
    max_digits=8
    if min_digits>digits_default:
      digits_default=min_digits
    digits=inputValue("digits",min_digits,max_digits,digits_default,"","Digits is out of range!",True)
    params["digits"]=digits
    
    # Intervals
    interval_min=inputValue("interval",minutes_min,minutes_max,minutes_min,"min","Interval is out of range!",True)
    params['min']=interval_min
    time_min=int(((10**digits-1)-2)*interval_min)
    time_max=int(((10**digits-1)-1)*interval_min)
    t_min,t_max,u=time_and_unit(time_min,time_max)
    t_str=str(t_max)+" "+u
    print("Time-lapse maximum duration: "+t_str)
    print("")

    if not previewImage:
        previewImage=inputYesNo("Preview","Preview image",False)
    params["f"]=previewImage

    startTL=inputYesNo("Time-lapse","Start time-lapse now",True)

    #
    # Time-lapse capture values section end

    # Create a lock file
    file=open("/tmp/"+lockfile,"w")
    file.write("#"+curdir)
    file.close()

    # Delete old TLID file if found
    try:
        os.remove(project_dir+"/"+idfile)
    except:
        False
    
    user_cron = CronTab(user=user)
    print("Old crontab:")
    for job in user_cron:
        print(job)
    
    # Clear user crontab
    user_cron.remove_all()
    print("User "+user+" crontab cleared")
    print("")
      
    # Create initial TLID
    frame=0
    counter=0
    file=open(project_dir+"/"+idfile,"w")
    file.write(str(frame).zfill(digits)+"\n")
    file.write(str(counter))
    file.close()       
    
    # Write parameters to a configuration file
    config_file=open(project_dir+"/"+configfile,"w")
    writer=csv.writer(config_file,delimiter=delimiter)
    for key,val in params.items():
        writer.writerow([key,val])
    config_file.close()
    
    # Create a log file
    file=open(project_dir+"/"+logfile,"w")
    file.close()
    
    if not startTL:
        print("Time-lapse start command:")
        print("tlcronmin.py -s")

if startTL:
    # Get project directory
    file=open("/tmp/"+lockfile,"r")
    first_line=file.readline()
    file.close()
    if first_line.find("#")==0:
        # Activate lock file (remove #)
        first_line=first_line[1:]
        file=open("/tmp/"+lockfile,"w")
        file.write(first_line)
        file.close()
        firstFrame=True
        
        # New crontab job
        timestr,cmd=cronstr()
        user_cron = CronTab(user=user)
        job = user_cron.new(cmd)
        job.setall(timestr)
        user_cron.write()
        
        print("Time-lapse job started.")
        sys.exit(0)

if captureTL or firstFrame:
    # Get project directory
    try:
        file=open("/tmp/"+lockfile,"r")
        project_dir=file.readline()
        file.close()
    except:
        # Lock file not found
        sys.exit(1)
    if project_dir.find("#")==0:
        sys.exit(0)
    
    # Read the configuration file
    with open(project_dir+"/"+configfile,"r") as file:
        reader=csv.reader(file,delimiter=",")
        for row in reader:
            k,v=row
            if v in ["True","False"]:
                v=ast.literal_eval(v)
            try:
                params[k]=v
            except:
                False
    digits=int(params["digits"])

    # Read file ID and counter
    skip=False
    if not os.path.isfile(project_dir+"/"+idfile):
        print("TLID file not found!")
        sys.exit(1)
    try:
        file=open(project_dir+"/"+idfile,"r")
        frame=int(file.readline())
        counter=int(file.readline())
        file.close()
    except:
        print("Unable to open TLID file.")
        sys.exit(1)
    interval=int(params["min"])
    if counter % interval > 0:
        counter+=1
        file=open(project_dir+"/"+idfile,"w")
        file.write(str(frame).zfill(digits)+"\n")
        file.write(str(counter))
        file.close()
        skip=True
    else:
        counter+=1
    if frame==0:
        firstFrame=True
    if not skip:        
        frame+=1
        if len(str(frame))<=digits:        
                
            # Create capture string
            # Template:
            # raspistill -f -t 1000 -ISO 100 -q 90 -ss 200000 -ex off -awb off -ag 1 -awbg 1.5,2 -o file0001.jpg
            capture="raspistill "
            if bool(params["f"]):
                capture+="-f "
            else:
                capture+="-n "
            
            capture+="-t "+str(preview_time)+" "
            capture+="-ISO "+str(params["ISO"])+" "
            capture+="-q "+str(params["q"])+" "
            if params["ex"]:
                capture+="-ex auto "
            else:
                capture+="-ss "+str(params["ss"])+" "
            if params["awb"]:
                capture+="-awb auto "
            else:
                capture+="-awb off "
                capture+="-awbg "+str(params["rgain"])+","+str(params["bgain"])+" "
            capture+="-ag "+str(params["ag"])+" "
    
            # picture save string
            picname=str(frame).zfill(digits)+".jpg"
            capture+="-o "+project_dir+"/"+picname
        
            # Capture picture and append data to txt-file
            os.system(capture)
            if not firstFrame:
                capfile=open(project_dir+"/"+txtfile,"a+")
            else:
                capfile=open(project_dir+"/"+txtfile,"w")
    
            int_min=int(params["min"])
            capfile.write(str(frame)+delimiter+
                          str(int((int_min)*(frame-1)))+delimiter+
                          dtime()+delimiter+
                          picname+"\n")
            capfile.close()
            
            # Update TLID file
            file=open(project_dir+"/"+idfile,"w")
            file.write(str(frame).zfill(digits)+"\n")
            file.write(str(counter))
            file.close()
            
            # Write first capture command to log file
            if firstFrame:
                file=open(project_dir+"/"+logfile,"a+")
                file.write("Time-lapse capturing started at "+str(datetime.datetime.now())+"\n\n")
                file.write("First picture shoot command:\n")
                file.write(capture+"\n")
                file.close()
            
            firstFrame=False
        else:
            stopTL=True
        if frame==int(10**digits-1):
            stopTL=True

if stopTL:
    # Get project directory
    try:
        file=open("/tmp/"+lockfile,"r")
        project_dir=file.readline()
        file.close()
    except:
        sys.exit(1)

    try:
        file=open(project_dir+"/"+logfile,"a+")
        file.write("\nTime-lapse capturing finished at "+str(datetime.datetime.now())+"\n")
        file.close()
    except:
        False
    
    # Clear crontab
    user_cron = CronTab(user=user)
    user_cron.remove_all()
    user_cron.write()
    
    # Remove lock and tlid files
    try:
        if project_dir.find("#")==0:
            project_dir=project_dir[1:]
        os.remove(project_dir+"/"+idfile)
    except:
        False
    try:
        os.remove("/tmp/"+lockfile)
    except:
        False
    print("Time-lapse job finished.")
    
# Clean up memory

# Force a sweep
gc.collect()
    
# Clear references held by gc.garbage
del gc.garbage[:]


