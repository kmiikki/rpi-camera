#!/usr/bin/python3
# (C) Kim Miikki 2019

import tkinter # python version < 3: Tkinter
from picamera import PiCamera
import sys,tty,termios
from rpi.camerainfo import *

ESC=27
ENTER=13
maxx_tested=1600
maxy_tested=1200

fd = sys.stdin.fileno()
old_settings = termios.tcgetattr(fd)
def getch():
  try:
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
  finally:
    termios.tcsetattr(fd,termios.TCSADRAIN,old_settings)
  return ch

print("Raspberry Pi camera module ("+camera_revision+") live preview")
print("")
if camera_detected==0:
    print("Raspberry Pi camera module not found!")
    exit(0)

root=tkinter.Tk()
w=root.winfo_screenwidth()
h=root.winfo_screenheight()
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
        break
      if ch=="N":
        print(ch)
      if ch==chr(ENTER):
        print("Default selected")
      w=maxx_tested
      h=maxy_tested
      break

print("Preview:      ENTER")
print("Exit program: ESC")
while True:
  ch=getch()
  if ch==chr(ENTER):
    break
  if ch==chr(ESC):
    sys.exit()

camera=PiCamera(resolution=(camera_maxx,camera_maxy))
camera.start_preview(resolution=(w,h))
while True:
  if getch() == chr(ESC):
    break
camera.stop_preview()
