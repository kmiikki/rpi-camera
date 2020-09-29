#!/usr/bin/python3
# (C) Kim Miikki 2020

from pathlib import Path
from time import sleep
from picamera import PiCamera
import picamera.array
import os
from datetime import datetime
import numpy as np
import cv2
import matplotlib.pyplot as plt
from rpi.inputs import *
from rpi.camerainfo import *
from rpi.roi import *

# Custom exposure ranges
exp_start=100
exp_end=20000
exp_step=100

# Uncomment to determine the minimum exposure time for a camera sensor
#exp_start=1
#exp_end=2000
#exp_step=1

width=320
height=240
roiX=0.5-width/camera_maxx
roiY=0.5-height/camera_maxy
roiW=width/camera_maxx
roiH=height/camera_maxy
results=[]

# Uncomment to overide red and blue gains
# Calibration gains for Manfrotto Lumie LEDs

# imx219
#awbg_red=1.6
#awbg_blue=1.4

# imx477
#awbg_red=3.2
#awbg_blue=1.3

print("Raspberry Pi Detect Minimum Exposure Time")
print("")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(1)

print("List disk and partitions:")
os.system('lsblk')
print("\nCurrent directory:")
os.system("pwd")
path=input('\nPath to images (current directory: <Enter>): ')
name=input('Project name (default=exp: <Enter>): ')

iso=1
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")

# Gain value: 1.0 to 12.0 for the IMX219 sensor on Camera Module V2
awb_on="n"
default_awb="y"
awb_on=inputYesNo("AWB","AWB mode on",default_awb)
if awb_on=="n":
    print("")
    awbg_red=inputValue("red gain",1.0,8.0,awbg_red,"","Value out of range!",False)
    awbg_blue=inputValue("blue gain",1.0,8.0,awbg_blue,"","Value out of range!",False)

default_save_images="y"
print("")
save_images=inputYesNo("Save images","Save captured images",default_save_images)

if len(path)>0:
    roi_file_exists=read_roi_file(roi_filename,path)
    
if roi_file_exists:
    roiX=float(roi_dict["roi_x0"])
    roiY=float(roi_dict["roi_y0"])
    roiW=float(roi_dict["roi_w"])
    roiH=float(roi_dict["roi_h"])
    roi_string=roi_dict["roi_x0"]+","
    roi_string+=roi_dict["roi_y0"]+","
    roi_string+=roi_dict["roi_w"]+","
    roi_string+=roi_dict["roi_h"]

# Create a log file
logname=""
pngname=""
outname=""
imgpath=""
if (path!=""):
    logname=path+"/"
    pngname=path+"/"
    outname=path+"/"
    imgpath=path+"/"
if name=="":
  name="exp"
logname+=name+".log"
pngname+=name+".png"
outname+="rgb-"+name+".txt"
imgpath+="img_"+name

if save_images=="y":
  # Test if picture directory is present or can be created
  try:
    if not os.path.exists(imgpath):
      os.mkdir(imgpath)
  except OSError:
    print("Unable to create a directory under following path: "+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1)

now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")
file=open(logname,"w")
file.write("Log created on "+dt_string+"\n\n")
file.write("Project name: "+name+"\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")

file.write("Capture pictures parameters:\n")
file.write("Resolution: "+str(camera_maxx)+"x"+str(camera_maxy)+"\n")
file.write("Sensor: "+camera_revision+"\n")
file.write("ISO value: "+str(iso)+"\n")
file.write("Image width : "+str(width)+"\n")
file.write("Image height: "+str(height)+"\n")
file.write("ROI x0: "+str(roiX)+"\n")
file.write("ROI y0: "+str(roiY)+"\n")
file.write("ROI w : "+str(roiW)+"\n")
file.write("ROI h : "+str(roiH)+"\n")
file.write("EXP min : "+str(exp_start)+"\n")
file.write("EXP max : "+str(exp_end)+"\n")
file.write("EXP step: "+str(exp_step)+"\n")
file.write("AWB mode: ")
if awb_on=="y":
    file.write("Enabled\n")
else:
    file.write("Disabled\n")
    file.write("Red gain:  "+str(awbg_red)+"\n")
    file.write("Blue gain: "+str(awbg_blue)+"\n")
file.write("Save images: ")
if save_images=="y":
    file.write("Enabled\n")
else:
    file.write("Disabled\n")
if save_images=="y":
  file.write("Images path: "+imgpath+"\n")

camera=PiCamera(resolution=(width,height))
camera.zoom=(roiX,roiY,roiW,roiH)
camera.iso=int(iso)
# Wait for the automatic gain control to settle
sleep(2)
# Now fix the values
camera.shutter_speed = int(exp_start)
camera.exposure_mode = "off"
g = camera.awb_gains
camera.awb_mode = "off"
if awb_on=="y":
    camera.awb_gains = g
    #print(g): This gives Fractions i.e. (Fraction(395, 256), Fraction(245, 128))
else:
    camera.awb_gains=(awbg_red,awbg_blue)

t1=datetime.now()

# Create a RGB plot
exposure=list()
red=[]
green=[]
blue=[]
min_x=exp_start
max_x=exp_end
min_y=0
max_y=255
x_scale_type="linear"
y_scale_type="linear"
fig=plt.figure(figsize=(8,6))
fig.canvas.set_window_title("Camera Sensor RGB Response Curves")
plt.xlabel("Exposure (µs)")
plt.ylabel("RGB average values")
plt.xlim(min_x,max_x)
plt.ylim(min_y,max_y)
plt.xscale(x_scale_type)
plt.yscale(y_scale_type)

print("")
print("Capturing images:")
for i in range(exp_start,exp_end+exp_step,exp_step):
  fname=str(i).rjust(8,'0')
  camera.shutter_speed = int(i)
  with picamera.array.PiRGBArray(camera) as output:
    camera.capture(output,'bgr')
    if save_images=="y":
      cv2.imwrite(imgpath+"/"+fname+".png",output.array) 
    rgb_means=np.array(output.array).mean(axis=(0,1))
    r_avg=rgb_means[2]
    g_avg=rgb_means[1]
    b_avg=rgb_means[0]
    rgb_avg=(r_avg+g_avg+b_avg)/3
    rgb_ratio=rgb_avg/255
    r_ratio=r_avg/255
    g_ratio=g_avg/255
    b_ratio=b_avg/255
    results.append([fname,rgb_avg,r_avg,g_avg,b_avg,rgb_ratio,r_ratio,g_ratio,b_ratio])
    exposure.append(i)
    red.append(r_avg)
    green.append(g_avg)
    blue.append(b_avg)
    print(i,rgb_means[::-1])
    output.truncate(0)
red_curve,=plt.plot(exposure,red,color="#ff0000")
green_curve,=plt.plot(exposure,green,color="#00ff00")
blue_curve,=plt.plot(exposure,blue,color="#0000ff")
plt.savefig(pngname,dpi=(300))
plt.close("all")
t2=datetime.now()  
  
camera.close()
print("Time elapsed: "+str(t2-t1))
file.write("Time elapsed:;"+str(t2-t1)+"\n")
file.close()

# Test if a RGB file can be created
try:
  file=open(outname,"w")
except OSError:
  print("Unable to create a RGB file in the following directory:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

file.write("exposure (µs);rgb_avg;r_avg;g_avg;b_avg;rgb_ratio;r_ratio;g_ratio;b_ratio\n")
for value in results:
  s=""
  for i in range(0,9):
    s+=str(value[i])
    if i<8:
      s+=";"
  file.write(s+"\n")

plt.close("all")
