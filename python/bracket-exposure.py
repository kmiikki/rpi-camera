#!/usr/bin/python3
# Exposure bracketing program for Raspberry Pi camera v. 2.x (c) Kim Miikki 2019
import os
from datetime import datetime
from rpi.inputs import *
from rpi.camerainfo import *
from rpi.roi import *

print("Exposure bracketing program for Raspberry Pi camera (c) Kim Miikki 2020\n")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)

print("Current directory:")
os.system("pwd")
print("")

roi_result=validate_roi_values()
if roi_result:
    display_roi_status()
    print("")

quality_default=90
artist=""
artistfile="artist.txt"

quality_default=90
quality=inputValue("image quality",1,100,quality_default,"","Quality is out of range!",True)

path=input('Path to images (current directory: <Enter>): ')
name=input('Exposure bracketing name (default=exp: <Enter>): ')
if name=="":
    name="exp"

iso=100
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")

try:
    f=open(artistfile,"r")
    artist=f.readline()
    artist=artist.strip()
    print("Artist: "+artist)
    f.close()
except IOError:
    artist=""

if len(path)>0:
    roi_file_exists=read_roi_file(roi_filename,path)
    
if roi_file_exists:
    roi_string=roi_dict["roi_x0"]+","
    roi_string+=roi_dict["roi_y0"]+","
    roi_string+=roi_dict["roi_w"]+","
    roi_string+=roi_dict["roi_h"]

# Create a log file
logname=""
if (path!=""):
    logname=path+"/"
logname+=name+"_iso"+str(iso)+".log"

now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")

file=open(logname,"w")
file.write("Log created on "+dt_string+"\n\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")
file.write("Exposure bracketing parameters:\n")
file.write("Resolution: "+str(camera_maxx)+"x"+str(camera_maxy)+"\n")
file.write("ROI: ")
if roi_file_exists:
    file.write(roi_string+"\n")
else:
    file.write("FOV")
file.write("\n")
file.write("Sensor: "+camera_revision+"\n")
file.write("Quality: "+str(quality)+"\n")
file.write("ISO value: "+str(iso)+"\n\n")
file.write("Shoot commands:\n\n")

# Create a list of microsecond exposures
exposure=list()
filenames=list()
shootcommand=list()
digits=0
if camera_revision=="imx219":
    digits=6
    exposure = [
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
    digits=7
    exposure = [
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
        500000,
        750000,
        1000000
    ]
# Genereate file names and shoot commands
# Template:
#
# raspistill -n -t 1 -ISO 100 -q 10 -ss 20000 -bm -drc high
# -x IFD0.Artist="" -x IFD0.Copyright=""
# -o test123.jpg

i=0
for time in exposure:
    timestr=str(exposure[i])
    timestr=timestr.rjust(digits,'0')

    fname=name+"_iso"+str(iso)+"_"+timestr+".jpg"
    filenames.append(fname)

    tmp="raspistill -n -t 1 -ISO "+str(iso)+" "
    tmp+="-q "
    tmp+=str(quality)+" "
    tmp+="-ss "+timestr+" "
    tmp+="-bm -drc high "
    if roi_file_exists:
        tmp+="-roi "+roi_string+" "
    if artist!="":
        tmp+='-x IFD0.Artist="'+artist+'" '
        tmp+='-x IFD0.Copyright="'+artist+'" '
    if (path!=""):
        tmp+='-o '+path+'/'+fname
    else:
        tmp+='-o '+fname
    shootcommand.append(tmp)
    i=i+1

i=0
for picture in shootcommand:
    print(picture)
    os.system(picture)
    file.write(picture+"\n")
    i=i+1

file.close()
