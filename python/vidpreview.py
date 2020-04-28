#!/usr/bin/python3
# (C) Kim Miikki 2020

import tkinter # python version < 3: Tkinter
from picamera import PiCamera
import sys,tty,termios

ESC=27
ENTER=13
sensorX=3280
sensorY=2464

# MD, Description, A/R, video x, video y, FOV w, FOW h
videomodes=[
    [1," 1920x1080","16:9",680,692,1920,1080],
    [2," 1920x1080","16:9",0,310,3280,1845],
    [3," 1920x1080","16:9",0,310,3280,1845],
    [4," 1640x1232"," 4:3",0,0,3280,2464],
    [5,"  1640x922","16:9",0,310,3280,1845],
    [6,"  1280x720","16:9",360,512,2560,1440],
    [7,"   640x480"," 4:3",1000,752,1280,960]
]

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

print("Raspberry Pi camera v. 2.x video preview")
root=tkinter.Tk()

print("\nVideo modes")
print("Md Video     A/R   X0   Y0   ROI W  ROI H")
       #1," 1920x1080","16:9",1920,1080,1920,1080],
for md,description,ar,video_x,video_y,fow_w,fow_h in videomodes:
  print(md,description,ar,str(video_x).rjust(4," "),str(video_y).rjust(4," "),str(fow_w).rjust(5," "),str(fow_h).rjust(6," "))

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
roiX=(sensorX-videomodes[md-1][5])/(2*sensorX)
roiY=(sensorY-videomodes[md-1][6])/(2*sensorY)
roiW=videomodes[md-1][5]/sensorX
roiH=videomodes[md-1][6]/sensorY

strx=str(round(roiX,6)).rstrip("0").rstrip(".")
stry=str(round(roiY,6)).rstrip("0").rstrip(".")
strw=str(round(roiW,6)).rstrip("0").rstrip(".")
strh=str(round(roiH,6)).rstrip("0").rstrip(".")

print("")
print("Md:  "+ch)
print("ROI: "+strx+","+stry+","+strw+","+strh)

camera=PiCamera(resolution=(3280,2464))
camera.zoom=(roiX,roiY,roiW,roiH)
camera.start_preview()
while True:
  if getch() == chr(ESC):
    break
camera.stop_preview()
