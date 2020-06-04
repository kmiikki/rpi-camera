#!/usr/bin/python3
# (C) Kim Miikki 2020

import tkinter # python version < 3: Tkinter
import sys,tty,termios
from rpi.camerainfo import *

ESC=27
ENTER=13
sensorX=camera_maxx
sensorY=camera_maxy

# ROI x0, ROI y0, ROI w, ROI h
roi=[
    ["ROI x0","ROI y0","ROI w","ROI h"]
]

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
def getch():
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)
  return ch

print("Raspberry Pi camera module ("+camera_revision+") video preview")
print("")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)
    
root=tkinter.Tk()
print("Video modes")
if camera_revision=="imx219":
  print("Md Video     A/R   X0   Y0   ROI W  ROI H")
        #1," 1920x1080","16:9",1920,1080,1920,1080],
elif camera_revision=="imx477":
  print("Md Video     A/R     X0   Y0   ROI W  ROI H")
for md,description,ar,fov,x0,y0,roi_w,roi_h,fps_min,fps_max in videomodes:
  print(md,description,ar,str(x0).rjust(4," "),str(y0).rjust(4," "),str(roi_w).rjust(5," "),str(roi_h).rjust(6," "))

print("")
print("Preview:      Md")
print("Exit program: ESC")

while True:
  ch=getch()
  if "1234567".find(ch)>=0:
    break
  if ch==chr(ESC):
    sys.exit()

md=int(ch)
roiX=videomodes[md-1][4]/sensorX
roiY=videomodes[md-1][5]/sensorY
roiW=videomodes[md-1][6]/sensorX
roiH=videomodes[md-1][7]/sensorY

strx=str(round(roiX,6)).rstrip("0").rstrip(".")
stry=str(round(roiY,6)).rstrip("0").rstrip(".")
strw=str(round(roiW,6)).rstrip("0").rstrip(".")
strh=str(round(roiH,6)).rstrip("0").rstrip(".")

print("")
print("Md:  "+ch)
print("ROI: "+strx+","+stry+","+strw+","+strh)

camera=PiCamera(resolution=(camera_maxx,camera_maxy))
camera.zoom=(roiX,roiY,roiW,roiH)
camera.start_preview()
while True:
  if getch() == chr(ESC):
    break
camera.stop_preview()
