#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Sun Nov  7 19:44:36 2021

@author: Kim Miikki


'''
import argparse
import csv
import os
import sys
import numpy as np
from datetime import datetime
from pathlib import Path
from rpi.inputs2 import *
from rpi.camerainfo import *

# Initilize params
params={
    'name'      : '',
    'auto_name' : '',
    'mkv'       : '@',
    'b'         : '',
    't'         : '',   
    'ih'        : '',
    'stm'       : '',
    'md'        : '0',
    'w'         : '1920',
    'h'         : '1080',
    'g'         : '',
    'k'         : '',
    'i'         : 'pause',
    'rot'       : '',
    'fps'       : '25',
    'ss'        : '',
    'ex'        : '',
    'awb'       : '',
    'awbg'      : '',
    'ag'        : '1.0',
    'dg'        : '1.0',
    'ev'        : '',
    'p'         : '',
    'v'         : '',
    'n'         : '',
    'f'         : '',
    'pts'       : '',
    'o'         : '',
    }

# params['name']='@' <- default video name
# params['h264']='@' <- default video name

def setParams(params):
    params['name']=basename
    if isAutoName:
        params['auto_name']='@'
    params['mkv']=mkv
    params['b']=b
    params['t']=t
    params['ih']=ih
    params['stm']=stm
    params['md']=str(mode)
    params['w']=w
    params['h']=h
    params['g']=g
    params['k']=k
    params['i']=i
    params['rot']=rot
    params['fps']=fps
    params['ss']=ss
    params['ex']=ex
    params['awb']=awb
    params['awbg']=awbg
    params['ag']=ag
    params['dg']=dg
    params['ev']=ev
    params['n']=n
    params['p']=p
    params['f']=f
    params['v']=v
    params['pts']=pts
    params['o']=o

def generateParameters(params):
    result=''
    for option in params:                
        if option in ['name','auto_name','mkv']:
            continue
        s=params[option]
        if s=='':
            continue
        result+='-'+option
        if s!='@':
            result+=' '+s
        result+=' '
    result=result.strip()
    return result

def FHDplus(width,height):
    fhdResult=False
    if width==1920 and height>1080:
        fhdResult=True
    elif width>1920 and height==1080:
        fhdResult=True
    return fhdResult
    
def captureDim():
    w=-1
    h=-1

    resolution=videomodes[mode-1][1]
    resolution=resolution.strip()
    resolution=resolution.split('x')
    width=int(resolution[0])
    height=int(resolution[1])

    change=inputYesNo('resolution change','Change resolution',False)
    if change:        
        # FHD resolution question
        fhdResult=(width,height)
        if fhdResult:
            change=inputYesNo('resolution change','Use FHD resolution (1920x1080)',True)
            if change:
                w=1920
                h=1080
                return change,w,h
    else:
        return change,width,height
    
    # Ask for a new width
    ar=width/height
    maxw=width-2
    # raspivid minimum -wh and -h values: 32
    minw=round(ar*32)
    if minw // 2 == 1:
        minw+=1
    minh=32
    xstr='Enter a new even x value ('+str(minw)+'-'+str(maxw)+'): '
    while True:
        try:
            x=input(xstr)
            if x=='':
                print('Missing value!')
                continue
            elif not x.isdigit():
                print('Invalid value!')
                continue
            x=int(x)
            if x % 2 == 1:
                print('Odd number is not valid!')
                continue
            newy=int(x/ar)
            if newy % 2 == 1:
                newy+=1
            if newy<minh:
                newy=minh
            tmp='Accept the new resolution ('+str(x)+'x'+str(newy)+')'
            change=inputYesNo('resolution change',tmp,True)
            if change:
                w=x
                h=newy
                break
            #else:
            #    w=width
            #    h=height
            #break
        except:
            print('\nInvalid input')
        
    return change,w,h

# Initialize parameter variables
b=''    # bitrate=''
t=''    # interActive==False
        # frameexp='': autoexp==False
ih=''   # isTimings==True
stm=''  # isTimings==True
mode='' # mode
w=''    # w
h=''    # h
g=''    # isIntra==True 
k=''    # interActive==True
i=''    # interActive==True
rot=''  # rot
fps=''  # fps
ss=''   # autoExp==False
ex=''   # auto_exp==True
awb=''  # awb_on==False
awbg=''
ag=''
dg=''
ev=''   # ev != 0
n=''    # pmod==0
p=''    # pmod==1 or pmod==2
f=''    # pmod==3
v=''    # True
pts=''  # True
o=''    # name

#setParams(params)

options=[]
width=-1
height=-1
intra=-1

minIntra=0
maxIntra=50
defaultIntra=1

ymargin=32
xmargin=0
pip1=(1024,768)
pip2=(640,480)
pmode=-1

enableTimings=True

name=''
default_name='video'
isAutoName=True
readIni=False
writeIni=False
isVerbose=True
isFPS=False

FPSref=25

parser=argparse.ArgumentParser()
parser.add_argument('-i', action='store_true', help='Read video parameters from vrecorder.ini')
parser.add_argument('-o', action='store_true', help='Create vrecorder.ini from video parameters')
parser.add_argument('-name',nargs=1,type=str,help='video name',required=False)
parser.add_argument('-fps',type=float,help='fps value',required=False)
parser.add_argument('-ss',type=int,help='shutter speed in µs',required=False)
parser.add_argument('-awbg',type=str,help='awbg r_gain,b_gain',required=False)
args = parser.parse_args()

if args.i:
    readIni=True

if args.o:
    writeIni=True

if args.name!=None:
    name=args.name[0]

if args.ss!=None:
    ss=str(args.ss)

if args.awbg!=None:
    result=True
    awbg=args.awbg
    awbg=awbg.strip()
    if awbg.count(',')!=1:
        result=False
    pos=awbg.find(',')
    if pos==0 or len(awbg)==pos+1:
        result=False
    if result:
        rgain,bgain=awbg.split(',')
        try:
            float(rgain)
            float(bgain)
        except:
            result=False
    if not result:
        print('Illegal awbg value!')
        sys.exit(0)

def read_ini_file(filename,file_path=''):
    result=False
    if len(file_path)>0:
        filename=file_path+'/'+filename
    try:
        with open(filename,'r',newline='') as csvfile:
            csvreader=csv.reader(csvfile,delimiter=';')
            for row in csvreader:
                if row[0] in params:
                    params[row[0]]=row[1]
            result=True
    except:
        result=False
    return result

if args.fps!=None:
    try:
        fps=float(args.fps)
        isFPS=True
    except:
        print('Illegal fps value!')
        sys.exit(0)

print('Video recorder for Raspberry Pi camera module ('+camera_revision+') (c) Kim Miikki 2021')
print('')

print('Current directory:')
curdir=os.getcwd()
path=Path(curdir)
print(curdir)
print('')

ini_file_exists=False
if readIni:
    # Get the current path
    cp=Path('.').resolve()
    ini_file='vrecorder.ini'
    
    ini_file_exists=read_ini_file(ini_file)
    if ini_file_exists:
        ini_dir='current'
    else:
        # Check if roi.ini exists in parent path
        pp=cp.parent.resolve()   
        if pp!=cp:
            ini_file_exists=read_ini_file(str(pp)+'/'+ini_file)
        if ini_file_exists:
            ini_dir='parent'
    if ini_file_exists:
        print('vrecorder.ini file found in '+ini_dir+' directory:')
        # Display params
        for key in params:
            if key in ['name','auto_name','mkv']:
                continue
            s=params[key]
            if s=='':
                continue
            elif s=='@':
                print(key)
                continue
            print(key+': '+params[key])

if (not ini_file_exists) and (name==''):
    s='Video project name (Enter = video): '
    tmp=input(s)
    tmp=tmp.strip()
    if tmp=='':
        print('Default name selected')
        name=default_name
    else:
        name=tmp
    params['name']=name
elif name!='':
    params['name']=name
elif name=='':
    name=params['name']

if not ini_file_exists:
    isAutoName=inputYesNo('Auto name','Auto video name',isAutoName)
    if isAutoName:
        params['auto_name']='@'

if not ini_file_exists:    
    # Add SPS timings
    if enableTimings:
        ih='@'
        stm='@'
    
    # Select video mode & FPS from a table
    mode=0 # Automatic selection (we are not going to use this)
    fps=0
    while True:
        try:
            modes=0
            print('\nVideo modes')
            if camera_revision=='imx219':
                print('Md Resolution A/R  FOV        FPS')
            elif camera_revision=='imx477':
                print('Md Resolution A/R    FOV      FPS')
            for md,description,ar,fov,x0,y0,roi_w,roi_h,fps_min,fps_max in videomodes:
                s=str(md)+' '+description+'  '+ar+' '
                if fov==1:
                    s+='Full   '
                else:
                    s+='Partial'
                s+=' '+str(fps_min).rjust(6)+' ... '+str(fps_max)
                modes+=1
                print(s)
            tmp=input('Select video mode (1...'+str(modes)+'): ')        
            mode=int(tmp)
        except ValueError:
            print('Not a valid number!')
            continue
        else:
            if ((mode<1)or(mode>8)):
                print('Invalid mode!\n')
                continue
            break
    
    # Change capture resolution
    change,width,height=captureDim()
    w=str(width)
    h=str(height)
    
    default=FHDplus(width,height)
    
    print('')
    isIntra=inputYesNo('intra refresh modification','Intra refresh period on',default)
    if isIntra:
        tmp='key frame rate/GoP size'
        intra=inputValue(tmp,minIntra,maxIntra,defaultIntra,'','Intra refresh period is out of range!',True)
        g=str(intra)
        
    # Rotate video
    print('')
    rotationValues=[0,90,180,270]
    rot=inputListValue('rotation angle',rotationValues,0)
    if rot==0:
        rot=''
    else:
        rot=str(rot)

if isFPS:
    mode=params['md']
    try:
        mode=int(mode)
    except:
        mode=1
        params['md']=str(mode)
    fps_min=videomodes[mode-1][8]
    fps_max=videomodes[mode-1][9]
    v=args.fps
    try:
        fps=float(v)
    except:
        fps=fps_max
        params['fps']=str(fps)
    if fps>fps_max:
        fps=fps_max
        params['fps']=str(fps)
    elif fps<fps_min:
        fps=fps_min
        params['fps']=str(fps)
    if float(fps).is_integer():
        fps=str(int(fps))
    else:
        fps=str(fps)
    params['fps']=str(fps)

if (not isFPS) and (not ini_file_exists):    
    # Select the video FPS
    fps_min=videomodes[mode-1][8]
    fps=videomodes[mode-1][9]
    print("")
    fps=inputValue('FPS',fps_min,fps,fps,'','FPS is out of range!',False)

if (not ini_file_exists) or ss!='':
    # Select exposure time/frame
    # Exposure unit: µs
    auto_exp=False
    if fps=='':
        fps=params['fps']
        fps=int(fps)
    else:
        if fps<=120 and ss=='':
            print("")
            auto_exp=inputYesNo('Auto EXP','Auto EXP mode on',auto_exp)
        else:
            auto_exp=False
    min_exp=1 #imx219
    if camera_revision=='imx477':
        min_exp=250
    frameexp=int(1000000/fps)
    
    if ss!='':
        v=int(ss)
        if v<min_exp:
            ss=str(min_exp)
        elif v>frameexp:
            ss=str(frameexp)
        ex='off'
        params['ss']=str(ss)
        params['ex']=ex
    else:
        if not auto_exp:
            if frameexp>=1000:
                frameexp=round(frameexp/1000,10)
                min_exp=round(min_exp/1000,10)
                exposure=inputValue('exposure',min_exp,frameexp,frameexp,'ms','Exposure is out of range!',False)
                exposure=int(round(exposure*1000,10))
                ss=str(exposure)
                ex='off'
            else:
                exposure=inputValue('exposure',1,frameexp,frameexp,'µs','Exposure is out of range!',True)
        else:
            ex='auto'
    
if not ini_file_exists:
    # bitrate = 17000000; This is a decent default bitrate for 1080p
    # MAX BITRATE MJPEG = 25000000; 25Mbits/s
    
    # Select bitrate (default = auto (value 0) -> no bitrate parameter)
    bitrate=0
    while True:
        try:
            print("")
            tmp=input('Select bitrate (1-25000000 bits/s, automatic: <Enter>): ')        
            bitrate=int(tmp)
        except ValueError:
            if (tmp==''):
                bitrate=0 # Bitrate parameter will not be added to raspivid command
                print('Automatic bitrate selected.')
                break
            print('Not a valid number!')
            continue
        else:
            if ((bitrate<1)or(bitrate>25000000)):
                print('Bitrate is out of range!')
                continue
            break
    if bitrate>0:
        b=str(bitrate)
    
    # Select AWB or calibration values
    default_awb=True
    awb_on=True
    min_gain=0.0001
    max_gain=12.0 # imx219
    if camera_revision=='imx477':
        max_gain=8.0
    
    if fps>120:
        print('\nFor frame rates over 120, AWB is turned off.')
        awb_on=False
    else:
        print("")
        awb_on=inputYesNo('AWB','AWB mode on',default_awb)

if not ini_file_exists or awbg!='':
    if awbg!="":
        awb_on=False
        awb='off'
        params['awb']='off'
        params['awbg']=awbg
    else:
        if not awb_on:
            awbg_red=inputValue('red gain',min_gain,max_gain,awbg_red,'','Value out of range!',False)
            awbg_blue=inputValue('blue gain',min_gain,max_gain,awbg_blue,'','Value out of range!',False)
            awb='off'
            awbg=str(awbg_red)+','+str(awbg_blue)

if not ini_file_exists:    
    fps=str(fps)    
        
    # Sets the analog gain value directly on the sensor
    # (1.0 to 12.0 for the IMX219 sensor on Camera Module V2).
    analog_gain_default=1.0
    digital_gain_default=1.0
    print("")
    analog_gain=inputValue('analog gain ',1.0,12.0,analog_gain_default,'','Analog gain is out of range!',False)
    ag=str(analog_gain)
    digital_gain=inputValue('digital gain',1.0,10.0,digital_gain_default,'','Analog gain is out of range!',False)
    dg=str(digital_gain)
    
    # Set EV compensation
    print("")
    ev=inputValue('EV compensation (steps of 1/6 stop) ',-10.0,10.0,0,'','EV is out of range!',False)
    if ev != 0:
        ev=str(ev)
    else:
        ev=''
    
    # Select preview window
    pviews=[0,1,2,3]
    print('')
    print('Preview window')
    print('--------------')
    print('0 = No preview')
    print('1 = '+str(pip1[0])+'x'+str(pip1[1]))
    print('2 = '+str(pip2[0])+'x'+str(pip2[1]))
    print('3 = Full screen')
    pmod=inputListValue('preview mode',pviews,1)
    
    # Remove ymargin if aspect ratio >= 3:2
    if width/height>=3/2:
        ymargin=0
    if pmod==0:
        n='@'
    elif pmod==1:
        p=str(xmargin)+','+str(ymargin)+','+str(pip1[0])+','+str(pip1[1])
    elif pmod==2:
        p=str(xmargin)+','+str(ymargin)+','+str(pip2[0])+','+str(pip2[1])
    elif pmod==3:
        f='@'
    
    # Convert to MKV Y/N (default = Y)
    mkv=True
    while True:
        try:
            print("")
            tmp=input('Convert to MKV file (Y/N, Default Y: <Enter>): ')        
            tmp=str(tmp).lower()
        except ValueError:
            print('Invalid input!')
            continue
        else:
            if (tmp==''):
                print('Default selected: MKV conversion enabled')
                break
            if (tmp=='y'):
                print('Conversion to MKV enabled')
                break
            if (tmp=='n'):
                mkv=False
                print('Conversion to MKV disabled')
                break
            print ('Select Y or N!')
            continue
    if mkv:
        mkv='@'
    else:
        mkv=''
    params['mkv']=mkv
    
    # Select interactive video control or video duration
    print('')
    print('Video recorder control mode')
    print('---------------------------')
    isInteractive=inputYesNo('interactive','Interactive control mode on',True)
    if not isInteractive:
        # Video maximum duration 1 y = 31536000000 ms
        # Duration unit: ms
        print('')
        max_duration=31536000
        duration=inputValue('video duration',1,max_duration,20,'s','Duration is out of range!',True)
        # Change s to ms
        duration=duration*1000
        t=str(duration)
    else:
        k='@'
        i='pause'

    # Add verbose to the command
    if isVerbose:
        v='@'
      
# Generate stem name for results
if params['auto_name']=='@' and name=='':
    name=default_name
else:    
    name=params['name']

now=datetime.now()
dt_part=now.strftime('%Y%m%d-%H%M')
basename=name
params['name']=basename
if params['auto_name']=='@':    
    name+='-'+dt_part

# Generate the PTS filename
pts=name+'.pts'
params['pts']=pts

# Generate the h264 video filename
o=name+'.h264'
params['o']=o

# Generate the log filename
logname=name+'.log'

if params['mkv']=='@':
    # Generate the mkv filename
    mkvname=name+'.mkv'

# Build the rec file command
recname=name+'.rec'
rec_part='2>&1 | tee '+recname

# Build the video command
if not ini_file_exists:
    name=basename
    setParams(params)
parameters=generateParameters(params)

# Build the video recording command
record='raspivid '+parameters+' '

# Generate the vrecorder.ini file
if writeIni:
    inifile='vrecorder.ini'
else:
    inifile='vrecorder'
    inifile+='-'+dt_part
    inifile+='.ini'
with open(inifile, 'w') as f:
    writer = csv.writer(f,delimiter=';')
    for key in params.keys():
        f.write('%s;%s\n'%(key,params[key]))
 
# if non-interactive ask for start <enter>
# Start recording now Y/N (default = Y)
if params['k']=='':
    print('')
    recordnow='y'
    while True:
        try:
            tmp=input('Start recording now (Y/N, Default Y: <Enter>): ')        
            recordnow=str(tmp).lower()
        except ValueError:
            print('Invalid input!')
            continue
        else:
            if (recordnow==''):
                recordnow='y'
                print('Default selected: starting to record.')
                break
            if (recordnow=='n'):
                print('Only recording commands will be shown.')
                break
            if (recordnow=='y'):
                print('Starting to record.')
                break
            print ('Select Y or N!')
            continue    
    if recordnow=='n':
        print("")
        print("Video command:")
        print(record+rec_part)
    else:
        print("")
        print('Execute:')
        print(record+rec_part)
        os.system(record+rec_part)
else:
    print('')
    print('Execute:')
    print(record+rec_part)
    os.system(record+rec_part)

mkv_result=False
if params['mkv']=='@' and ((params['k']=='' and recordnow=='y') or params['k']=='@'):
            # Convert to MKV file
        # Template: mkvmerge -o file.mkv file.h264
        # => mkvmerge -o mkv_name h264_name
        mkv_command=''
        
        # Count frames and intervals
        data=[]
        intervals=[]
        frames=0
        for line in open(pts):
            if frames>0:
                data.append(float(line.strip()))
            frames+=1
        frames-=1
        if frames>2:
            data=np.array(data)
            diffs=data[1:]-data[:-1]
            trecord=data[-1]+diffs.mean()
            if params['t']!='':
                duration=float(params['t'])
            else:
                duration=trecord
            
            # tf = calculated time for one frame
            fps=params['fps']
            tf=round(float(fps)/FPSref*duration/frames,3)
            frame_time='--default-duration 0:'+str(tf)+'ms'
            mkv_command='mkvmerge '+frame_time+' -o '+mkvname+' '+o+' '
            mkv_command+='2>&1 | tee -a '+recname
            print('')
            print('Execute:')
            print(mkv_command+'\n')
            os.system(mkv_command)
            mkv_result=True
        else:
            print("Not enough frames for MKV creation.")

# Write a log file
results=[]
at=datetime.now()
results.append("vrecorder.py log file")
results.append("")
results.append("Log created on "+str(at))
results.append("")
results.append("Current directory:")
results.append(curdir)
results.append("")
results.append("Files:")
results.append("")
results.append(o)
results.append(pts)
if mkv_result:
    results.append(mkvname)
results.append(recname)
results.append(logname)
results.append("")
results.append("Commands:")
results.append("")
results.append(record+rec_part)
if mkv_result:
    results.append(mkv_command)
results.append("")

arguments=[]
for item in dir(args):
    if len(item)>0:
        if item[0]=="_":
            continue
    v=""
    if item=='awbg':
        if args.awbg==None:
            continue
        else:
            v=args.awbg
    elif item=='ss':
        if args.ss==None:
            continue
        else:
            v=str(args.ss)
    elif item=='fps':
        if args.fps==None:
            continue
        else:
            if (args.fps).is_integer():
                v=str(int(args.fps))
            else:
                v=str(args.fps)
    elif item=='i':
        if not readIni:
            continue
    elif item=='o':
        if not writeIni:
            continue
    elif item=='name':
        if args.name==None:
            continue
        else:
            v=str(args.name[0])
    if len(v)>0:
        v=" "+v
    arguments.append("-"+item+v)

results.append("Arguments:")
if len(arguments)>0:
    results.append("")
    for item in arguments:
        results.append(item)

if mkv_result:
    results.append("")
    results.append("Statistics:")
    results.append("----------")
    results.append("Frames    : "+str(frames))
    results.append("Time      : "+str(round(trecord/1000,1))+" s")
    results.append("Frame mean: "+str(tf)+" ms")


# Save the log file
with open (logname,"w") as f:
    for line in results:
        f.write(line+"\n")
