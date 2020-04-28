#!/usr/bin/python3
  
import os
import sys
from pathlib import Path
from PIL import Image
from datetime import datetime
import re

def newFilename(oldname):
  newname=re.sub("\s+", "_", oldname).strip()+".png"
  return newname

# Global variables
fname=""
w=0
h=0
pictures=0

print("Pics to PNG files 1.0, (c) Kim Miikki 2019")
print("")

# Get current directory
curdir=os.getcwd()
pngdir=curdir+"/png"
path=Path(curdir)
foldername=os.path.basename(curdir)

try:
  if not os.path.exists(pngdir):
    os.mkdir(pngdir)
except OSError:
  print("Unable to create a direcory or direcories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

t1=datetime.now()
for p in sorted(path.iterdir()):
  suffix=p.suffix.lower()
  if p.is_file():
    fname=p.name
    try:
      img=Image.open(str(path)+"/"+fname)
      pixels=img.load()
      w, h=img.size
    except:
      print("No PNG conversion: "+fname)
      continue
    else:
      try:
        newname=newFilename(p.stem)
        fullpath=pngdir+"/"+newname
        img.save(fullpath)
      except:
        print("Unable to save: "+newname)
        continue
      else:
        tmp=fname+" ("+str(w)+"x"+str(h)+") -> "+newname
        print(tmp)
        pictures+=1
t2=datetime.now()

print("\nPictures converted: "+str(pictures))
print("Time elapsed:       "+str(t2-t1))

