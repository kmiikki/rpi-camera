#!/usr/bin/python3
# Calibrate Raspberry Pi camera v. 2.x and HQ camera
# (c) Kim Miikki and Alp Karakoc 2021
# Version: 2.0

import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
import cv2
from rpi.inputs2 import *
from rpi.camerainfo import *
from rpi.roi import *

pip=(0,0,640,480)
pw=640
ph=480
ext=".jpg"

expss=0

# Uncomment to override gain ranges
#red_gain_min=1.00
#red_gain_max=1.15
#blue_gain_min=0.15
#blue_gain_max=0.20

# Uncomment to override gain ranges (8 MP: uvitec)
#red_gain_min=2.0
#red_gain_max=8.0
#blue_gain_min=0.5
#blue_gain_max=1.5

red_step=0.1
blue_step=0.1

roi_result=validate_roi_values()
if not roi_result:
    roi_x0=0.25
    roi_y0=0.25
    roi_w=0.5
    roi_h=0.5

# Uncomment for full field of view
#roi_x0=0
#roi_y0=0
#roi_w=1
#roi_h=1

color_max=255
r_avg=0
g_avg=0
b_avg=0
scale_type="linear"

exp_digits=6
default_calibration_name="calibration"
curdir=os.getcwd()

# Create a list of microsecond exposures
exposure=list()
filenames=list()
shootcommand=list()

exp_fast=[]
if camera_revision=="imx219":
  exp_fast = [
    50,
    100,
    250,
    500,
    750,
    1000
  ]
elif camera_revision=="imx477":
  exp_fast = [
    250,
    500,
    750,
    1000,
    1500,
    2000
  ]

exp_medium1 = [
    1000,
    2500,
    5000,
    7500,
    10000,
    15000
]

exp_medium2 = [
    10000,
    20000,
    30000,
    40000,
    50000,
    60000
]

exp_slow = [
    20000,
    35000,
    50000,
    100000,
    200000,
    300000
]

exp_wide=[]
if camera_revision=="imx219":
  exp_wide = [
    50,
    100,
    200,
    500,
    1000,
    2000,
    5000,
    10000,
    20000,
    50000,
    100000,
    200000
  ]
elif camera_revision=="imx477":
  exp_wide = [
    250,
    500,
    750,
    1000,
    2000,
    5000,
    10000,
    20000,
    25000,
    50000,
    100000,
    200000
  ]

exp_full=[]
if camera_revision=="imx219":    
  exp_full = [
    1,
    5,
    10,
    25,
    50,
    100,
    200,
    350,
    500,
    750,
    1000,
    2000,
    3500,
    5000,
    7500,
    10000,
    15000,
    20000,
    35000,
    50000,
    100000,
    150000,
    200000,
    250000,
    300000,
    330000
  ]
elif camera_revision=="imx477":
  exp_full = [
    250,
    350,
    500,
    750,
    1000,
    2000,
    3500,
    5000,
    7500,
    10000,
    15000,
    20000,
    35000,
    50000,
    100000,
    150000,
    200000,
    250000,
    300000,
    350000,
    500000
  ]

exp_auto=[]
exposures=0
min_y=0
max_y=255

def get_exp_awbg(file_name):
    global exp_digits
    s=os.path.splitext(file_name)[0]
    s=s[-exp_digits:]
    ss=int(s)
    # Remove last underscore, when ext length is 4
    file_name=file_name[:-(1+exp_digits+4)]
    #search last comma
    comma_pos=file_name.rfind(",")
    b_gain=float(file_name[comma_pos+1:len(file_name)])
    # remove comma and blue gain
    file_name=file_name[:-(len(file_name)-comma_pos)]
    # Get last underscore position
    underscore_pos=file_name.rfind("_")
    # Get red gain
    r_gain=float(file_name[underscore_pos+1:len(file_name)])
    return ss,r_gain,b_gain

# Optimum gains functions

def partition(lst, n):
  division = len(lst) / n
  return [lst[round(division * i):round(division * (i + 1))] for i in range(n)]

def distanceextract(lst): 
    return [item[3] for item in lst]

def distancesort(sub_li): 
  
    # reverse = None (Sorts in Ascending order) 
    # key is set to sort using second element of  
    # sublist lambda has been used 
    return(sorted(sub_li, key = lambda x: x[2]))  

print("Calibrate Raspberry Pi camera module ("+camera_revision+")")
print("(c) Kim Miikki and Alp Karakoc 2020\n")
quality_default=90
artist=""
artistfile="artist.txt"

np.set_printoptions(suppress=True)

if roi_result:
    print("ROI file found: "+str(roi_x0)+","+str(roi_y0)+","+str(roi_w)+","+str(roi_h))
    print("")

print("Current directory:")
curdir=os.getcwd()
print(curdir)
path=input('\nPath to images (current directory: <Enter>): ')
name=input('Calibration name (Default: '+default_calibration_name+'): ')
if name=="":
    name=default_calibration_name
    print("Default calibration name assigned: "+name)

if camera_detected==1:
    analyzeOnly=inputYesNo("Analyze only mode","Calibration from existing files",False)
else:
    print("Raspberry Pi camera module not found!")  
    analyzeOnly=inputYesNo("Analyze only mode","Calibration from existing files",True)
    if not analyzeOnly:
        print("Calibration of existing files is only allowed, without a camera module. Program is terminated.")
        exit(0)
if not analyzeOnly:
    from picamera import PiCamera
    quality=inputValue("quality",1,100,quality_default,"","Quality is out of range!",True)
else:
    quality=quality_default

iso=100
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
if not analyzeOnly:
    iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!")
    w=camera_maxx
    h=camera_maxy
    camera=PiCamera(resolution=(w,h))
    camera.iso=int(iso)
    # You can query the exposure_speed attribute to determine the actual
    # shutter speed being used when this attribute is set to 0
    camera.exposure_mode='auto'
    camera.shutter_speed=0
    print("\nCalculating auto exposure range for calibration:")
    # Wait for the automatic gain control to settle
    time.sleep(2)
    expss=int(camera.exposure_speed)
    camera.close()
    l=len(str(expss))
    print("Auto shutter speed: "+str(round(expss/1000)).rjust(l)+" ms")
    print("Auto shutter speed: "+str(expss)+" µs")
    r=0.25
    minss=5
    maxss=330000
    minexp=int(minss/(1+r*3))
    maxexp=int(maxss/(1+r*3))
    if expss>=minss and expss<=maxexp:
        exp_auto.append(int(expss*(1-r*3)))
        exp_auto.append(int(expss*(1-r*2)))
        exp_auto.append(int(expss*(1-r)))
        exp_auto.append(expss)
        exp_auto.append(int(expss*(1+r)))
        exp_auto.append(int(expss*(1+r*2)))
        exp_auto.append(int(expss*(1+r*3)))
    print("Auto shutter speed range for calibration (µs):")
    print(exp_auto)
    print("")

# Selection of the calibration mode
if not analyzeOnly:
    md=[]
    md.append(["1",len(exp_fast),exp_fast[0],exp_fast[len(exp_fast)-1]])
    md.append(["2",len(exp_medium1),exp_medium1[0],exp_medium1[len(exp_medium1)-1]])
    md.append(["3",len(exp_medium2),exp_medium2[0],exp_medium2[len(exp_medium2)-1]])
    md.append(["4",len(exp_slow),exp_slow[0],exp_slow[len(exp_slow)-1]])
    md.append(["5",len(exp_wide),exp_wide[0],exp_wide[len(exp_wide)-1]])
    md.append(["6",len(exp_full),exp_full[0],exp_full[len(exp_full)-1]])
    if (len(exp_auto)>0):
        md.append(["7",len(exp_auto),exp_auto[0],exp_auto[len(exp_auto)-1]])
    modes=len(md)
    while True:
        try:
            print("\nCalibration modes")
            print("Md  Pictures  EXP min  EXP max")
            for mode,pics,exp_min,exp_max in md:
                print(mode+str(pics).rjust(11," ")+str(exp_min).rjust(9," ")+str(exp_max).rjust(9," ")+" µs")
            tmp=input("Select exposure range mode (1..."+str(modes)+"): ")        
            mode=int(tmp)
        except ValueError:
            print("Not a valid number!")
            continue
        else:
            if ((mode<1)or(mode>modes)):
                print("Invalid mode!\n")
                continue
            break
    if mode==1:
        exposure=exp_fast
    if mode==2:
        exposure=exp_medium1
    if mode==3:
        exposure=exp_medium2
    if mode==4:
        exposure=exp_slow
    if mode==5:
        exposure=exp_wide
    if mode==6:
        exposure=exp_full
    if mode==7:
        exposure=exp_auto
    exposures=md[mode-1][1]
    min_x=exposure[0]
    max_x=exposure[len(exposure)-1]

if not analyzeOnly:
    print("\nDefault calibration ranges:")
    print("Red gain range:  "+str(red_gain_min)+"-"+str(red_gain_max))
    print("Red gain step:   "+str(red_step))
    print("Blue gain range: "+str(blue_gain_min)+"-"+str(blue_gain_max))
    print("Blue gain step:  "+str(blue_step))
    print("")
    defaultRanges=inputYesNo("Current ranges","Accept default ranges",True)
    print("")

    if not defaultRanges:

        # Red gain range and step
        red_gain_min=inputValue("red gain min",red_gain_min,red_gain_max,red_gain_min,"","Gain out of range!",False)
        if red_gain_max<red_gain_min:
            red_gain_max=red_gain_min
        red_gain_max=inputValue("red gain max",red_gain_min,red_gain_max,red_gain_max,"","Gain out of range!",False)
        red_max_step=round(red_gain_max-red_gain_min,3)
        if red_max_step<red_step:
            red_step=red_max_step
        if red_max_step==0.0:
            print("Red gain min and max are equal. Red step auto adjusted to 1.0.")
            red_step=1.0
        else:
            red_step=inputValue("red gain step",0.001,red_max_step,red_step,"","Step out of range!",False)
        print("")

        # Blue gain range and step
        blue_gain_min=inputValue("blue gain min",blue_gain_min,blue_gain_max,blue_gain_min,"","Gain out of range!",False)
        if blue_gain_max<blue_gain_min:
            blue_gain_max=blue_gain_min
        blue_gain_max=inputValue("blue gain max",blue_gain_min,blue_gain_max,blue_gain_max,"","Gain out of range!",False)
        blue_max_step=round(blue_gain_max-blue_gain_min,3)
        if blue_max_step<blue_step:
            blue_step=blue_max_step
        if blue_max_step==0.0:
            print("Blue gain min and max are equal. Blue step auto adjusted to 1.0.")
            blue_step=1.0
        else:
            blue_step=inputValue("blue gain step",0.001,blue_max_step,blue_step,"","Step out of range!",False)
        print("")

    red_decimals=str(red_step)[::-1].find(".")
    red_min_decimals=str(red_gain_min)[::-1].find(".")
    if red_min_decimals>red_decimals:
        red_decimals=red_min_decimals
    red_format="{:"+"."+str(red_decimals)+"f}"

    blue_decimals=str(blue_step)[::-1].find(".")
    blue_min_decimals=str(blue_gain_min)[::-1].find(".")
    if blue_min_decimals>blue_decimals:
        blue_decimals=blue_min_decimals
    blue_format="{:"+"."+str(blue_decimals)+"f}"
    
scale_type=inputListValue("scale type",["linear","log"],"linear","Not a valid scale type!",True)
if not analyzeOnly:
    previewImage=inputYesNo("Preview","Preview image",True)

    try:
        f=open(artistfile,"r")
        artist=f.readline()
        artist=artist.strip()
        print("")
        print("Artist: "+artist)
        f.close()
    except IOError:
        artist=""

# Create a log file
logname=""
if (path!=""):
    logname=path+"/"
if not analyzeOnly:
    logname+=name+"_iso"+str(iso)+".log"
else:
    logname+=name+"_analyze_mode.log"
now = datetime.now()

# Start time
t1=now

dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")

file=open(logname,"w")
file.write("Log created on "+dt_string+"\n\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")
file.write("Calibration name: "+name+"\n\n")

if not analyzeOnly:
    file.write("Calibration parameters:\n")
    if camera_detected==1:
        file.write("Resolution: "+str(camera_maxx)+"x"+str(camera_maxy)+"\n")
        file.write("Sensor: "+camera_revision+"\n")
    file.write("Red gain:   "+str(red_gain_min)+"-"+str(red_gain_max)+"\n")
    file.write("Blue gain:  "+str(blue_gain_min)+"-"+str(blue_gain_max)+"\n")
    file.write("Red gain step:  "+str(red_step)+"\n")
    file.write("Blue gain step: "+str(blue_step)+"\n")
    file.write("Quality: "+str(quality)+"\n")
    file.write("ISO value: "+str(iso)+"\n")
    file.write("ROI x0: "+str(roi_x0)+"\n")
    file.write("ROI y0: "+str(roi_y0)+"\n")
    file.write("ROI w : "+str(roi_w)+"\n")
    file.write("ROI h : "+str(roi_h)+"\n")
    file.write("Exposure mode  : "+str(mode)+"\n")
    file.write("Exposures (µs) : "+str(exposure)+"\n")
    file.write("Pictures/series: "+str(exposures)+"\n")
    file.write("Exposure range : "+str(exposure[0])+"-"+str(exposure[len(exposure)-1])+" µs"+"\n")

file.write("Scale type: "+scale_type+"\n")
file.write("Analyze only mode: ")
if analyzeOnly:
    file.write("Enabled")
else:
    file.write("Disabled")
file.write("\n")

i=0
r=red_gain_min
subdirs=[]
subdirs_count=0

# Capture pictures
if not analyzeOnly:
    reds=int((red_gain_max-red_gain_min+red_step)/red_step)
    blues=int((blue_gain_max-blue_gain_min+blue_step)/blue_step)
    combinations=reds*blues
    pictures=combinations*len(exposure)
    digits=len(str(pictures))
    
    # Create ared gains array
    i=0
    red_gains=[]
    while i<reds:
        red_gains.append(round(red_gain_min+i*red_step,10))
        i+=1
        
    # Create a blue gains array
    i=0
    blue_gains=[]
    while i<blues:
        blue_gains.append(round(blue_gain_min+i*blue_step,10))
        i+=1

    camera=PiCamera(resolution=(pw,ph))
    camera.iso=iso
    camera.framerate=1
    camera.exposure_mode="off"
    camera.awb_mode="off"
    zoom=(roi_x0,roi_y0,roi_w,roi_h)
    camera.zoom=zoom
    
    if previewImage:
        camera.start_preview(fullscreen=False,window=pip)
        sleep(2)
    i=0
    rindex=0
    bindex=0
    expindex=0
    r=red_gains[rindex]
    b=blue_gains[bindex]
    e=exposure[expindex]
    camera.shutter_speed=e
    camera.awb_gains=(r,b)
    sleep(2)
    newCombination=True
    if artist!="":
        camera.exif_tags["IFD0.Artist"]=artist
        camera.exif_tags["IFD0.Copyright"]=artist
    print("")
    print("Capturing calibration images:")
    for filename in camera.capture_continuous("temp{counter:0"+str(digits)+"d}"+ext,quality=quality):        
        i+=1
        if i>pictures:
            if os.path.isfile(filename):
                os.remove(filename)
            break

        # Build the subdirectory string
        r_tmp=round(r,10)
        b_tmp=round(b,10)
        r_str=red_format.format(r_tmp)
        b_str=blue_format.format(b_tmp)
        subdir=name+"_"+r_str+","+b_str
        if (path!=""):
            subdir=path+"/"+subdir
        if newCombination:
            subdirs.append(subdir)
            subdirs_count+=1
        if not os.path.exists(subdir):
            os.mkdir(subdir)
            newCombination=False
        else:
            if newCombination:
                shutil.rmtree(subdir)
                os.mkdir(subdir)
                newCombination=False
            
        # Build the picture name string
        timestr=str(exposure[expindex])
        timestr=timestr.rjust(6,'0')
        fname=name+"_iso"+str(iso)+"_"+r_str+","+b_str+"_"+timestr+".jpg"

        shutil.move(filename,subdir+"/"+fname)
        print(fname)
        
        expindex+=1
        if expindex>=exposures:
            expindex=0        
            bindex+=1
            newCombination=True
            if bindex>=blues:
                bindex=0
                rindex+=1
            if rindex>=reds:
                break

        r=red_gains[rindex]
        b=blue_gains[bindex]
        e=exposure[expindex]
            
        camera.shutter_speed=e
        camera.awb_gains=(r,b)
    camera.close()

else:
    # List calibration directories
    dirpath=""
    if not path=="":
        dirpath=path
    for p in sorted(Path(dirpath).iterdir()):
        if p.is_dir():
            tmp=str(p.name)
            # Check is directory name equals calibration name+"_"
            if not tmp.find(name+"_")==0:
                continue
            # Search for gains in directory name; format: rgain,bgain
            tmp=tmp[len(name)+1:]
            gainlist=tmp.split(",")
            # Only 2 gains list is allowed
            if not len(gainlist)==2:
                continue
            # Test if both gains are numbers
            rgain=-1
            bgain=-1
            try:
                rgain=float(gainlist[0])
            except ValueError:
                continue
            try:
                bgain=float(gainlist[1])
            except ValueError:
                continue
            if rgain<=0 or bgain<=0:
                continue
            subdir=str(p.name)
            if (path!=""):
                subdir=path+"/"+subdir
            subdirs.append(subdir)
            subdirs_count+=1

# Create figures subdirectory and analyze RGB channels
results=[]
figures_dir=name+"_figures"
if not path=="":
    figures_dir=path+"/"+figures_dir
if not os.path.exists(figures_dir):
    os.mkdir(figures_dir)

for d in subdirs:
    red=[]
    green=[]
    blue=[]
    dirpath=d
    if analyzeOnly:
        min_x=-1
        max_x=-1
        exposure=list()
    print("Analyzing: "+dirpath)
    for p in sorted(Path(dirpath).iterdir()):
        suffix=p.suffix.lower()
        if p.is_file() and (suffix==".png" or suffix==".jpg"):
            fname=p.name
            img=cv2.imread(dirpath+"/"+fname)
            h,w,ch=img.shape
            if ch==1:
                print(fname+" has only 1 channel. Skipping file.")
                continue
            rgb_means=np.array(img).mean(axis=(0,1))
            r_avg=rgb_means[2]
            g_avg=rgb_means[1]
            b_avg=rgb_means[0]
            rgb_avg=(r_avg+g_avg+b_avg)/3
            rgb_ratio=rgb_avg/255
            r_ratio=r_avg/255
            g_ratio=g_avg/255
            b_ratio=b_avg/255
            red.append(r_avg)
            green.append(g_avg)
            blue.append(b_avg)
            ss,red_gain,blue_gain=get_exp_awbg(fname)
            if analyzeOnly:
                if (min_x==-1) and (max_x==-1):
                    min_x=ss
                    max_x=ss
                if ss<min_x:
                    min_x=ss
                if ss>max_x:
                    max_x=ss
                exposure.append(ss)
            results.append([fname,ss,red_gain,blue_gain,rgb_avg,r_avg,g_avg,b_avg,rgb_ratio,r_ratio,g_ratio,b_ratio])
    fig=plt.figure()
    fig.canvas.set_window_title(d)
    plt.xlabel("Exposure (µs)")
    plt.ylabel("RGB average values")
    plt.xlim(min_x,max_x)
    plt.ylim(min_y,max_y)
    plt.xscale(scale_type)
    red_curve,=plt.plot(exposure,red,color="#ff0000")
    green_curve,=plt.plot(exposure,green,color="#00ff00")
    blue_curve,=plt.plot(exposure,blue,color="#0000ff")
    file_name=os.path.basename(d)+".png"
    plt.savefig(figures_dir+"/"+file_name)
    plt.close("all")

# Save results in a text file
outname="rgb-"+name+"_iso"+str(iso)+".txt"
if not path=="":
    outname=path+"/"+outname
rgbfile=open(outname,"w")
rgbfile.write("picture_name;exp_time;r_gain;b_gain;rgb_avg;r_avg;g_avg;b_avg;rgb_ratio;r_ratio;g_ratio;b_ratio\n")
for value in results:
  s=""
  for i in range(0,12):
    s+=str(value[i])
    if i<11:
      s+=";"
  rgbfile.write(s+"\n")
rgbfile.close()

# Calculate optimum gains
fileRead = open(outname, "r") 
sampling = 6

lines = fileRead.readlines()
fileRead.close()
count = len(lines)
# listorder = ["exp_time2", "r_gain3", "b_gain4", "r_avg6", "g_avg7", "b_avg8"]
dfs = list()
disposed=0
for x in range(1,count):
  defsets = lines[x].split(";")
  defset = [float(defsets[1]), float(defsets[2]), float(defsets[3]), \
              float(defsets[5]), float(defsets[6]), float(defsets[7])]
#    indices = [1,2,3,5,6,7]
#   defset = np.take(defsets,indices)
#     defset = [float(defset[i]) for i in len(indices)]
    
    # Dispose under- and overexposed images
    # R, G, B thresholds: minimum 1.0 and maximum 254.0
  if (defset[3]<0.5 or defset[3]>254.5) and \
    (defset[4]<0.5 or defset[4]>254.5) and \
    (defset[5]<0.5 or defset[5]>254.5):
    disposed+=1
  else:
    distance = abs(defset[3]-defset[4]) + abs(defset[4]-defset[5]) \
              + abs(defset[5]-defset[3])
    defsetdistance = [defset[0],defset[1],defset[2],distance]
    dfs.append(defsetdistance)

count=len(dfs)
if disposed>0:
  print("Under- or overexposed images (which are not included in calibration): "+str(disposed))
  print("Valid images for calibration: "+str(count))
  file.write("Under- or overexposed images (which are not included in calibration): "+str(disposed)+"\n")
  file.write("Valid images for calibration: "+str(count)+"\n")
else:
  print("Calibration images: "+str(count))
  file.write("Calibration images: "+str(count)+"\n")

if count>0:
  #count = int(count/sampling)
  #defsetdistsample =  partition(dfs,count)
  
  exposuretime=int(lines[1].split(";")[1])

  dfsflatten = list()

  for i in range(len(dfs)): #Traversing through the main list
    for j in range (len(dfs[i])): #Traversing through each sublist
      dfsflatten.append(dfs[i][j]) #Appending elements into our flat_list
    
  #Sampling is the number of exposures used for each r_ and b_gains
  samplinglists = dfsflatten.count(exposuretime)
  #print("Sampling = ", samplinglists)
  #sampling = int((count-1) / samplinglists)

  #Partitioning of the total list into exposure sampling sets
  #count = int((count-1)/sampling)
  defsetdistsample =  partition(dfs,samplinglists)  

  dft = list()
  for x in range(0,samplinglists):
    dists = distanceextract(defsetdistsample[x])
    totaldist = sum(dists)
    defsettotaldist = [defsetdistsample[x][0][1],defsetdistsample[x][0][2], \
                       totaldist]
    dft.append(defsettotaldist)
  optimal = distancesort(dft)[0]
  print("")
  print("Optimal r_gain = ", optimal[0])
  print("Optimal b_gain = ", optimal[1])
  print("Total distance = ", optimal[2])
  file.write("Optimal r_gain: "+str(optimal[0])+"\n")
  file.write("Optimal b_gain: "+str(optimal[1])+"\n")
  file.write("Total distance: "+str(optimal[2])+"\n")
else:
  print("No valid calibration images!\nUnable to calculate optimal calibration values.")
  file.write("No valid calibration images!\nUnable to calculate optimal calibration values.\n")

t2=datetime.now()
print("Time elapsed: "+str(t2-t1))
file.write("Time elapsed: "+str(t2-t1)+"\n")
file.close()
