#!/usr/bin/python3
# (C) Kim Miikki 2020

import csv
from picamera import PiCamera
import os,sys,tty,termios
import tkinter as tk
from rpi.camerainfo import *
from rpi.roi import *

roi_crop_enabled=True
high_resolution=False

# Maxiumum resolution for PiCam preview
max_width=1920
max_height=1080

ESC=27
ENTER=13
SPACE=32

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
def getch():
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)
  return ch

root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

roi_result=validate_roi_values()
if roi_result==True:
    zoom=(roi_x0,roi_y0,roi_w,roi_h)
    
    print("Raspberry Pi Camera ROI Preview")
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
        
    if screen_width>max_width or screen_height>max_height:
        high_resolution=True
        cmd_roi="raspistill -t 0 -roi "
        cmd_roi+=str(roi_x0)+","+str(roi_y0)+","+str(roi_w)+","+str(roi_h)
        print("Current resolution:    "+str(screen_width)+"x"+str(screen_height))
        print("Max toggle resolution: "+str(max_width)+"x"+str(max_height)+"\n")
        print("Exit program: Ctrl + C -> ESC")
        os.system(cmd_roi)

    else:
        print("Toggle between FOV and ROI: SPACE")
        print("Exit program:  ESC")
    camera=PiCamera(resolution=(camera_maxx,camera_maxy))
    camera.zoom=zoom
    camera.awb_mode = "auto"
    if not high_resolution:
        camera.start_preview()
    while True:
      ch=getch()
      if ch==chr(SPACE):
        roi_crop_enabled=not roi_crop_enabled
        if roi_crop_enabled:
            camera.zoom=zoom
        else:
            camera.zoom=(0,0,1,1)
      elif ch==chr(ESC):
        if not high_resolution:
          camera.stop_preview()
        camera.close()
        exit(0)
else:
    print("ROI file not found.")