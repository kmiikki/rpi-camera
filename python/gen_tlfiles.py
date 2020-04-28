#!/usr/bin/python3
  
import fnmatch
import os, os.path
import math
import shutil
from datetime import datetime

def countJPG(filesdir):
  count=len(fnmatch.filter(os.listdir(filesdir), "*.jpg"))
  return count

def countPNG(filesdir):
  count=len(fnmatch.filter(os.listdir(filesdir), "*.png"))
  return count

def input():
  return 0

# Global variables
fname=""
jpgs=0
pngs=0
fileformat="*.png"
ext=""
convert_list=[]
pictures=0
digits=0
min_digits=0
max_digits=10
digits=0
default_digits=4

start_frame=1

t1=datetime.now()
print("Pictures to Time-lapse files 1.0, (c) Kim Miikki 2020")
print("")

# Get current directory
curdir=os.getcwd()
tldir=curdir+"/tl"

try:
  if not os.path.exists(tldir):
    os.mkdir(tldir)
except OSError:
  print("Unable to create a direcory or direcories under following path:\n"+curdir)
  print("Program is terminated.")
  exit(1)

jpgs=countJPG(curdir)
pngs=countPNG(curdir)
if jpgs==0 and pngs==0:
  print("No PNG or JPG files found!")
  print ("Program is terminated.")
  exit(1)

if jpgs>pngs:
  pictures=jpgs
  fileformat="*.jpg"
  ext=".jpg"
else:
  pictures=pngs
  fileformat="*.png"
  ext=".png"

for filename in sorted(os.listdir(curdir)):
  if fnmatch.fnmatch(filename,fileformat):
    convert_list.append([filename,""])

digits=len(str(pictures))
ratio=pictures/math.pow(10,digits)

if ratio>=0.9:
  digits+=1
  default_digits=digits

for i in range(pictures):
  s="img_"+str(i).rjust(digits,"0")
  convert_list[i][1]=s+ext

# Create a list of new file names
for i in range(pictures):
  s="img_"+str(i+start_frame).zfill(digits)+ext
  convert_list[i][1]=s

src_path=curdir+"/"
dst_path=tldir+"/"

for src,dst in convert_list:
  old=src
  new=dst
  print("cp "+src_path+src,dst_path+dst)
  shutil.copy(src_path+src,dst_path+dst)

now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")
file=open(dst_path+"/tl-files.log","w")
file.write("Log created on "+dt_string+"\n\n")
t2=datetime.now()
for src,dst in convert_list:
  file.write(src+";"+dst+"\n")
file.write("\nTime elapsed:\t"+str(t2-t1))
print("\nTime elapsed:"+str(t2-t1))
file.close()
