#!/usr/bin/python3
# FPS video program for Raspberry Pi camera v. 2.x (c) Kim Miikki 2020
import os
from datetime import datetime
from rpi.inputs import *

# Calibration gains for Manfrotto Lumiemuse LEDs
awbg_red=1.6
awbg_blue=1.4
default_awb="y"
awb_on="y"
analog_gain=1.0
analog_gain_default=1.0

print("FPS video program for Raspberry Pi camera v. 2.x (c) Kim Miikki 2020\n")

print("List disk and partitions:")
os.system('lsblk')
print("\nCurrent directory:")
os.system("pwd")
path=input('\nPath to images (current directory: <Enter>): ')
name=input('Video project name: ')
if name=="":
    name="video"

# bitrate = 17000000; This is a decent default bitrate for 1080p
# MAX BITRATE MJPEG = 25000000; 25Mbits/s

# Select bitrate (default = auto (value 0) -> no bitrate parameter)
bitrate=0
while True:
    try:
        tmp=input("Select bitrate (1-25000000 bits/s, automatic: <Enter>): ")        
        bitrate=int(tmp)
    except ValueError:
        if (tmp==""):
            bitrate=0 # Bitrate parameter will not be added to raspivid command
            print("Automatic bitrate selected.")
            break
        print("Not a valid number!")
        continue
    else:
        if ((bitrate<1)or(bitrate>25000000)):
            print("Bitrate is out of range!")
            continue
        break


# Define shoot command and time variables
shootcommand=""
exposure=1
duration=1

# Select video mode & FPS from a table
mode=0 # Automatic selection (we are not going to use this)
videomodes=[
    [1,"1920x1080","16:9 Partial FOV  ",30],
    [2,"1920x1080","4:3  Full FOV     ",15],
    [3,"1920x1080","4:3  Full FOV     ",15],
    [4,"1640x1232","4:3  Full FOV     ",40],
    [5,"1640x922","16:9 Full FOV     ",40],
    [6,"1280x720","16:9 Partial FOV  ",90],
    [7,"640x480","4:3  Partial FOV  ",200],
    [8,"640x480","4:3  Partial FOV  ",180]
]

fps=0
while True:
    try:
        print("\nVideo modes")
        for a,b,c,d in videomodes:
            print(a,"\t",b,"\t",c,"\t",d)
        tmp=input("Select video mode (1...8): ")        
        mode=int(tmp)
    except ValueError:
        print("Not a valid number!")
        continue
    else:
        if ((mode<1)or(mode>8)):
            print("Invalid mode!\n")
            continue
        break
fps=videomodes[mode-1][3]

# Select different FPS: FPS_MIN...FPS (default fps)
fps_new=fps
fps_min=1
if videomodes[mode-1][0]>=6:
    fps_min=40

fps=inputValue("FPS",fps_min,fps,fps,"","FPS is out of range!",True)
frameexp=int(1000000/fps)

# Exposure unit: µs
# Exposure time must be <= 1 frame / x frame/s = 1 /x s
# Maximum exposure is 330000 µs
exposure=inputValue("exposure",1,frameexp,frameexp,"µs","Exposure is out of range!",True)

# Gain value: 1.0 to 12.0 for the IMX219 sensor on Camera Module V2
if fps>120:
    print("\nFor frame rates over 120, AWB is turned off.")
    awb_on="n"
else:
    awb_on=inputYesNo("AWB","AWB mode on",default_awb)
if awb_on=="n":
    print("")
    awbg_red=inputValue("red gain",1.0,12.0,awbg_red,"","Value out of range!",False)
    awbg_blue=inputValue("blue gain",1.0,12.0,awbg_blue,"","Value out of range!",False)

# Sets the analog gain value directly on the sensor
# (1.0 to 12.0 for the IMX219 sensor on Camera Module V2).
print("")
analog_gain=inputValue("analog gain",0.0,12.0,analog_gain_default,"","Analog gain is out of range!",False)

# int64_t lasttime
# max int64 = 9223372036854775807 
# Video maximum duration 1 y = 31536000000 ms
# Duration unit: ms
print("")
max_duration=31536000
duration=inputValue("video duration",1,max_duration,20,"s","Duration is out of range!",True)
# Change s to ms
duration=duration*1000

# Select Preview ON/OFF (default = ON
print("")
preview="n"
while True:
    try:
        tmp=input("Enable preview (Y/N, Default Y: <Enter>): ")        
        preview=str(tmp).lower()
    except ValueError:
        print("Invalid input!")
        continue
    else:
        if (preview==""):
            preview="y"
            print("Default selected: preview enabled")
            break
        if (preview=="y"):
            print("Preview enabled")
            break
        if (preview=="n"):
            print("Preview disabled")
            break
        print ("Select Y or N!")
        continue

# Convert to MKV Y/N (default = Y)
mkv="y"
while True:
    try:
        tmp=input("Convert to MKV file (Y/N, Default Y: <Enter>): ")        
        mkv=str(tmp).lower()
    except ValueError:
        print("Invalid input!")
        continue
    else:
        if (mkv==""):
            mkv="y"
            print("Default selected: MKV conversion enabled")
            break
        if (mkv=="y"):
            print("Conversion to MKV enabled")
            break
        if (mkv=="n"):
            print("Conversion to MKV disabled")
            break
        print ("Select Y or N!")
        continue

# Start recording now Y/N (default = Y)
print("")
recordnow="y"
while True:
    try:
        tmp=input("Start recording now (Y/N, Default Y: <Enter>): ")        
        recordnow=str(tmp).lower()
    except ValueError:
        print("Invalid input!")
        continue
    else:
        if (recordnow==""):
            recordnow="y"
            print("Default selected: starting to record.")
            break
        if (recordnow=="n"):
            print("Only recording commands will be shown.")
            break
        if (recordnow=="y"):
            print("Starting to record.")
            break
        print ("Select Y or N!")
        continue

# Create mode and resolution strings
mode_str="-md "
md_str=""
if (mode<8):
    mode_str+=str(mode)
    md_str=str(mode)
else:
    mode_str+=str(mode-1)
    md_str=str(mode-1)
tmp=videomodes[mode-1][1]
w_str=tmp.split('x')[0]
h_str=tmp.split('x')[1]
res_str=tmp
resolution_str="-w "+w_str+" -h "+h_str

# Create fps string
fps_str="-fps "+str(fps)

# Create exposure and duration strings
exp_str="-ss "+str(exposure)
duration_str="-t "+str(duration)

# Create bitrate string
bitrate_str=""
if (bitrate>0):
    bitrate_str="-b "+str(bitrate)

# Turn awb off if more than 120 fps
additional_params="-ag "+str(analog_gain)
if awb_on=="n":
    additional_params+=" -ex off -awb off "
    additional_params+="-awbg "+str(awbg_red)+","+str(awbg_blue)

#if fps>120:
#    additional_params="-ex off -ag 1.0 -dg 1.0 -awb off "
#    additional_params+="-awbg "+str(awbg_red)+","+str(awbg_blue)

# File name templates
# name-640x480_200fps_5000ss_20s.h264
# name-640x480_200fps_5000ss_20s.pts
# name-640x480_200fps_5000ss_20s.log
# name-640x480_200fps_5000ss_20s.rec <- raspivid terminal output
params_str=videomodes[mode-1][1]+"_"+str(fps)+"fps_"+str(exposure)+"ss_"+str(int(duration/1000))+"s"
h264_name=name+"-"+params_str+".h264"
pts_name=name+"-"+params_str+".pts"
log_name=name+"-"+params_str+".log"
rec_name=name+"-"+params_str+".rec"
mkv_name=name+"-"+params_str+".mkv"

if (path!=""):
    h264_name=path+"/"+h264_name
    pts_name=path+"/"+pts_name
    log_name=path+"/"+log_name
    rec_name=path+"/"+rec_name
    mkv_name=path+"/"+mkv_name

# Create pts and h264 strings
pts_str="-pts "+pts_name
h264_str="-o "+h264_name

# Templates for raspivid
# raspivid -md 7 -w 640 -h 480 -fps 180 -t 40000 -v -pts time.1000ss_120fps_40s.pts -ss 1000 -ag 1.0 -dg 1.0 -awb off -awbg 1,1 -o 640x480-120fps-1000ss_40s.h264 -a 512
# raspivid -md 7 -w 640 -h 480 -ss 5000 -fps 180 -t 20000 -v -pts name-640x480_200fps_5000ss_20s.pts -o name-640x480_200fps_5000ss_20s.h264
# raspivid -md 1 -w 1920 -h 1080 -ss 30000 -fps 30 -t 40000 -v -pts name-1920x1080_30fps_30000ss_40s.log -o name-1920x1080_30fps_30000ss_40s.h264
# If fps>120:
# raspivid -md 7 -w 640 -h 480 -ss 5000 -fps 180 -t 20000 >>-ex off -ag 1.0 -dg 1.0 -awb off -awbg 1.5,1.5 << -v -pts name-640x480_200fps_5000ss_20s.pts -o name-640x480_200fps_5000ss_20s.h264
#
# Add: 2>&1 | tee rec_name
# Add: Preview on or off; no preview: -n
# Add: Convert to MKV: Y/N, default No

# Build shoot command
tmp="raspivid "
if (preview=="n"):
    tmp+="-n "
tmp+=mode_str+" "
tmp+=resolution_str+" "
tmp+=exp_str+" "
tmp+=fps_str+" "
tmp+=duration_str+" "
if (awb_on=="n"):
    tmp+=additional_params+" "
tmp+="-v "
tmp+=pts_str+" "
tmp+=h264_str+" "
tmp+="2>&1 | tee "+rec_name

shootcommand=tmp

# Convert to MKV file
# Template: mkvmerge -o file.mkv file.h264
# => mkvmerge -o mkv_name h264_name
mkv_command=""
if (mkv=="y"):
    mkv_command="mkvmerge -o "+mkv_name+" "+h264_name+" "
    mkv_command+="2>&1 | tee -a "+rec_name

# Create a log file
now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")

file=open(log_name,"w")
file.write("Log created on "+dt_string+"\n\n")
if (path!=""):
    file.write("File path: "+path+"\n\n")
else:
    file.write("File path: Not defined\n\n")
file.write("Files:\n")
file.write("Video: "+h264_name+"\n")
file.write("PTS:   "+pts_name+"\n")
file.write("Log:   "+log_name+"\n")
file.write("REC:   "+rec_name+"\n\n")
file.write("FPS video parameters:\n")
file.write("Sensor mode: "+md_str+"\n")
file.write("Resolution: "+res_str+"\n")
file.write("Exposure: "+str(exposure)+" µs\n")
file.write("FPS: "+str(fps)+"\n")
file.write("Analog gain: "+str(analog_gain)+"\n")
if (awb_on=="y"):
    file.write("AWB: Auto\n")
else:
    file.write("AWB: Off\n")
    file.write("Red gain:  "+str(awbg_red)+"\n") 
    file.write("Blue gain: "+str(awbg_blue)+"\n")
file.write("Duration: "+str(int(duration/1000))+" s\n")
if (preview=="y"):
    file.write("Preview: on\n\n")
else:
    file.write("Preview: off\n\n")
file.write("Record video:\n\n")
file.write(shootcommand+"\n")
if (mkv=="y"):
    file.write("\n"+mkv_command+"\n")
file.close()

print ("\n"+shootcommand+"\n")
print (mkv_command+"\n")

if (recordnow=="y"):
    os.system(shootcommand)
    if (mkv=="y"):
        os.system(mkv_command)
