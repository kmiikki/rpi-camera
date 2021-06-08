#!/usr/bin/python3
# (C) Kim Miikki 2020

from time import sleep
import tkinter # python version < 3: Tkinter
from picamera import PiCamera
import os,sys,tty,termios
from datetime import datetime
from rpi.inputs import *
from rpi.camerainfo import *
from rpi.roi import *

png_mode=True
roi_crop_enabled=True
high_resolution=False
zoom=(0,0,1,1)

# Maxiumum resolution for PiCam preview
max_width=1920
max_height=1080

TAB=9
ESC=27
ENTER=13
SPACE=32
maxx_tested=1600
maxy_tested=1200
exposure=1
framenumber=1
frame_default=1
digits=4
digits_default=4
digits_max=8
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

print("Current directory:")
os.system("pwd")
print("")

roi_result=validate_roi_values()
if roi_result:
    zoom=(roi_x0,roi_y0,roi_w,roi_h)
    display_roi_status()
    print("")

png_mode="y"
default_png="y"
png_mode=inputYesNo("PNG","PNG mode on",default_png)
   
# Quality is not required for PNG format
if png_mode=="n":
    quality_default=90
    quality=inputValue("image quality",1,100,quality_default,"","Quality is out of range!",True)

print("")
path=input('Path to images (current directory: <Enter>): ')
name=input('Project name (default=pic: <Enter>): ')

iso=100
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")

# Exposure unit: µs
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
# Quality is not rquired for PNG format
if png_mode=="n":
    file.write("Quality: "+str(quality)+"\n")
    file.write("Compression: lossy\n")
else:
    file.write("Compression: lossless\n")
file.write("ISO value: "+str(iso)+"\n")
file.write("Exposure: "+str(exposure)+" µs\n")
file.write("AWB mode: ")
if awb_on=="y":
    file.write("Enabled\n")
else:
    file.write("Disabled\n")
    file.write("Red gain:  "+str(awbg_red)+"\n")
    file.write("Blue gain: "+str(awbg_blue)+"\n")
file.write("Start frame: "+str(framenumber)+"\n")
file.write("Digits: "+str(digits)+"\n")
file.write("First file name: "+name+"_"+str(framenumber).rjust(digits,'0'))
if png_mode=="y":
    file.write(".png\n")
else:
    file.write(".jpg\n")

root=tkinter.Tk()
w=root.winfo_screenwidth()
h=root.winfo_screenheight()
if w>max_width or h>max_height:
    print("")
    print("Current resolution:    "+str(w)+"x"+str(h))
    print("Max supported resolution: "+str(max_width)+"x"+str(max_height))
    print("New preview resolution:   "+str(max_width)+"x"+str(max_height))
    w=max_width
    h=max_height
    #print("Proram is terminated.")
    #exit(0)

print("")
if (w>maxx_tested) or (h>maxy_tested):
  print("Full screen and cropped preview (Y/N, default: N <ENTER>)")
  while True:
    try:
      ch=getch()
      ch=ch.upper()
    except ValueError:
      print("Not a valid selection!")
      continue
    else:
      if not (ch=="Y" or ch=="N" or ch==chr(ENTER)):
        continue
      if ch=="Y":
        print(ch)
        break
      if ch=="N":
        print(ch)
      if ch==chr(ENTER):
        print("Default selected")
      w=maxx_tested
      h=maxy_tested
      break

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

camera=PiCamera(resolution=(camera_maxx,camera_maxy))
camera.iso=int(iso)
camera.zoom=zoom
camera.start_preview(resolution=(w,h))
# Wait for the automatic gain control to settle
sleep(2)
# Now fix the values
camera.shutter_speed = int(exposure)
camera.exposure_mode = "off"
g = camera.awb_gains
camera.awb_mode = "off"
if awb_on=="y":
    camera.awb_gains = g
    #print(g): This gives Fractions i.e. (Fraction(395, 256), Fraction(245, 128))
else:
    camera.awb_gains=(awbg_red,awbg_blue)

# Finally, take several photos with the fixed settings
while framenumber<10**digits:
  ch=getch()
  if ch==chr(SPACE):
    camera.stop_preview()
    fname=name+"_"+str(framenumber).rjust(digits,'0')
    print(fname)
    if path!="":
        fname=path+"/"+fname
    if png_mode=="y":
        fname=fname+".png"
    else:
        fname=fname+".jpg"
    old=camera.zoom
    if roi_result:
        camera.zoom=zoom
    else:
        camera.zoom=(0,0,1,1)
    if png_mode=="y":
        camera.capture(fname)
    else:
        camera.capture(fname,format="jpeg",quality=quality)
    file.write(fname+"\n")
    framenumber+=1
    camera.zoom=old
    camera.start_preview()
  elif ch==chr(TAB):
    roi_crop_enabled=not roi_crop_enabled
    if roi_crop_enabled:
        camera.zoom=zoom
    else:
        camera.zoom=(0,0,1,1)
  elif ch==chr(ESC):
    break

camera.stop_preview()
camera.close()
file.close()
