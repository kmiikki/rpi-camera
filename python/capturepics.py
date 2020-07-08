#!/usr/bin/python3
# (C) Kim Miikki 2019

import os,sys,tty,termios
from datetime import datetime
from rpi.inputs import *
from rpi.camerainfo import *

ESC=27
ENTER=13
SPACE=32
exposure=1
framenumber=1
frame_default=1
digits=4
digits_default=4
quality_default=90
artist=""
artistfile="artist.txt"

# Uncomment to overide red and blue gains
# Calibration gains for Manfrotto Lumie LEDs
#awbg_red=1.6
#awbg_blue=1.4

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
def getch():
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)
  return ch

print("Raspberry Pi capture pictures")
print("")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)

quality_default=90
quality=inputValue("image quality",1,100,quality_default,"","Value out of range!",True)

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

# Exposure unit: µs
exp_min=1
exp_max=330000
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
    artistfile=path+"/"+artistfile
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
    # print("No artist.txt file")
print("")
quick_preview=inputYesNo("quick preview","Quick preview mode","y")

if artist!="":
    file.write("Artist: "+artist+"\n")    
file.write("Capture pictures parameters:\n")
file.write("Resolution: "+str(camera_maxx)+"x"+str(camera_maxy)+"\n")
file.write("Sensor: "+camera_revision+"\n")
file.write("Quality: "+str(quality)+"\n")
file.write("ISO value: "+str(iso)+"\n")
file.write("Exposure: "+str(exposure)+" µs\n")
file.write("AWB mode: ")
if awb_on=="y":
    file.write("Enabled\n")
else:
    file.write("Disabled\n")
    file.write("Red gain:  "+str(awbg_red)+"\n")
    file.write("Blue gain: "+str(awbg_blue)+"\n")
file.write("Digits: "+str(digits)+"\n")
file.write("Start frame: "+str(framenumber)+"\n")
file.write("First file name: "+name+"_"+str(framenumber).rjust(digits,'0')+".png\n\n")

print("\nStart capturing images: ENTER")
print("Capture image: SPACE")
print("Exit program:  ESC\n")
while True:
  ch=getch()
  if ch==chr(ENTER):
    print("Capture mode enabled.")
    break
  if ch==chr(ESC):
    file.close()
    sys.exit()

while framenumber<10**digits:
  ch=getch()
  if ch==chr(SPACE):
    fname=name+"_"+str(framenumber).rjust(digits,'0')
    print(fname)
    framenumber+=1
    tmp="raspistill "
    if quick_preview=="n":
        tmp+="-n "
    tmp+="-t 1 "
    tmp+="-ISO "+str(iso)+" "
    tmp+="-q "
    tmp+=str(quality)+" "
    tmp+="-ss "+str(exposure)+" "
    # tmp+="-ex off "
    #tmp+="-bm -drc high "
    if awb_on=="n":
        tmp+="-awb off -awbg "+str(awbg_red)+","+str(awbg_blue)+" "
    if artist!="":
        tmp+='-x IFD0.Artist="'+artist+'" '
        tmp+='-x IFD0.Copyright="'+artist+'" '
    if (path!=""):
        tmp+='-o '+path+'/'+fname
    else:
        tmp+='-o '+fname
    tmp=tmp+".png"
    os.system(tmp)
    file.write(tmp+"\n")
  if ch==chr(ESC):
    break
  
file.close()
