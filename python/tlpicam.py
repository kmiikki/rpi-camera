#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 11:14:15 2021
Relay feature added: 17.2.2023

@author: Kim Miikki
"""
import os
from datetime import datetime,timedelta
from pathlib import Path
from time import sleep, perf_counter
from picamera import PiCamera
from rpi.inputs2 import *
from rpi.camerainfo import *
import RPi.GPIO as GPIO

# Relay options
channel=26
shutdown_threshold=300 # default 5 min = 300 s
fast_turn_on=1 # seconds
relay_time=30  # relay is 30 s on

pip=(0,0,640,480)
dropfile="__drop.jpg"
logfile="tlpicam.log"
ext=".jpg"

isRelay=False

def relay_on():
    GPIO.output(channel,True)

def relay_off():
    GPIO.output(channel,False)


def swap(a,b):
    return b,a

def time_and_unit(minimum,maximum):
    if minimum>maximum:
        minimum,maximum=swap(minimum,maximum)
    unit="s"
    divisor=1
    q=minimum // 60
    if q>=1:
        unit="min"
        divisor*=60
    q=minimum // (60*60)
    if q>=1:
        unit="h"
        divisor*=60
    q=minimum // (60*60*24)
    if q>=1:
        unit="d"
        divisor*=24
    q=minimum // (60*60*24*365.2425)
    if q>=1:
        unit="a"
        divisor*=365.2425
    t1=minimum/divisor
    t2=maximum/divisor
    if float(t1).is_integer() and float(t2).is_integer():
        t1=int(t1)
        t2=int(t2)
    else:
        t1=round(t1,1)
        t2=round(t2,1)
    return t1,t2,unit


def get_sec_fractions(resolution=5) -> float:
    t = datetime.now()
    return round(t.timestamp() % 1, resolution)

print("PiCamera based time-lapse program ver. 1.1")
print("")

time_and_unit(60,60)

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
print("Current directory:")
print(curdir)
print("")

# Time-lapse capture values section start
#
# Default values and ranges
exposure=1
minutes_min=1
minutes_max=525950
minutes_on=True
s_min=2
s_max=int(60*minutes_max)
red_gain_min=0.1
red_gain_max=10.0
blue_gain_min=0.1
blue_gain_max=10.0
awbg_red_default=awbg_red
awbg_blue_default=awbg_blue

quality_default=90
quality=inputValue("image quality",1,100,quality_default,"","Quality is out of range!",True)

iso=1
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")

autoexp_on=True
autoexp_default=True
autoexp_on=inputYesNo("EXP auto","Auto exposure on",autoexp_default)
print("")

# Exposure unit: µs
if not autoexp_on:
    exp_min=1
    exp_max=1000000
    exp_default=20000
    exposure=inputValue("exposure time",exp_min,exp_max,exp_default,"µs","Exposure is out of range!",True)

# Gain value: 1.0 to 12.0 for the IMX219 sensor on Camera Module V2
awb_on=True
default_awb=True
awb_on=inputYesNo("AWB","AWB mode on",default_awb)
if not awb_on:
    print("")
    awbg_red=inputValue("red gain",0.001,8.0,awbg_red_default,"","Value out of range!",False)
    awbg_blue=inputValue("blue gain",0.001,8.0,awbg_blue_default,"","Value out of range!",False)

print("")
jpg_mode=inputYesNo("jpg mode","Image format JPG",True)
print("")
if jpg_mode:
    ext=".jpg"
else:
    ext=".png"

# Digits
digits_default=4
min_digits=1
max_digits=8
if min_digits>digits_default:
  digits_default=min_digits
digits=inputValue("digits",min_digits,max_digits,digits_default,"","Digits is out of range!",True)
max_count=int(10**digits-1)

# Intervals
# PNG capture speed is slow => Enable only JPG capturing in s mode
if jpg_mode:
    minutes_default=True
    minutes_on=inputYesNo("Interval in minutes mode","Select minute mode",minutes_default)
else:
    minutes_on=True
if minutes_on:
    interval_min=inputValue("interval",minutes_min,minutes_max,minutes_min,"min","Interval is out of range!",True)
    interval_s=interval_min*60
else:
    interval_s=inputValue("interval",s_min,s_max,s_min,"s","Interval is out of range!",True)
    interval_min=interval_s/60
t_mins=((10**digits-1)-2)*interval_s
t_maxs=((10**digits-1)-1)*interval_s
t_min,t_max,u=time_and_unit(t_mins,t_maxs)
t_str=str(t_max)+" "+u
print("Time-lapse maximum duration: "+t_str)
print("")

previewImage=inputYesNo("Preview","Preview image",False)
isRelay=inputYesNo("Relay","Enable relay",False)
if isRelay:
    # Use GPIO numbers not pin numbers
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channel, GPIO.OUT)
    relay_on()
    
startTL=inputYesNo("Time-lapse","Start time-lapse now",True)

if startTL:
    # Get camera resolution
    camera=PiCamera()
    resX,resY=camera.MAX_RESOLUTION
    camera.close()
    
    camera=PiCamera(resolution=(resX,resY))
    camera.iso=iso
    camera.framerate=1
    if autoexp_on:
        camera.exposure_mode="auto"
    else:
        camera.exposure_mode="off"
        camera.shutter_speed=exposure
    sleep(2)
    if awb_on:
        camera.awb_mode="auto"
        g=camera.awb_gains
        """
        Red gain:  2.11 539/256
        Blue gain: 2.66 681/256
        """
        camera.awb_gains=g
    else:
        camera.awb_mode="off"
        camera.awb_gains=(awbg_red,awbg_blue)
    if previewImage:
        camera.start_preview(fullscreen=False,window=pip)
        sleep(2)
    
    t1=datetime.now()
    t2=datetime.now()
    i=0
    print("")
    print("Press CTRL+C to exit time-lapse shooting.")
    print("")

    # Discard the first image to stabilize the capture stream
    print("Stabilizing the camera")
    camera.capture(dropfile)
    os.remove(dropfile)
    sleep(5)    

    # Create a log file
    file=open(logfile,"w")
    file.write("tlpicam\n\n")
    file.write("Options\n")
    file.write("-------\n")
    file.write("Current directory: "+curdir+"\n")
    file.write("Quality : "+str(quality)+"\n")
    file.write("ISO     : "+str(iso)+"\n")
    file.write("EXP mode: ")
    if autoexp_on:
        file.write("auto\n")
    else:
        file.write("off\n")
        file.write("Shutter speed: "+str(exposure)+" µs"+"\n")
    file.write("AWB mode: ")
    if autoexp_on:
        file.write("auto\n")
    else:
        file.write("off\n")
        file.write("Red gain : "+str(awbg_red)+"\n")
        file.write("Blue gain: "+str(awbg_blue)+"\n")
    file.write("Digits  : "+str(digits)+"\n")
    if minutes_on:
        interval=interval_min
        unit="min"
    else:
        interval=interval_s
        unit="s"
    file.write("Mode    : "+unit+"\n")
    file.write("Interval: "+str(interval)+" "+unit+"\n")
    file.write("Time-lapse maximum duration: "+t_str+"\n")
    file.write("Extension: "+ext+"\n")
    file.close()
    
    lags=[]
    print("Time synchronization.")
    # Wait until a new second starts
    while get_sec_fractions() != 0:
        pass
    
    tp0 = perf_counter()
    tl_start=datetime.now()
    print("\nCapturing time-lapse images:")
    
    try:
        for filename in camera.capture_continuous("{counter:0"+str(digits)+"d}"+ext,quality=quality):
            i+=1
            tp1 = perf_counter()
            t1=datetime.now()
            capture_time = (tp1-(tp0 + interval_min * (i - 1) * 60))
            delay = float(interval_min * 60 - capture_time)
            print(str(i).zfill(digits)+"/"+str(max_count),end="")
            if delay<0:
                print(": frame delayed "+format(round(abs(delay),3),".3f")+" s")
                lags.append([i,round(abs(delay),3)])
            else:
                print()
            
            if i>=max_count:
                break
            
            if (not isRelay) or (interval_s<shutdown_threshold):
                if delay>0:
                    sleep(delay)
                continue
            
            # Relay section
            off_time=delay-relay_time
            on_time=relay_time

            if off_time>0:
                relay_off()
                sleep(off_time)
            else:
                on_time+=off_time
            
            relay_on()
            if on_time<fast_turn_on:
                sleep(1)
            else:
                sleep(on_time)
            
    except KeyboardInterrupt: # Press Ctrl+C to interrupt
        print("\nTime-lapse shooting exited.")
    else:
        print("\nTime-lapse shooting finished.")
    finally:
        tl_end=datetime.now()
        print("Time-lapse started : "+str(tl_start))
        print("Time-lapse ended   : "+str(tl_end))
        print("Time-lapse duration: "+str(tl_end-tl_start)+"\n")
        print("Frames captured: "+str(i))
        if len(lags)>0:
            print("Frames delayed : "+str(len(lags))+"\n")
            print("Delayed frames:")
            for s in lags:
                print(str(s[0]).zfill(digits)+": "+format(round(abs(s[1]),3),".3f")+" s")
        file=open(logfile,"a+")
        file.write("\n")
        file.write("----\n\n")
        file.write("Time-lapse started : "+str(tl_start)+"\n")
        file.write("Time-lapse ended   : "+str(tl_end)+"\n")
        file.write("Time-lapse duration: "+str(tl_end-tl_start)+"\n")
        file.write("\n")
        file.write("Frames captured: "+str(i)+"\n")
        if len(lags)>0:
            file.write("Frames delayed : "+str(len(lags))+"\n\n")
            file.write("Delayed frames:\n")
            for s in lags:
                file.write(str(s[0]).zfill(digits)+": "+format(round(abs(s[1]),3),".3f")+" s\n")
        file.close()
    camera.close()
else:
    print("Time-lapse canceled.")

if isRelay:
    relay_off()