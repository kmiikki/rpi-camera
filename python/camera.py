#!/usr/bin/python3
# Camera with Preview
# (C) Kim Miikki 2020

from picamera import PiCamera
import os,sys,tty,termios
from datetime import datetime
from rpi.inputs import *
from rpi.camerainfo import *

exposure=1
framenumber=1
frame_default=1
digits=4
digits_default=4
digits_max=8
quality_default=90
artist=""
artistfile="artist.txt"

print("Raspberry Pi camera")
print("")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)
   
quality_default=90
quality=inputValue("image quality",1,100,quality_default,"","Quality is out of range!",True)

print("\nList disk and partitions:")
os.system('lsblk')
print("\nCurrent directory:")
os.system("pwd")
path=input('\nPath to images (current directory: <Enter>): ')
name=input('Project name (default=pic: <Enter>): ')

iso=100
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")


autoexp_on="y"
autoexp_default="y"
autoexp_on=inputYesNo("EXP auto","Auto exposure on",autoexp_default)


# Exposure unit: µs
if autoexp_on=="n":
    exp_min=1
    exp_max=3300000
    exp_default=2000
    exposure=inputValue("exposure time",exp_min,exp_max,exp_default,"µs","Exposure is out of range!",True)

# Gain value: 1.0 to 12.0 for the IMX219 sensor on Camera Module V2
print("")
awb_on="n"
default_awb="y"
awb_on=inputYesNo("AWB","AWB mode on",default_awb)
if awb_on=="n":
    print("")
    awbg_red=inputValue("red gain",1.0,8.0,awbg_red,"","Value out of range!",False)
    awbg_blue=inputValue("blue gain",1.0,8.0,awbg_blue,"","Value out of range!",False)

analog_gain=0
analog_gain_default=1.0
print("")
analog_gain=inputValue("analog gain",0.0,12.0,analog_gain_default,"","Analog gain is out of range!",False)

# Digits
min_digits=len(str(framenumber))
max_digits=8
if min_digits>digits_default:
  digits_default=min_digits
print("")
digits=inputValue("digits",min_digits,max_digits,digits_default,"","Digits is out of range!",True)

# Start frame
frame_min=1
frame_max=10**digits-1
frame_default=1
framenumber=inputValue("first frame",frame_min,frame_max,frame_default,"","Frame number is out of range!")

# Create a log file
logname=""
if (path!=""):
    logname=path+"/"
if name=="":
  name="pic"
logname+=name+".log"

now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")

file=open(logname,"w")
file.write("Log created on "+dt_string+"\n\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")
try:
    f=open(artistfile,"r")
    artist=f.readline()
    artist=artist.strip()
    print("Artist: "+artist)
    f.close()
except IOError:
    artist=""
if artist!="":
  file.write("Artist: "+artist+"\n")
file.write("Capture pictures parameters:\n")
file.write("Resolution: "+str(camera_maxx)+"x"+str(camera_maxy)+"\n")
file.write("Sensor: "+camera_revision+"\n")
file.write("Quality: "+str(quality)+"\n")
file.write("Compression: lossy"+"\n")
file.write("ISO value: "+str(iso)+"\n")
if autoexp_on=="y":
    file.write("Exposure: auto\n")
else:
    file.write("Exposure: "+str(exposure)+" µs\n")
file.write("AWB mode: ")
if awb_on=="y":
    file.write("Enabled\n")
else:
    file.write("Disabled\n")
    file.write("Red gain:  "+str(awbg_red)+"\n")
    file.write("Blue gain: "+str(awbg_blue)+"\n")
file.write("Analog gain: "+str(analog_gain)+"\n")
file.write("Start frame: "+str(framenumber)+"\n")
file.write("Digits: "+str(digits)+"\n")
file.write("First file name: "+name+"_"+str(framenumber).rjust(digits,'0')+".jpg\n\n")

# Build raspistill command
#
# Templates
# raspistill -v -q 90 -ISO 100 -awb off -awbg 1.5,1.5 -ag 1 -k -fs 1 -o image%04d.jpg
# raspistill -v -q 90 -ISO 100 -ss 20000 -ex off -drc high -awb off -awbg 3.16,1.24 -ag 1.0 -k -fs 1 -o pic_%04d.jpg
# raspistill -v -q 90 -ISO 100 -ag 1.0 -k -fs 1 -o pic_%04d.jpg

tmp="raspistill "
tmp+="-v "
tmp+="-t 0 "
tmp+="-q "+str(quality)+" "
tmp+="-ISO "+str(iso)+" "
if autoexp_on=="n":
    tmp+="-ss "+str(exposure)+" "
    tmp+="-ex off "
    tmp+="-drc high "
    tmp+="-dg 1.0 "    
if awb_on=="n":
    tmp+="-awb off -awbg "+str(awbg_red)+","+str(awbg_blue)+" "
tmp+="-ag "+str(analog_gain)+" "
tmp+="-k "
# Slow png capturing
# tmp+="-e png "
if artist!="":
    tmp+='-x IFD0.Artist="'+artist+'" '
    tmp+='-x IFD0.Copyright="'+artist+'" '
tmp+="-fs "+str(framenumber)+" "
fname=name+"_%0"+str(digits)+"d"
if (path!=""):
    tmp+='-o '+path+'/'+fname
else:
    tmp+='-o '+fname
tmp=tmp+".jpg"

file.write("Capture command:\n")
file.write(tmp+"\n")
file.close()

os.system(tmp)
