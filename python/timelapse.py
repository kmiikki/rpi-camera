#!/usr/bin/python3
# Time-lapse program for Raspberry Pi camera v. 2.x (c) Kim Miikki 2019
import os
from datetime import datetime
from rpi.inputs import *
from rpi.camerainfo import *

# Calibration gains for Manfrotto Lumie LEDs
awbg_red=1.6
awbg_blue=1.4

print("Time-lapse program for Raspberry Pi camera module (c) Kim Miikki 2020\n")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)

print("List disk and partitions:")
os.system('lsblk')
print("\nCurrent directory:")
os.system("pwd")
path=input('\nPath to images (current directory: <Enter>): ')
name=input('Time-lapse project name: ')
if name=="":
    name="pic"
print("")
quality_default=90
quality=inputValue("image quality",1,100,quality_default,"","Value out of range!",True)

iso=100
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")

# Define shoot command and time variables
shootcommand=""
exposure=1
interval=1
duration=1
start_frame=1

artist=""
artistfile="artist.txt"

# Exposure unit: µs
exposure=inputValue("exposure time",1,330000,20000,"µs","Exposure is out of range!",True)

# Interval unit: ms
interval=inputValue("interval",1,86400,1,"s","Interval out of range!",True)

# Time-lapse maximum duration 1 y = 31536000000 ms
# Duration unit: ms
max_duration=31536000
duration=inputValue("time-lapse duration",1,max_duration,30,"s","Duration is out of range!",True)

# Gain value: 1.0 to 12.0 for the IMX219 sensor on Camera Module V2
print("")
awb_on="n"
default_awb="y"
awb_on=inputYesNo("AWB","AWB mode on",default_awb)
if awb_on=="n":
    print("")
    awbg_red=inputValue("red gain",1.0,12.0,awbg_red,"","Value out of range!",False)
    awbg_blue=inputValue("blue gain",1.0,12.0,awbg_blue,"","Value out of range!",False)

# Sets the analog gain value directly on the sensor
# (1.0 to 12.0 for the IMX219 sensor on Camera Module V2).
analog_gain=0
analog_gain_default=1.0
print("")
analog_gain=inputValue("analog gain",0.0,12.0,analog_gain_default,"","Analog gain is out of range!",False)

#print(awbg_red,awbg_blue,analog_gain)

# Turn awb off if more than 120 fps
additional_params="-ag "+str(analog_gain)
if awb_on=="n":
    additional_params+=" -awb off "
    additional_params+="-awbg "+str(awbg_red)+","+str(awbg_blue)

try:
    f=open(artistfile,"r")
    artist=f.readline()
    artist=artist.strip()
    print("\nArtist: "+artist)
    f.close()
except IOError:
    artist=""

# Start recording now Y/N (default = Y)
print("")
recordnow="y"
while True:
    try:
        tmp=input("Start time-lapse shooting now (Y/N, Default Y: <Enter>): ")        
        recordnow=str(tmp).lower()
    except ValueError:
        print("Invalid input!")
        continue
    else:
        if (recordnow==""):
            recordnow="y"
            print("Default selected: starting the time-lapse shooting.")
            break
        if (recordnow=="n"):
            print("Only time-lapse command will be shown.")
            break
        if (recordnow=="y"):
            print("Starting the time-lapse shooting.")
            break
        print ("Select Y or N!")
        continue

# Change s to ms
interval=interval*1000
duration=duration*1000

# Generate shoot command
# Template:
#
# raspistill -t 60000 -tl 1 -n -ISO 100 -q 90 -ss 35000 -drc high
# -x IFD0.Artist="" -x IFD0.Copyright=""
# -fs 1 -o /media/kim/data/temp_images/test_frame%08d.jpg

## raspistill -n -t 1 -ISO 100 -q 10 -ss 20000 -bm -drc high
## -x IFD0.Artist="" -x IFD0.Copyright=""
## -o testi123.jpg
fname=name+"-frame%08d.jpg"
tmp="raspistill -t "+str(duration)+" "
tmp+="-tl "+str(interval)+" "
tmp+="-n "
tmp+="-ISO "+str(iso)+" "
tmp+="-q "+str(quality)+" "
tmp+="-ss "+str(exposure)+" "
tmp+=additional_params+" "
if artist!="":
  tmp+='-x IFD0.Artist="'+artist+'" '
  tmp+='-x IFD0.Copyright="'+artist+'" '
tmp+="-fs "+str(start_frame)+" "

if (path!=""):
    tmp+='-o '+path+'/'+fname
else:
    tmp+='-o '+fname

shootcommand=tmp

# Create a log file
logname=path+"/"+name+".log"
logname=""
if (path!=""):
    logname=path+"/"
logname+=name+".log"
now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")

file=open(logname,"w")
file.write("Log created on "+dt_string+"\n\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")
file.write("Time-lapse parameters:\n")
if artist!="":
  file.write("Artist: "+artist+"\n")
file.write("Resolution: "+str(camera_maxx)+"x"+str(camera_maxy)+"\n")
file.write("Sensor: "+camera_revision+"\n")
file.write("Quality: "+str(quality)+"\n")
file.write("ISO value: "+str(iso)+"\n")
file.write("Exposure: "+str(exposure)+"\n")
file.write("Duration: "+str(duration)+"\n")
file.write("Interval: "+str(interval)+"\n")
file.write("Additional parameters: "+str(additional_params)+"\n")
file.write("Start frame: "+str(start_frame)+"\n\n")
file.write("Shoot command:\n\n")
file.write(shootcommand)
file.close()

print("")
print (shootcommand)
print ("")

if (recordnow=="y"):
    os.system(shootcommand)

