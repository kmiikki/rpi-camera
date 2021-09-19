#!/usr/bin/python3
from pathlib import Path
from datetime import datetime
import os
import exifread
from PIL import Image
import sys
import math
import re
import numpy as np
import cv2
import pandas as pd

# gtlvideo version 1.1
# OpenCV based crop/resize instead of ffmpeg: 3.5x processing speedup

# gtlvideo version 1.2
# Video creation support: h264, mkv and mp4
# ffmpeg argument added:  -pix_fmt yuv420p

# Global variables
version_text="1.2"
copyright_text="(C) Kim Miikki 2019"
project_name=""
isProjectName=False
video_name=""
log_name=""
vformat="mkv"

files_cr2=0
wcr2=0
hcr2=0

maxvideomode=13

files_png=0
wpng=0
hpng=0

files_jpg=0
wjpg=0
hjpg=0

# Get current directory
current_dir=""
png_path=""
video_path=""
input_path=""
output_path=""

native_video=False

cr2_sample=""  # Sample file names of CR2, PNG or/and JPG
png_sample=""
jpg_sample=""
base_name=""
suffix=""
cr2_suffix=""
png_suffix=""
jpg_suffix=""
sample=""
sample_length=0
numbers=0

frames_start=0 # First picture
frames_end=0   # Last picture

cr2list=np.array([]).astype(int)
pnglist=np.array([]).astype(int)
jpglist=np.array([]).astype(int)
difflist=np.array([]).astype(int)
duplist=np.array([]).astype(int)

frames_min=0
frames_max=0
framenumber=0
min_cr2=0
max_cr2=0
min_png=0
max_png=0
min_jpg=0
max_jpg=0

different_names_cr2=False
different_names_png=False
different_names_jpg=False

wn=0 #n=native
hn=0

files=0 # Total files count of automatically selected picture format

wc=0 #c=custom
hc=0

file_format=""
mode=0
landscape=""
cropmode=""
crop_type=[]

ratiohw=0
ratiodc=0
crop90=False
xnew=0
ynew=0
newcropmode=""

scoreh=0  # h, w help variables
scorew=0

videox=0  # video size
videoy=0

xmarginal=0
ymarginal=0

xcropmin=0
ycropmin=0
xcropmax=0
ycropmax=0

xcrop1=0
ycrop1=0
xcrop2=0
ycrop2=0

selection=0
crop_selection=0

inter_methods=[cv2.INTER_NEAREST,
               cv2.INTER_LINEAR,
               cv2.INTER_CUBIC,
               cv2.INTER_AREA,
               cv2.INTER_LANCZOS4
               ]
method=2

fps=0
crf=0

crop=False
list_summary=[]

def get_python_version(ver_major=0, ver_minor=0):
  ver_major=sys.version_info.major
  ver_minor=sys.version_info.minor
  return ver_major, ver_minor

def get_info_cr2(cr2_sample="", files=0, w=0, h=0):
  global min_cr2
  global max_cr2
  global framenumber
  global different_names_cr2
  global cr2_suffix
  global cr2list
  
  # Get current directory
  curdir=os.getcwd()
  path=Path(curdir)

  # Loop trough all CR2 files in current directory
  files=0
  fname=""
  length=0
  digits=0
  for p in sorted(path.iterdir(),reverse=True):
    if p.is_file() and p.suffix.upper()=='.CR2':
      files+=1
      fname=p.name
      if files==1:
        cr2_suffix=p.suffix
        cr2_sample=p.name
        length=len(cr2_sample)
        digits=get_sample_numbers(cr2_sample)
        file_path=str(path)+"/"+fname
        fil=open(file_path,'rb')
        tags=exifread.process_file(fil)
        if not isPictureNameOk(fname,length,digits):
          print("Sample picture (CR2) name is not valid! Program terminated.\n")
          sys.exit(1)
        min_cr2=framenumber
        max_cr2=framenumber
        cr2list=np.append(cr2list, framenumber)
        for tag in tags.keys():
          if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            if (tag=="EXIF ExifImageWidth"):
              w=tags[tag]
            if (tag=="EXIF ExifImageLength"):
              h=tags[tag]
        fil.close()
      if files>1 and isPictureNameOk(fname,length,digits)==True:
        if framenumber<min_cr2:
          min_cr2=framenumber
        else:
          if framenumber>max_cr2:
            max_cr2=framenumber
        cr2list=np.append(cr2list, framenumber) 
  if cr2list.size>0:
    cr2list=np.sort(cr2list)
  return cr2_sample, files, w, h

def get_info_png(png_sample="", files=0, w=0, h=0):
  global min_png
  global max_png
  global framenumber
  global different_names_png
  global png_suffix
  global pnglist

  # Get current directory
  curdir=os.getcwd()
  path=Path(curdir)

  # List all png files in current directory
  length=0
  digits=0
  fname=""
  result=False  
  for p in sorted(path.iterdir(),reverse=True):
    if p.is_file() and p.suffix.lower()=='.png':
      files+=1
      fname=p.name
      if files==1:
        png_suffix=p.suffix
        png_sample=p.name
        length=len(png_sample)
        digits=get_sample_numbers(png_sample)
        if not isPictureNameOk(fname,length,digits):
          print("Sample picture (PNG) name is not valid! Program terminated.")
          print(cr2_sample,length,digits)
          print("")
          sys.exit(1)
        min_png=framenumber
        max_png=framenumber
        pnglist=np.append(pnglist, framenumber)
      if files>1:
        result=isPictureNameOk(fname,length,digits)
        if result==True:
          if framenumber<min_png:
            min_png=framenumber
          else:
            if framenumber>max_png:
              max_png=framenumber
          pnglist=np.append(pnglist, framenumber)
        else:
          print("PNG: Different picture name format!")
          different_names_png=True       
    if fname!="":
      with Image.open(fname) as img:
        w, h = img.size
  if pnglist.size>0:        
    pnglist=np.sort(pnglist)
  return png_sample, files, w, h

def get_info_jpg(jpg_sample="", files=0, w=0, h=0):
  global min_jpg
  global max_jpg
  global framenumber
  global different_names_jpg
  global jpg_suffix
  global jpglist
  
  # Get current directory
  curdir=os.getcwd()
  path=Path(curdir)

  # List all jpg files in current directory
  length=0
  digits=0
  fname=""
  result=False
  for p in sorted(path.iterdir(),reverse=True):
    if p.is_file() and p.suffix.lower()=='.jpg':
      files+=1
      fname=p.name
      if files==1:
        jpg_suffix=p.suffix
        jpg_sample=p.name
        length=len(jpg_sample)
        digits=get_sample_numbers(jpg_sample)
        if not isPictureNameOk(fname,length,digits):
          print("Sample picture (JPG) name is not valid! Program terminated.")
          print("")
          sys.exit(1)
        min_jpg=framenumber
        max_jpg=framenumber
        jpglist=np.append(jpglist, framenumber)
      if files>1:
        result=isPictureNameOk(fname,length,digits)
        if result==True:
          if framenumber<min_jpg:
            min_jpg=framenumber
          else:
            if framenumber>max_jpg:
              max_jpg=framenumber
          result=isPictureNameOk(fname,length,digits)
          jpglist=np.append(jpglist, framenumber)
        else:
          print("jpg: Different picture name format!")
          different_names_jpg=True
    if fname!="":
      with Image.open(fname) as img:
        w, h = img.size
  if jpglist.size>0:        
    jpglist=np.sort(jpglist)
  return jpg_sample, files, w, h

def default_picture_format(files_cr2, files_png, files_jpg):
  global suffix
  global cr2_suffix
  global png_suffix
  global jpg_suffix
  
  # Priority order: CR2 > PNG > JPG
  pformat=""
  if (files_cr2>0 or files_png>0 or files_jpg>0):
    if (files_cr2>=files_png and files_cr2>=files_jpg):
      pformat="CR2"
      suffix=cr2_suffix
      sample=cr2_sample
    else:
      if (files_png>=files_jpg):
        pformat="PNG"
        suffix=png_suffix
        sample=png_sample
      else:
        pformat="JPG"
        suffix=jpg_suffix
        sample=jpg_sample
  return sample, pformat
  
def get_sample_numbers(s=""):
  numbers=0
  l=len(s)
  if (l<=4):
    print("Picture name(s) is too short! Program terminated.")
    print("")
    sys.exit(1)
  else:
    s=s[0:l-4]
  # Count numbers from end of the string
  l=len(s)
  i=l-1
  while(i>=0):
    #print(s[i:l])
    if not s[i:l].isdigit():
      break
    i=i-1
    numbers+=1
  if (numbers<1):
    print("Picture name ("+s+") is not valid! Program terminated.")
    print("")
    sys.exit(1)
  return numbers
  
def isPictureNameOk(s="",length=0,digits=0):
  global framenumber
  ok=True
  if (len(s)<4+digits) or length!=len(s):
    ok=False
  if ok:
    strnum=s[length-4-digits:length-4]
    if int(strnum)>=0:
      framenumber=int(strnum)
  return ok
  
def isEq(a,b,decimals):
  largea=a*math.pow(10,decimals)
  largeb=b*math.pow(10,decimals)
  if (int(largea)==int(largeb)):
    return True
  else:
    return False

def isLess_or_Eq(a,b,decimals):
  largea=a*math.pow(10,decimals)
  largeb=b*math.pow(10,decimals)
  if (int(largea)<=int(largeb)):
    return True
  else:
    return False    

def getMinCropSize(xnew,ynew):
  xmin=0
  ymin=0
  ratiochw=ynew/xnew
  while (xmin<xnew) or (ymin<ynew):
    # Check if ratio is landscape
    if (ratiochw<=1):
      xmin=xmin+1
      ymin=ratiochw*xmin
    else:
      ymin=ymin+1
      xmin=ymin/ratiochw
    xmin=int(xmin)
    ymin=int(ymin)
    if xmin>=1 and ymin>=1:
      break
    continue
  return xmin,ymin

# ------------
# Main program
# ------------

version_major, version_minor=get_python_version()
print("Generate time-lapse videos from images")
print("Version "+str(version_text)+" "+copyright_text)
print("")
print("Python version: "+str(version_major)+"."+str(version_minor))
if not version_major==3 and version_minor >= 5:
  print("This script requires Python 3.5 or higher!")
  print("You are using Python {}.{}".format(version_major, version_minor))
  sys.exit(1)

videomodes=[
    [0,"Native",0,0,"x:y",25],
    [1,"8K/UHD",7680,4320,"16:9",25],
    [2,"4K/DCI",4096,2160,"256:135",25],
    [3,"4K/UHD",3840,2160,"16:9",25],
    [4,"2K",2560,1440,"16:9",25],
    [5,"Full HD",1920,1080,"16:9",30],
    [6,"Pi/md4",1640,1232,"4:3",40],
    [7,"Pi/md5",1640,922,"16:9",40],
    [8,"HD",1280,720,"16:9",90],
    [9,"SD",720,576,"16:9",90],
    [10,"XGA",1024,768,"4:3",200],
    [11,"VGA",640,480,"4:3",200],
    [12,"GIF",320,200,"4:3",180],
    [13,"Custom",0,0,"x:y",25]
]

# Get current directory
current_dir=os.getcwd()
png_path=current_dir+"/png/"
video_path=current_dir+"/video/"

#print(current_dir)
print("\nScanning supported image files in current directory...")

cr2_sample, files_cr2, wcr2, hcr2 = get_info_cr2()
png_sample, files_png, wpng, hpng = get_info_png()
jpg_sample, files_jpg, wjpg, hjpg = get_info_jpg()

print("\nCR2 info:")
print("Files: ",files_cr2)
print("Width: ",wcr2)
print("Height:",hcr2)

print("\nPNG info:")
print("Files: ",files_png)
print("Width: ",wpng)
print("Height:",hpng)

print("\nJPG info:")
print("Files: ",files_jpg)
print("Width: ",wjpg)
print("Height:",hjpg)

if (files_cr2==0) and (files_png==0) and (files_jpg==0):
	print ("\nCR2, PNG or JPG files not found!")
	sys.exit()

sample, file_format=default_picture_format(files_cr2, files_png, files_jpg)
print("\nSample file name: "+sample)
numbers=get_sample_numbers(sample)
print("Digits before file extension:",numbers)

# Get minumum and maximum image number

if file_format!="":
  print("Default picture format:",file_format)
  if file_format=="CR2":
    wn=int(wcr2.printable)
    hn=int(hcr2.printable)
    files=files_cr2
    frames_start=min_cr2
    frames_end=max_cr2
  if file_format=="PNG":
    wn=wpng
    hn=hpng
    files=files_png
    frames_start=min_png
    frames_end=max_png
  if file_format=="JPG":
    wn=wjpg
    hn=hjpg
    files=files_jpg
    frames_start=min_jpg
    frames_end=max_jpg
  
rangelist=np.linspace(frames_start,frames_end,frames_end-frames_start+1).astype(int)
if rangelist.size>0:        
  rangelist=np.sort(rangelist)
  # print(rangelist)
  mean=0
  if file_format=="CR2":
    difflist=np.setdiff1d(rangelist,cr2list)
    df=pd.DataFrame(cr2list)
    duplist=df[df.duplicated()]
    mean=cr2list.mean()
  elif file_format=="PNG":
    difflist=np.setdiff1d(rangelist,pnglist)
    df=pd.DataFrame(pnglist)
    duplist=df[df.duplicated()]
    mean=pnglist.mean()
  elif file_format=="JPG":
    difflist=np.setdiff1d(rangelist,jpglist)
    df=pd.DataFrame(jpglist)
    duplist=df[df.duplicated()]
    mean=jpglist.mean()
if difflist.size>0:
  print("")
  print("First frame: "+str(frames_start))
  print("Last frame : "+str(frames_end))
  print("Calculated number of frames: "+str((frames_end-frames_start+1)))
  print(file_format+" files:   "+str(files))
  print("Frames mean: "+str(mean))
  print("Range mean : "+str(int(rangelist.mean())))
  print("")
  if (frames_end-frames_start+1)!=files:
    print("Different number of frames than files.\n")
  else:
    print("Inconsistent numbering of frames.\n")
  for i in difflist:
    print("Missing frame:   "+str(i).rjust(numbers,"0"))
  for i in duplist.to_numpy():
    print("Duplicate frame: "+str(i[0]).rjust(numbers,"0"))
  
  print("\nProgram is terminated.\n")
  sys.exit(1)

# Select video codec or container format
print("")
while True:
    try:
        ask="Video codec or container format (h264, mkv, mp4; Default="+vformat+" <Enter>): "
        tmp=input(ask)
        if tmp=="":
            vformat="."+vformat
            break
        tmp=tmp.lower()
        if tmp in ["h264","mkv","mp4"]:
            vformat="."+tmp
            break
        raise ValueError("ValueError")
    except ValueError:
        print("Not a valid format!")
        continue
    else:
        continue

# Select project name
while True:
  try:
    defaultstr=""
    tmp=input("\nSelect project name (Default: video <Enter>): ")        
    valid_file_name = re.sub('[^\w_.)( -]', '', tmp)
    valid_file_name=valid_file_name.strip()
    if (tmp!=""):
      project_name=tmp
  except ValueError:
    print("Not a valid project name!")
    continue
  else:
    if (tmp==""):
      print("No project name selected. Default video name: video"+vformat)
      video_name="video"+vformat
      log_name="video.log"
      break
    else:
      if " " in valid_file_name:
        print("No spaces are allowed in the project name!")
        continue
      isProjectName=True
      project_name=valid_file_name
      video_name=project_name+".mkv"
      log_name=valid_file_name+".log"
      print("Project name: "+project_name)
      print("Video name  : "+video_name)
      break
    print("Select a valid project name!")
    continue

# Select Landscape or Portrait video mode
while True:
  try:
    defaultstr=""
    if isLess_or_Eq(ratiohw,1,6):
      landscape="l"
      defaultstr="Landscape"
    else:
      landscape="p"
      defaultstr="Portrait"
    tmp=input("\nSelect video mode (landscape=L, portrait=P, Default: "+defaultstr+" <Enter>): ")        
    tmp=tmp.lower()
    if (tmp!=""):
      landscape=tmp
  except ValueError:
    print("Not a valid selection!")
    continue
  else:
    if (tmp==""):
      print(defaultstr+" video mode selected")
      break
    else:
      if landscape=="l" or landscape=="p":
        break
    print("Select L or P!")
    continue

# Picture landscpe; video orintation 90°landscape => opposite geometry
# Crop: landscape
if (hn/wn<1) and (landscape=="p"):
  scoreh=int(hn*hn/wn+0.0)
  scorew=hn
  crop90=True

# Image portrait; video landscape, crop: vertical
if (hn/wn>1) and (landscape=="l"):
  scoreh=int(wn*wn/hn+0.0)
  scorew=wn 
  crop90=True

if crop90:
  xnew=scorew
  ynew=scoreh

# Select video mode
while True:
  try:
    print("\nVideo modes")
    i=0
    vmode=0
    first_mode=0
    list=[]
    for a,b,c,d,e,f in videomodes:
      na=False
      if i==0:
        if not crop90:
          if landscape=="l":
            c=wn
            d=hn
            e=str(c)+":"+str(d)
          else:
            d=wn
            c=hn
        else:
          b="V90deg"
          c=xnew
          d=ynew
          if landscape=="l":
            e=str(c)+":"+str(d)
      s="{:>2}".format(a)
      s+=" {:<8}".format(b)
      
      if landscape=="l":
        if hn>=d and wn>=c:
          if first_mode==0:
            first_mode=i
          na=False
          s2=str(c)+"x"
          s2+=str(d)
        else:
          na=True
      else:  
        if hn>=c and wn>=d:
          if first_mode==0:
            first_mode=i            
          na=False
          s2=str(d)+"x"
          s2+=str(c)
        else:
          na=True
      if not na:
        if b=="Custom":
          s2="?x?"
        l2=len(s2)
        s+=s2+" "*(12-l2)
        if landscape=="l":
          s+=str(e)
      else:
        s=""
      if not na:
        list.append(i)
        print(s)

      # Determine closest video mode
      if (i>0) and (i<maxvideomode):
        tempsw=(wn-c)/c
        tempsh=(hn-d)/d
        if landscape=="l" and (wn>=c) and (hn>=d):
          if ((tempsw>=0) and (tempsw<=0.1)) and ((tempsh>=0) and (tempsh<=0.1)):
            vmode=i
            scorew=c
            scoreh=d
        if landscape=="p" and (wn>=d) and (hn>=c):
          tempsw=(wn-d)/d
          tempsh=(hn-c)/c
          
          if ((tempsw>=0) and (tempsw<=0.1)) and ((tempsh>=0) and (tempsh<=0.1)):
            vmode=i
            scorew=d
            scoreh=c
      i=i+1
    i=i-1

    # Select it as the default mode
    question="\nSelect video mode ("
    defaultstr="Default mode is: "+str(vmode)+" = "+str(wn)+"x"+str(hn)+" <Enter>"
    if mode==0 and crop90==True:
      defaultstr="Default mode is: "+str(vmode)+" = "+str(xnew)+"x"+str(ynew)+" <Enter>"    
    tmp=input(question+defaultstr+"): ")
    if (tmp!=""):
      mode=int(tmp)
    else:
      mode=vmode
  except ValueError:
    print("Not a valid number!")
    list.clear()
    continue
  else:
    if ((mode<0)or(mode>i)):
      print("Invalid mode!\n")
      list.clear()
      continue
    if (tmp==""):
      mode=vmode
      print("Default video mode selected")
    if (mode==0):
      if not crop90:
        native_video=True
        scorew=wn
        scoreh=hn
      break
    if (mode>0) and (mode<maxvideomode) and (mode in list):
      if landscape=="l":
        scorew=videomodes[mode][2]
        scoreh=videomodes[mode][3]
      else:
        scorew=videomodes[mode][3]
        scoreh=videomodes[mode][2]
      break
    else:
      if mode==maxvideomode:
        break
      else:
        print("Not a valid selection!")
        list.clear()
        continue
    
# Select custom mode resolution
while (mode==maxvideomode):
  try:
    print("\nCustom resolution selection:")
    tmp1=input("Select width (1..."+str(wn)+")? ")
    tmp2=input("Select height (1..."+str(hn)+")? ")    
    a=int(tmp1)
    b=int(tmp2)
  except ValueError:
    print("Not a valid selection!")
    continue
  else:
    error=0
    if (a<1) or (a>wn):
      print("Width out of range!")
      error=1
    if (b<1) or (b>hn):
      print("Hight out of range!")
      error=1
    if error==1:
      continue
    scorew=a
    scoreh=b
    break

# Calculate h/w and d/c ratios
ratiohw=hn/wn
ratiodc=scoreh/scorew

# Select crop + resize (default) or only crop
while True:
  try:
    print("\nCrop & Resize or only Crop?")
    tmp=input("Select Crop & Resize or only Crop (C&R=Y, C=N, Default: C&R <Enter>): ")        
    tmp=tmp.lower()
  except ValueError:
    print("Not a valid selection!")
    continue
  else:
    if (tmp==""):
      print("C&R mode selected")
      crmode="y"
      break
    if tmp=="y":
      crmode="y"
      break
    else:
      if tmp=="n":
        crmode="n"
        break
    print("Select Y or N!")
    continue

# If C&R
if crmode=="y":
  crop=True  
  if (not isEq(hn/wn,ratiodc,6)):
    if (hn/wn>ratiodc):
      newcropmode="vertical"
      xnew=wn
      ynew=int(ratiodc*wn)
    else:
      newcropmode="horizontal"
      xnew=int(1/ratiodc*hn)
      ynew=hn    
    if (scorew>xnew) or (scorew>wn) or (xnew>wn):
      print("Warning: This selection extrapolates width of images!")
      crmode="n"
    if (scoreh>ynew) or (scoreh>hn) or (ynew>hn):
      print("Warning: This selection extrapolates height of images!")
      crmode="n"
    print("\nCrop mode:",newcropmode)
    print("Image original size:       ",wn,"x",hn)
    print("Image size before scaling: ",xnew,"x",ynew)
    if crmode=="n":
      print("Video size must be same or less than original image size.")
      print("Image extrapolation is not implemented in this program. Program terminated!")
      print("")
      sys.exit(1)
    videox=scorew
    videoy=scoreh
    print("Video size after scaling:  ",videox,"x",videoy)
  else:
    xnew=wn
    ynew=hn
    videox=scorew
    videoy=scoreh
    print("\nImage geometry is same as video geometry. No need to crop images!")
    print("Original size before scaling:",wn,"x",hn)
    print("Video size after scaling:    ",videox,"x",videoy)
    crop=False

# Crop selctions for C&R and C modes
# If only crop => calculate maximum and minimum image size for cropping
# => Print this information with final video size 
if crmode=="n":
  crop=True
  changecrop=False
  ynew=scoreh
  xnew=scorew
  xcropmin,ycropmin=getMinCropSize(xnew,ynew)
  if ratiodc<=ratiohw:
    # Vertical cropping
    xcropmax=wn
    ycropmax=int(ratiodc*xcropmax)
    newcropmode="vertical"
  else:
    ycropmax=hn
    xcropmax=int(ycropmax/ratiodc)
    newcropmode="horizontal"

  ratiominhw=ycropmin/xcropmin
  videox=scorew
  videoy=scoreh
  err=False

  if videox<=wn:
    xnew=videox
  else:
    print(videox+" (video width) > "+wn+" (picture width")
    err=True
  if videoy<=hn:
    ynew=videoy
  else:
    print(videoy+" (video height) > "+hn+" (picture height")
    err=True
  if err==True:
    print("Calculation error. Program terminateted!")
    print("")
    sys.exit(1)
  
  # Ask if the user wants to do geometry cropping
  while True:
    try:
      print("")
      print("New video crop selection?")
      print("Crop mode:               "+newcropmode)
      print("Image size:              "+str(wn)+"x"+str(hn))
      print("Video size:              "+str(xnew)+"x"+str(ynew))
      print("Minimum crop size:       "+str(xcropmin)+"x"+str(ycropmin))
      print("Maximum crop size:       "+str(xcropmax)+"x"+str(ycropmax))
      print("Minimum crop size error: "+"{:.2f}".format((ycropmin/xcropmin-ratiodc)/ratiodc*100)+" %")
      print("Maximum crop size error: "+"{:.2f}".format((ycropmax/xcropmax-ratiodc)/ratiodc*100)+" %")
      print("Picture geometry (h/w):  "+str(ratiohw))
      print("Video geometry (h/w):    "+str(ratiodc))
      print("")
      answer=input("Do you want to change crop dimension by video geometry Y/N (Default = N)? ")
      answer=answer.lower()
    except ValueError:
      print("Not a valid selection!")
      continue
    else:
      if answer=="" or answer=="n":
        print("Default crop size selected: "+str(xnew)+"x"+str(ynew))
        break
      if answer=="y":
        changecrop=True
        break
      print("\nNot a valid selection!")
      continue
  if changecrop:
    while True:
      try:
        if newcropmode=="vertical":
          tmp=input("Select a new X value ("+str(xcropmin)+"..."+str(xcropmax)+") ? ")
        else:
          tmp=input("Select a new Y value ("+str(ycropmin)+"..."+str(ycropmax)+") ? ")
        value=int(tmp)
      except ValueError:
        print("Not a valid value!")
        continue
      else:  
        if newcropmode=="vertical":
          if value<1 or value>xcropmax:
            print("Value out of range!")
            continue
          else:
            xnew=value
            ynew=int(ratiodc*xnew)
            break
        else:
          if value<1 or value>ycropmax:
            print("Value out of range!")
            continue
          else:
            ynew=value
            xnew=int(ynew/ratiodc)
            break
  if changecrop==True:
    print("New crop size is: "+str(xnew)+"x"+str(ynew))
    print("Geometry error from original crop size: "+"{:.2f}".format((ynew/xnew-ratiodc)/ratiodc*100)+" %")

# Crop section
xmarginal=wn-xnew
ymarginal=hn-ynew

# Crop geometry is not same as video geometry
if (not isEq(ratiohw,ratiodc,6)):
  list=[]
  default=0
  selection=0
  crselection=-1
  selectionOk=False
  while not selectionOk:
    try:
      if crmode=="y":
        if ymarginal>0:
          ycropmax=ymarginal
          print("\n0 = Middle crop")
          print("1 = Top crop")
          print("2 = Bottom crop")
          print("3 = Custom crop start Y (0..."+str(ycropmax-1)+")")
          crop_type=[
            "Middle crop",
            "Top crop",
            "Bottom crop",
            "Custom crop"]
        else:
          if xmarginal>0:
            xcropmax=xmarginal
            print("\n0 = Middle crop")
            print("1 = Left crop")
            print("2 = Right crop")
            print("3 = Custom crop start X (0..."+str(xcropmax-1)+")")
            crop_type=[
              "Middle crop",
              "Left crop",
              "Right crop",
              "Custom crop"]      
        list=[0,1,2,3]
        default=0        
      else:
        # crmode=="n"; only crop
        crop_type=[          
          "Top left crop",
          "Top center crop",
          "Top right crop",
          "Center left crop",
          "Center center crop",
          "Center right crop",
          "Bottom left crop",
          "Bottom center crop",
          "Bottom right crop",
          "X,Y crop"]
        print("\nCrop positions:")        
        print("123\n456\n789\n")
        if xmarginal>0 and ymarginal>0:
          print("1  = Top left crop")
          print("2  = Top center crop")
          print("3  = Top right crop")
          print("4  = Center left crop")
          print("5  = Center center crop")
          print("6  = Center right crop")
          print("7  = Bottom left crop")
          print("8  = Bottom center crop")
          print("9  = Bottom right crop")
          list=[1,2,3,4,5,6,7,8,9,10]
        else:
          if xmarginal>0 and ymarginal==0:
            print("4  = Left crop")
            print("5  = Center crop")
            print("6  = Right crop")
            list=[4,5,6,10]
          else:
            if xmarginal==0 and ymarginal>0:
              print("2  = Top crop")
              print("5  = Center crop")
              print("8  = Bottom crop")
              list=[2,5,8,10]
        print("10 = X,Y crop")
        default=5
      tmp=input("Select crop mode (Default: "+str(default)+")? ")
      if tmp!="":
        selection=int(tmp)
    except ValueError:
      print("Not a valid selection!")
      list.clear()
      continue
    else:
      if (tmp==""):
        print("Default crop mode selected")
        selection=default
      if not selection in list:
        print("Not a valid selection!")
        list.clear()
        continue
      crop_selection=selection
      selectionOk=True
      if crmode=="n":
        crop_selection-=1
      #break

    if crmode=="y" and selection==3:
      while True:
        try:
          if newcropmode=="horizontal":
            tmp=input("Select crop start X value (0..."+str(xcropmax-1)+") ? ")
          else:
            tmp=input("Select crop start Y value (0..."+str(ycropmax-1)+") ? ")
          value=int(tmp)
        except ValueError:
          print("Not a valid value!")
          continue
        else:  
          if newcropmode=="horizontal":
            if value<0 or value>xcropmax-1:
              print("Value out of range!")
              continue
            else:
              xcrop1=value
              xcrop2=wn-xmarginal+value-1
              ycrop1=0
              ycrop2=hn-1
              selection=11
              selectionOk=True
              break
          else:
            if value<0 or value>ycropmax-1:
              print("Value out of range!")
              continue
            else:
              ycrop1=value
              ycrop2=hn-ymarginal+value-1
              xcrop1=0
              xcrop2=wn-1
              selection=12
              selectionOk=True
              break

    if crmode=="n" and selection==10:
      # Ask for x and y values
      temp1=0
      temp2=0
      v1=0
      v2=0
      while True:
        try:
          if xmarginal>0:
            temp1=input("Select crop start X value (0..."+str(xcropmax-1)+") ? ")
          if ymarginal>0:
            temp2=input("Select crop start Y value (0..."+str(ycropmax-1)+") ? ")
          v1=int(temp1)
          v2=int(temp2)
        except ValueError:
          print("Crop start position is not valid!\n")
          continue
        else:
          error=False
          if xmarginal>0:
            if v1<0 or v1>xcropmax-1:
              print("X value out of range!")
              error=True
            if ymarginal>0:
              if v2<0 or v2>ycropmax-1:
                print("Y value out of range!")
                error=True
            if not error:
              xcrop1=v1
              xcrop2=wn-xmarginal+v1-1
              ycrop1=v2
              ycrop2=hn-ymarginal+v2-1
              selectionOk=True
              break
          print("")
          continue
  
  # Calculate crop area coordinates
  if crmode=="y":
    crselection=selection
    tmp=-1
    if ymarginal>0:
      if selection==1:
        # TL = Top Left
        tmp=1
      if selection==0:
        # CL = Center Left
        tmp=4
      if selection==2:
        # BL = Bottom Left
        tmp=7
    else:
      if selection==1:
        # TL = Top Left
        tmp=1
      if selection==0:
        # TC = Top Center
        tmp=2
      if selection==2:
        # TR = Top Right
        tmp=3
    selection=tmp
  if selection>0:
    if selection in [1,2,3]:
      ycrop1=0
      ycrop2=hn-ymarginal-1
    if selection in [4,5,6]:
      ycrop1=int(ymarginal/2)
      ycrop2=hn-int(ymarginal/2)-1
    if selection in [7,8,9]:
      ycrop1=ymarginal-1
      ycrop2=hn-1
    if selection in [1,4,7]:
      xcrop1=0
      xcrop2=wn-xmarginal-1
    if selection in [2,5,8]:
      xcrop1=int(xmarginal/2)
      xcrop2=wn-int(xmarginal/2)-1
    if selection in [3,6,9]:
      xcrop1=xmarginal-1
      xcrop2=wn-1
else:
  # Same geometry (image and video)
  xcrop1=0
  ycrop1=0
  xcrop2=wn-1
  ycrop2=hn-1      

while True:
  try:
    print("")
    print("Standard video frame rates: 24, 25, 30, 48, 50 and 60")
    temp=input("Select video FPS (1...60, Default=25 <Enter>): ")
    if temp!="":
      fps=int(temp)
  except ValueError:
    print("Not a valid selection!")
    continue
  else:
    error=True
    if temp=="":
      print("Default FPS selected")
      fps=25
      error=False
    if (fps<1) or (fps>60):
      print("Value out of range!")
    else:
      error=False
      if not error:
        print("\nVideo information")
        print("Frames:   "+str(files))
        print("FPS:      "+str(fps))
        print("Duration: "+str(files/fps)+" s")
        try:
          answer=input("\nSelect "+str(fps)+" frames/s (Y/N, Default: Y <Enter>): ")
          answer=answer.lower()
        except ValueError:
          print("Not a valid selection!")
          error=True
          continue
        else:
          if answer=="":
            print("Default FPS selected")
            break
          if answer=="y":
            break
          if answer=="n":
            error=True
            continue
          print("Not a valid selection!")
        continue

# Ask for Constant Rate Factor (=CRF)
# ffmpeg paramters: -rc cbr_hq -b:v 144.1M
# ffmpeg -i input.mp4 -c:v libx264 -crf 23 output.mp4

while True:
  try:
    print("")
    print("Constant Rate Factor: 0 (lossless) - 18 - 23 (default) - 28 - 51 (worst)")
    temp=input("Select video CRF for x264 (0...51, Default=23 <Enter>): ")
    if temp!="":
      crf=int(temp)
  except ValueError:
    print("Not a valid selection!")
    continue
  else:
    if temp=="":
      print("Default CRF selected")
      crf=23
      break
    if (crf<0) or (crf>51):
      print("Value out of range!")
      continue
    else:
      break

## Summary of selections ##
list_summary.append("Program version: "+version_text)
list_summary.append("")
s=""
base_name=sample[:sample_length-numbers-len(suffix)]
if project_name!="":
  s=project_name
else:
  s="video (default)"
list_summary.append("Project name: "+s)
list_summary.append("Video name:   "+video_name)
list_summary.append("")
#print(wn,hn,xnew,ynew)
if wn==xnew and hn==ynew:
  native_video=True
if native_video:
  list_summary.append("Native video mode (no cropping or resizing)")
else:
  list_summary.append("Video resolution is smaller than image size")
list_summary.append("")
if crmode=="y":
  temp="crop and resize"
else:
  temp="crop"
list_summary.append("Crop mode:                    "+temp)
if (not native_video) and crop:
  list_summary.append("Crop direction:               "+newcropmode)
  list_summary.append("Crop selection:               "+str(crop_type[crop_selection]))
  crop_coordinates="("+str(xcrop1)+","+str(ycrop1)+")-("+str(xcrop2)+","+str(ycrop2)+")"
  list_summary.append("Crop coordinates:             "+crop_coordinates)
  list_summary.append("Crop geometry error:          "+"{:.2f}".format((ynew/xnew-ratiodc)/ratiodc*100)+" %")
  list_summary.append("")
list_summary.append("Image size:                   "+str(wn)+"x"+str(hn))
if (not native_video) and crop:
  list_summary.append("Cropped image size:           "+str(xnew)+"x"+str(ynew))
list_summary.append("Video size:                   "+str(videox)+"x"+str(videoy))
list_summary.append("")
list_summary.append("Picture geometry (h/w):       "+str(ratiohw))
if (not native_video) and crop:
  list_summary.append("Cropped image geometry (h/w): "+str(ynew/xnew))
list_summary.append("Video geometry (h/w):         "+str(ratiodc))
list_summary.append("")
list_summary.append("File format:                  "+file_format)
if not native_video:
  list_summary.append("First new file name:          "+base_name+str(frames_start).rjust(numbers,"0")+".png")
list_summary.append("Last sample file name:        "+sample)
list_summary.append("Working path:                 "+current_dir)
list_summary.append("PNG path:                     "+png_path)
list_summary.append("Video and log path:           "+video_path)
list_summary.append("Video name:                   "+video_name)
list_summary.append("Log name:                     "+log_name)

# New paths: cur/png and cur/video
list_summary.append("File format digits:           "+str(numbers))
list_summary.append("First frame:                  "+str(frames_start))
list_summary.append("Last frame:                   "+str(frames_end))
list_summary.append("Calculated number of frames:  "+str((frames_end-frames_start+1)))
list_summary.append("Files:                        "+str(files))
list_summary.append("FPS:                          "+str(fps))
list_summary.append("Duration:                     "+str(files/fps)+" s")
list_summary.append("Constant Rate Factor (CRF):   "+str(crf))

sample_length=len(sample)
source_dir=current_dir
source_path=current_dir+"/"
cr2_cmd=""
png_cmd=""
mkv_cmd=""

# PNG actions:
# Native mode CR2 -> png/start_frame...end_frame
# Native mode PNG, JPG -> nothing
# Crop CR2, PNG, JPG -> png/start_frame...end_frame
# Overwrite if file exists

stage=1
if file_format=="CR2":
  # FORMAT:
  # for i in *.CR2 ; do darktable-cli "$i" source_dir/"$(basename "$i" .CR2)".png ; done
  # cr2_cmd= "for i in *"+suffix+" ; do darktable-cli \"$i\" "
  # cr2_cmd+=source_path+"\"$(basename \"$i\" "+suffix+")\".png ; done"
  
  cr2_cmd= "for i in "+source_path+"*"+cr2_suffix+" ; do darktable-cli \"$i\" "
  if project_name!="":
    cr2_cmd+=png_path+"\""+project_name+"-$(basename \"$i\" "+cr2_suffix+")\".png ; done"
  else:
    cr2_cmd+=png_path+"\"$(basename \"$i\" "+cr2_suffix+")\".png ; done"
  list_summary.append("")
  list_summary.append("Stage "+str(stage)+": CR2->PNG")
  stage+=1
  list_summary.append(cr2_cmd)

# Crop images?
png_txt=""
if (xnew<wn) or (ynew<hn):
  png_txt="Crop/resize processing"
  list_summary.append("")
  if file_format!="CR2":
    list_summary.append("Stage "+str(stage)+": "+file_format+"->PNG")
  else:
    list_summary.append("Stage "+str(stage)+": PNG->PNG")
  stage+=1
  list_summary.append(png_txt)
  input_path=png_path
else:
  # Native mode images -> native mode video (no cropping or resizing)
  # FORMAT: ffmpeg -r 30 -start_number 6894 -i IMG_%04d.png-3840.png ouput.mkv
  # ffmpeg -i input.mp4 -c:v libx264 -crf 23 -pix_fmt yuv420p output.mp4
  if file_format=="CR2":
    input_path=png_path
    suffix=".png"
  else:
    input_path=source_path

# Create video script
# FORMAT:
# ffmpeg -y -r 25 -start_number 80842 -i /home/pi/tlvimg/20190322_%06d.jpg -c:v libx264 -crf 23 -pix_fmt yuv420p /home/pi/tlvimg/video/video.mkv
mkv_cmd="ffmpeg -y -r "+str(fps)+" -start_number "+str(frames_start)+" "
mkv_cmd+="-i "+"\""+input_path
if (xnew<wn) or (ynew<hn):
  if project_name!="":
    mkv_cmd+=project_name+"-"
mkv_cmd+=base_name

mkv_cmd+="%0"+str(numbers)+"d"
if (xnew<wn) or (ynew<hn):
  mkv_cmd+=".png"
else:
  mkv_cmd+=suffix
mkv_cmd+="\" "

mkv_cmd+="-c:v libx264 "
mkv_cmd+="-crf "+str(crf)+" "
mkv_cmd+="-pix_fmt yuv420p "
mkv_cmd+="\""+video_path
if project_name!="":
  mkv_cmd+=project_name+vformat
else:
  mkv_cmd+="video"+vformat
mkv_cmd+="\""
list_summary.append("")
list_summary.append("Stage "+str(stage)+": Create video")
list_summary.append(mkv_cmd)

print("\n---------------------\n\nSummary of selections:\n")
for text in list_summary:
  print(text)

while True:
  try:
    print("")
    temp=input("Are you sure you want to proceed (Y/N, Default=Y <Enter>)? ")
    temp=temp.lower()
    if temp=="":
      temp="y"
  except ValueError:
    print("Not a valid selection!")
    continue
  else:
    if temp=="y":
      break
    if temp=="n":
      print("Video creation aborted!")
      sys.exit(1)
    continue

# Test if directories are present or can be created (png and video) #
try:
  if not os.path.exists(png_path):
    os.mkdir(png_path)
  if not os.path.exists(video_path):
    os.mkdir(video_path)
except OSError:
  print("Unable to create direcory or directories under following path: "+current_dir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

# Test if a file can be created in png and video directories
try:
  testfile="FILE-REMOVE-666.666.file"
  file1=png_path+"/"+testfile
  file2=video_path+"/"+testfile
  f1 = open(file1, "w")
  f2 = open(file2, "w")
except OSError:
    print("Unable to create file under following path(s): ")
    print(png_path)
    print(video_path)
    print("Program is terminated.")
    print("")
    sys.exit(1)
else:
  f1.close()
  f2.close()
  os.remove(file1)
  os.remove(file2)

now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")
file=open(video_path+log_name,"w")
file.write("Log created on "+dt_string+"\n\n")

for text in list_summary:
  file.write(text+"\n")

# Execute commands
stage=1
timearray=[datetime.now()]

if cr2_cmd!="":
  print("\nStage "+str(stage)+":")
  stage+=1
  os.system(cr2_cmd)
  timearray.append(datetime.now())

if png_txt!="":
  print("\nStage "+str(stage)+":")
  stage+=1
  if (xnew<wn) or (ynew<hn):
    # OpenCV crop and resize
    if file_format=="CR2":
      input_path=png_path
      suffix=".png"
    else:
      input_path=source_path
    if file_format=="PNG":
      suffix=png_suffix
    if file_format=="JPG":
      suffix=jpg_suffix
  
    path=Path(input_path)
    for p in sorted(path.iterdir()):
      if p.is_file() and p.suffix.lower()==suffix:
        fname=p.name
        try:
          image = cv2.imread(str(path)+"/"+fname)
        except:
          print("Unable to open: "+fname)
          continue
        else:
          try:
            if crop:
              image=image[ycrop1:ycrop1+ynew, xcrop1:xcrop1+xnew]
            if crmode=="y":
              image=cv2.resize(image,(videox,videoy),interpolation=inter_methods[method])
            png_out=png_path
            if isProjectName:
              png_out+=project_name+"-"
            png_out+=p.stem+".png"
            print(fname)
            cv2.imwrite(png_out,image)
          except:
            continue
  timearray.append(datetime.now())
if mkv_cmd!="":
  print("\nStage "+str(stage)+":")
  stage+=1
  os.system(mkv_cmd)
  timearray.append(datetime.now())

# Duration of different stages
for i in range(len(timearray)):
  if i==1:
    print("")
    file.write("\n")
  if i>0:
    tmp="Stage "+str(i)+" duration: "+str(timearray[i]-timearray[i-1])
    print(tmp)
    file.write(tmp+"\n")

file.close()
