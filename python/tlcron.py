#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 23 20:16:31 2020

@author: Kim Miikki

Usage:
tlcron.py   : Setup time-lapse shooting
tlcron.py -s: Start time-lapse shooting
tlcron.py -e: End time-lapse shooting
tlcron.py -c: Capture a time-lapse picture

/tmp/.tlcron.lock
#'path to time-lapse directory':    ready to start time-laps shooting
'path to time-lapse directory':     time-lapse shooting started
-                                   time-lapse shooting stopped

Required module installation:
sudo pip3 install python-crontab

"""

import argparse
import ast
import csv
import datetime
import os
import sys
from crontab import CronTab
from pathlib import Path

user="pi"
python3_dir="/usr/bin/python3"
install_dir="/opt/tools"
curdir=""
lockfile=".tlcron.lock"
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

minutes=[0,1,2,3,4,5,6,12,15,20,30]
hours=[0,1,2,3,4,6,8,12]

# Default parameters
params={
        "q"      : 90,
        "t"      : 1000,
        "ISO"    : 100,
        "ss"     : 20000,
        "awb"    : True,
        "ex"     : True,
        "bgain"  : 1.0,
        "rgain"  : 1.0,
        "ag"     : 1.0,
        "digits" : 4,
        "min"    : 1,
        "h"      : 0,
        }

"""
Image and time-lapse parameters

-ISO, --ISO	: Set capture ISO
-ex, --exposure	: Set exposure mode (see Notes)
-awb, --awb	: Set AWB mode (see Notes)
-ss, --shutter	: Set shutter speed in microseconds
-awbg, --awbgains	: Set AWB gains - AWB mode must be off
-ag, --analoggain	: Set the analog gain (floating point)
-d  : Time-lapse frame number digits
-min: time-lapse interval in minutes when h=0
-h  : time-lapse interval in hours when min=0

"""

def cronstr(interval):
    # interval unit: min
    h=interval // 60
    m=interval % 60
    # Templates:
    # start_min/min_interval start_h/h_interval * * * python3_dir install_dir/tlcron.py -c
    # */min_interval * * * * python3_dir install_dir/tlcron.py -c
    # * */h_interval * * * python3_dir install_dir/tlcron.py -c
    if m>0:
        time_s="*/"+str(m)+" "
    else:
        now=datetime.datetime.now()
        m=(now+datetime.timedelta(minutes=1)).minute
        time_s=str(m)+" "
    if h>0:
        time_s+="*/"+str(h)+" "
    else:
        time_s+="* "
    time_s+="* * *"
    command_s=python3_dir+" "
    command_s+=install_dir+"/tlcron.py -c"
    return time_s,command_s

def dtime():
    now=datetime.datetime.now()
    return now.strftime("%Y%m%d-%H%M%S")

parser=argparse.ArgumentParser()
parser.add_argument("-s", action="store_true", help="start time-lapse shooting")
parser.add_argument("-e", action="store_true", help="stop time-lapse shooting")
parser.add_argument("-c", action="store_true", help="capture time-lapse image")
args = parser.parse_args()

if args.s:
    startTL=True
if args.e:
    stopTL=True
if args.c:
    captureTL=True

if [startTL,stopTL,captureTL].count(True)>1:
    print("Only one argument is allowed!")
    sys.exit(1)

# Setup time-lapse
if not True in [startTL,stopTL,captureTL]:
    from rpi.camerainfo import *
    from rpi.inputs2 import *

    print("Crontab based time-lapse camera")

    # Get current directory
    curdir=os.getcwd()
    path=Path(curdir)
    lock_exists = os.path.isfile("/tmp/"+lockfile) 
    if lock_exists:
        print("")
        print("Time-lapse lock file exists!")
        print("Terminate time-lapse job with the following command:")
        print("tlcron.py -e")
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
    interval_min=inputListValue("minutes interval",minutes,1)
    params['min']=interval_min
    h_default=0
    hours_min=0
    interval_h=0
    if interval_min==0:
        hours_min=1
        h_default=1
        interval_h=inputListValue("hours interval",hours[hours_min:],h_default)
        params['h']=interval_h
    time_min=int(((10**digits-1)-2)*(interval_h*60+interval_min))
    time_max=int(((10**digits-1)-1)*(interval_h*60+interval_min))
    print("Time-lapse duration: "
          +str(time_min)+"-"+str(time_max)
          +" min")
    print("")

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
    
    # New crontab job
    timestr,cmd=cronstr(int(interval_min+interval_h*60))
    job = user_cron.new(cmd)
    job.setall(timestr)
    user_cron.write()
    
    # Create initial TLID
    tlid_file=open(project_dir+"/"+idfile,"w")
    tlid_file.write("0".zfill(digits))
    tlid_file.close()
    
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
        print("tlcron.py -s")

if startTL:
    # Get project directory
    file=open("/tmp/"+lockfile,"r")
    first_line=file.readline()
    file.close()
    if first_line.find("#")==0:
        first_line=first_line[1:]
        file=open("/tmp/"+lockfile,"w")
        file.write(first_line)
        file.close()
        firstFrame=True

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
    # Read file ID
    if not os.path.isfile(project_dir+"/"+idfile):
        print("TLID file not found!")
        sys.exit(1)
    try:
        file=open(project_dir+"/"+idfile,"r")
        frame=int(file.readline())
        file.close()
    except:
        print("Unable to open TLID file.")
        sys.exit(1)
    frame+=1
    if len(str(frame))<=digits:        
            
        # Create capture string
        # Template:
        # raspistill -fp -t 1000 -ISO 100 -q 90 -ss 200000 -ex off -awb off -ag 1 -awbg 1.5,2 -o file0001.jpg
        capture="raspistill "
        capture+="-fp "
        
        capture+="-t "+str(preview_time)+" "
        capture+="-ISO "+str(params["ISO"])+" "
        capture+="-q "+str(params["q"])+" "
        if params["ex"]:
            capture+="-ex auto "
        else:
            capture+="-ss "+str(params["ss"])+" "
            capture+="-ex off "
        if params["awb"]:
            capture+="-awb auto "
        else:
            capture+="-awb off "
            capture+="-awbg "+str(params["rgain"])+","+str(params["bgain"])+" "
        capture+="-ag "+str(params["ag"])+" "

        # picture save string
        picname=str(frame).zfill(digits)+".jpg"
        capture+="-o "+project_dir+"/"+picname
        # print(capture)
    
        # Capture picture and append data to txt-file
        os.system(capture)
        if not firstFrame:
            capfile=open(project_dir+"/"+txtfile,"a+")
        else:
            capfile=open(project_dir+"/"+txtfile,"w")
        if frame>1:
            int_min=int(params["min"])
            int_h=int(params["h"])
            capfile.write(str(frame)+delimiter+
                          str(int((int_min+int_h*60)*(frame-2)))+delimiter+
                          dtime()+delimiter+
                          picname+"\n")
        else:
            capfile.write(str(frame)+delimiter+
                          delimiter+
                          dtime()+delimiter+
                          picname+"\n")
        
        # Update TLID file
        file=open(project_dir+"/"+idfile,"w")
        file.write(str(frame).zfill(digits))
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
        file.write("\nTime-lapse capturing ended at "+str(datetime.datetime.now())+"\n")
        file.close()
    except:
        False
    
    # Clear crontab
    user_cron = CronTab(user=user)
    user_cron.remove_all()
    user_cron.write()
    
    # Remove lock and TLID files
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
