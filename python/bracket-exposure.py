#!/usr/bin/python3
# Exposure bracketing program for Raspberry Pi camera v. 2.x (c) Kim Miikki 2019
import os
from datetime import datetime
from rpi.inputs import *

print("Exposure bracketing program for Raspberry Pi camera v. 2.x (c) Kim Miikki 2020\n")
quality_default=90
artist=""
artistfile="artist.txt"

quality_default=90
quality=inputValue("image quality",1,100,quality_default,"","Quality is out of range!",True)

print("\nList disk and partitions:")
os.system('lsblk')
print("\nCurrent directory:")
os.system("pwd")
path=input('\nPath to images (current directory: <Enter>): ')
name=input('Exposure bracketing name (default=exp: <Enter>): ')
if name=="":
    name="exp"

iso=100
iso_default=100
iso_modes=[100,200,320,400,500,640,800]
iso=inputListValue("ISO",iso_modes,iso_default,"Not a valid ISO value!",False)
print("")

try:
    f=open(artistfile,"r")
    artist=f.readline()
    artist=artist.strip()
    print("Artist: "+artist)
    f.close()
except IOError:
    artist=""

# Create a log file
logname=""
if (path!=""):
    logname=path+"/"
logname+=name+"_iso"+str(iso)+".log"

now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")

file=open(logname,"w")
file.write("Log created on "+dt_string+"\n\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")
file.write("Exposure bracketing parameters:\n")
file.write("Quality: "+str(quality)+"\n")
file.write("ISO value: "+str(iso)+"\n\n")
file.write("Shoot commands:\n\n")

# Create a list of microsecond exposures
exposure=list()
filenames=list()
shootcommand=list()
exposure = [
    1,
    5,
    10,
    25,
    50,
    100,
    200,
    350,
    500,
    750,
    1000,
    2000,
    3500,
    5000,
    7500,
    10000,
    15000,
    20000,
    35000,
    50000,
    100000,
    150000,
    200000,
    250000,
    300000,
    330000
]

# Genereate file names and shoot commands
# Template:
#
# raspistill -n -t 1 -ISO 100 -q 10 -ss 20000 -bm -drc high
# -x IFD0.Artist="" -x IFD0.Copyright=""
# -o test123.jpg

i=0
for time in exposure:
    timestr=str(exposure[i])
    timestr=timestr.rjust(6,'0')

    fname=name+"_iso"+str(iso)+"_"+timestr+".jpg"
    filenames.append(fname)

    tmp="raspistill -n -t 1 -ISO "+str(iso)+" "
    tmp+="-q "
    tmp+=str(quality)+" "
    tmp+="-ss "+timestr+" "
    tmp+="-bm -drc high "
    if artist!="":
        tmp+='-x IFD0.Artist="'+artist+'" '
        tmp+='-x IFD0.Copyright="'+artist+'" '
    if (path!=""):
        tmp+='-o '+path+'/'+fname
    else:
        tmp+='-o '+fname
    shootcommand.append(tmp)
    i=i+1

i=0
for picture in shootcommand:
    print(picture)
    os.system(picture)
    file.write(picture+"\n")
    i=i+1

file.close()
