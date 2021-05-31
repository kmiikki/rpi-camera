#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 12 08:34:19 2021

@author: Kim Miikki

"""

import argparse
import cv2
import os
import sys
import math
import numpy as np 
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import MaxNLocator
from pathlib import Path
from scipy.signal import savgol_filter
from scipy.signal import find_peaks
from rpi.inputs2 import *

autopeaks=False
datafiles=False
calibration=False
view=False
saveall=False
save=True
patch=False
der_given=False
fname=""
parent=""
stem=""
ch=0
inverse=False
linew1=0.2
linew2=0.4
dpi=300
delimiter=","

# Savgol parameters
polyorder=2
window_default=11
window_max=101
derivative=2    # Allowed values: 1 or 2

# Relative minimum peak size
minp=0.15

# Default unit and maximum digts of the calibration value
cal_width=0
cal_height=0
cal_dev=0
cal_tolerance=0.05  # Calibration tolerance
xyl_tolerance=0.05  # X and Y length tolerance
ssq_tolerance=0.02  # Solid square tolerance
unit="mm"

def deviation(a,b):
    mean=(a+b)/2
    distance=a-mean
    return distance/mean

def error(value,mean):
    return (value-mean)/value


# Round a value with a specified number of digits
def roundval(value,digits):
    v=0
    dec=0
    if value==0:
        return 0
    d=math.log10(abs(value))

    if d<=0:
        dec=digits+int(abs(d))
    elif d>0 and d<(digits-1):
        dec=digits+int((-d-1))
    elif d>=(digits-1):
        dec=0

    if dec>0:
        v=round(value,dec)
    else:
        v=round(value)
    return v

def windowsize(start,end,w,h,default):
    # Window size must be an odd number
    # size > polyorder
    # Minumum value is 3
    # Maximum < (w/4 and h/4)
    
    # Fix start and end values
    if start<=polyorder:
        start=polyorder+1
    if start%2==0:
        start=int(start+1)
    if start<3:
        start=3
    if end%2==0:
        end=int(end+1)
    if end<=start:
        end=start+2
    if default<start:
        default=start
    
    # Calculate maximum value
    if w>=h:
        maximum=int(h/4)
    else:
        maximum=int(w/4)
    if maximum%2==0:
        maximum-=1
    if end<maximum:
        maximum=end
        if maximum%2==0:
            maximum-=1
    end=maximum
    if end==start:
        return start
    elif end<start:
        return -1
    
    while True:
        try:
            win=input("Select window size (odd number "+str(start)+"-"+str(end)+"; Default="+str(default)+"): ")
            if win=="":
                win=default
                print("default selected")
                break
            win=int(win)
            if win<start or win>end:
                print("Selection is out of range!")
                continue
            if win%2==0:
                print(str(win)+" is an even number!")
                continue
            break
        except:
            print("Invalid selection!")
    return win
        
def uniquepeaks(lpeaks,rpeaks):
    lpeaks=lpeaks.tolist()
    rpeaks=rpeaks.tolist()    
    i=0
    lefts=[]
    rights=[]
    while i<len(lpeaks):
        if lpeaks[i] in rights:
            break
        lefts.append(lpeaks[i])
        if rpeaks[-1-i] in lefts:
            break
        rights.append(rpeaks[-1-i])
        i+=1
    return lefts,rights

def defaultpeaks(lpeaks,rpeaks,der,derivative):
    peaks=[]
    if derivative<1 or derivative>2:
        return peaks
    if derivative==1:
        sign=-1
    else:
        sign=1
    if len(lpeaks)<1:
        return peaks
    elif len(rpeaks)<1:
        return peaks
    peaks.append(lpeaks[0])
    # Search from right opposite signed second derivative
    # Search from right equal signed second derivative
    for i in sorted(rpeaks,reverse=True):
        if sign*der[peaks[0]]<0:
            if der[i]<0:
                peaks.append(i)
                return peaks
        else:
            if der[i]>0:
                peaks.append(i)
                return peaks
    if len(peaks)==1:
        peaks.append(sorted(rpeaks,reverse=True)[-1])
    return peaks

print("Calibration and length measurement utility, (C) Kim Miikki 2021")
print("")

# Read and parse program arguments
parser=argparse.ArgumentParser()
parser.add_argument("file", type=Path, help="calibration or analysis image")
parser.add_argument("-d", action="store", dest="d", type=int, help="Savitzky-Golay derivative: 1 or 2")
parser.add_argument("-a", action="store_true", help="auto peak selection")
parser.add_argument("-c", action="store_true", help="calibration mode")
parser.add_argument("-o", action="store_true", help="save all files")
parser.add_argument("-n", action="store_true", help="saving of graphs disabled")
parser.add_argument("-p", action="store_true", help="plot calibration graphs on screen")
parser.add_argument("-s", action="store_true", help="save data files")
parser.add_argument("-t", action="store_true", help="save patch image")
args = parser.parse_args()

if args.d:
    if args.d not in [1,2]:
        print("Only 1st or 2nd derivative is allowed. Argument usage: NONE, -d 1 or -d 2")
        print("Default derivative is: "+str(derivative))
        sys.exit(0)
    derivative=args.d
    der_given=True
if args.a:
    autopeaks=True
if args.s:
    datafiles=True
if args.c:
    calibration=True    
if args.n:
    save=False
if args.p:
    view=True
if args.t:
    patch=True
if args.o:
    if save==False:
        # Override argument -n
        print("Argument -n overridden with -o. All files are saved.\n")
        patch=True
        save=True
    saveall=True

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
if curdir!="/":
    curdir+="/"
print("Current directory:")
print(path)
print("")

if os.path.isfile(args.file):
    stem=args.file.stem
    fname=str(args.file.name)
    parent=str(args.file.parent)
else:
    print("File "+str(args.file)+" not found!")
    sys.exit(0)

if parent=="":
    parent=curdir

try:
    # Load a calibration image
    tmp=parent
    if tmp=="/":
        tmp=""
    img=cv2.imread(tmp+"/"+fname,cv2.IMREAD_UNCHANGED)
except:
    print("Unable to open "+fname+"!")
    sys.exit(0)

if img is None:
    print("Not a valid calibration image: "+fname)
    sys.exit(0)

if len(img.shape)==3:
    if img.shape[2]==3:
        
        
        ch=3
    h,w,ch=img.shape
elif len(img.shape)==2:
    ch=1
    h,w=img.shape

if not ch in [1,3]:
    print(fname+" does not have 1 or 3 color channels. Program is terminated.")
    sys.exit(0)

# Get direactional means of mean channel values
if ch==3:
    ## Convert color image to grayscale and get directional means
    #imgbw=np.mean(img,axis=2)
    #xxs=imgbw.mean(axis=0)
    #yxs=imgbw.mean(axis=1)
    xxs=img.mean(axis=0).mean(axis=1)
    yxs=img.mean(axis=1).mean(axis=1)

# get directional means when ch==1
if ch==1:
    xxs=img.mean(axis=0)
    yxs=img.mean(axis=1)

# Select 2nd or 1st derivative
if not der_given:
    if derivative==2:
        der2_default=True
    else:
        der2_default=False
    der2sel=inputYesNo("2nd derivative mode","Use Savitzky-Golay 2nd derivative",der2_default)
    if der2sel:
        derivative=2
    else:
        derivative=1

# Default window width 11 or 21: 3- (odd number)
window=windowsize(3,window_max,w,h,window_default)

# Minimum peak height
minp=inputValue("minimum peak relative height:",0.01,1.0,minp,"","Relative height is out of range!",False)


if w<2*window or h<2*window:
    print("Too small image. Program is terminated.")
    sys.exit(0)

# Find peaks with default settings
start_peaks=4
end_peaks=4
lpeaks=[]
rpeaks=[]
cpeaks=[]
hpeaks=[]
der_arrays=[]
i=0
for ar in [xxs,yxs]:
    if i==0:
        xlabel="X coordinate"
        d="x"
    else:
        xlabel="Y coordinate"
        d="y"
    der = savgol_filter(ar, window_length=window, polyorder=polyorder, deriv=derivative)
    xdata=abs(der)
    maxh=xdata.max()
    minh=xdata.min()
    midh=(maxh-minh)/2
    # Find peaks from the array
    peaks,properties=find_peaks(xdata,height=maxh*minp)
    lpeaks.append(peaks[:start_peaks])
    rpeaks.append(peaks[-end_peaks:])
    cpeaks.append(len(peaks))
    hpeaks.append(properties["peak_heights"])
    der_arrays.append(der)

    fig=plt.figure()
    plt.plot(der,linewidth=linew2)
    plt.xlim(0,len(der))
    plt.xlabel(xlabel)
    if derivative==1:
        plt.ylabel("1st derivative")
    else:
        plt.ylabel("2nd derivative")
    if save or saveall:
        # xder or yder = x/y direction, (color analysis) derivative 1 or 2
        plt.savefig(curdir+d+"cader"+str(derivative)+"-"+stem+".png", dpi=300)
    if view:
        plt.show()
    plt.close(fig)
    
    # Generate smooth graphs
    smooth=savgol_filter(ar, window_length=window, polyorder=2)
    fig=plt.figure()
    plt.plot(smooth,linewidth=linew2)
    plt.xlim(0,len(smooth))
    plt.xlabel(xlabel)
    plt.ylabel("Smoothed grayscale mean value")
    if save or saveall:
        # x/y direction, (color analysis) savgol
        plt.savefig(curdir+d+"casg-"+stem+".png", dpi=300)
    if view:
        plt.show()
    plt.close(fig)
    
    fig=plt.figure()
    minh=ar.min()
    maxh=ar.max()
    plt.plot(ar,color="r",linewidth=linew2)
    plt.vlines(peaks,minh,maxh,color="k",linewidth=linew1)
    plt.xlim(0,len(der))
    plt.xlabel(xlabel)
    plt.ylabel("Grayscale mean value")
    if save or saveall:
        # xcap or ycap =x/y direction color analysis peaks
        plt.savefig(curdir+d+"cap-"+stem+".png", dpi=300)
    if view:
        plt.show()
    plt.close(fig)
    # Save data files
    if datafiles or saveall:
        # ypeaks,xpeaks,xdata,ydata
        coordinates=np.arange(0,len(ar))
        a=np.array([coordinates,ar,der]).T
        header=d.upper()+" coordinate, Grayscale value, "
        if derivative==1:
            header+="1st derivative"
        else:
            header="2nd derivative"
        np.savetxt(curdir+d+"data-"+stem+".csv", a, delimiter=delimiter, header=header, fmt=["%d", "%f", "%f"])
    i+=1

# Adjust start and end peaks
rps=rpeaks[0]
lps=lpeaks[0]
tps=rpeaks[1]
bps=rpeaks[1]

if cpeaks[0]<2 or cpeaks[1]<2:
    print("Too few peaks. The program is terminated.")
    sys.exit(0)

# Ask for outer peaks
peak_l=-1
peak_r=-1
peak_t=-1
peak_b=-1

# List Left peaks in X direction
digits=4
vdigits=1

lps,rps=uniquepeaks(lpeaks[0],rpeaks[0])
p=defaultpeaks(lps,rps,der_arrays[0],derivative)
if len(p)==2:
    peak_l=p[0]
    peak_r=p[1]
if not autopeaks:
    if len(lps)>1:
        print("X direction, L peaks (left):")
        print("pos     der"+str(derivative)+"     value  default")
        i=0
        while i<len(lps):
            s=str(lps[i]).rjust(5)
            s+=": "
            s+=str(round(der_arrays[0][lps[i]],digits)).rjust(digits+4)
            s+="  "
            s+=str(round(xxs[lps[i]],vdigits)).rjust(5)
            if lps[i]==peak_l:
                s+="x".rjust(6)
            print(s)
            i+=1
        peak_l=inputListValue("left peak position",lps,peak_l,"Not a valid peak value!")
        if len(p)==2:
            i=lps.index(peak_l)
            p=defaultpeaks(lps[i:],rps,der_arrays[0],derivative)
            peak_r=p[1]
   
# List Right peaks in X direction
if not autopeaks:
    if len(lps)>1:
        print("")
        print("X direction, R peaks (right):")
        print("pos     der"+str(derivative)+"     value  default")
        i=0
        while i<len(rps):
            s=str(rps[i]).rjust(5)
            s+=": "
            s+=str(round(der_arrays[0][rps[i]],digits)).rjust(digits+4)
            s+="  "
            s+=str(round(xxs[rps[i]],vdigits)).rjust(5)
            if rps[i]==peak_r:
                s+="x".rjust(6)
            i+=1
            print(s)
        peak_r=inputListValue("right peak position",rps,peak_r,"Not a valid peak value!")


# List Left peaks in Y direction (Top)
tps,bps=uniquepeaks(lpeaks[1],rpeaks[1])
p=defaultpeaks(tps,bps,der_arrays[1],derivative)
if len(p)==2:
    peak_t=p[0]
    peak_b=p[1]
if not autopeaks:
    if len(tps)>1:
        print("")
        print("Y direction, L peaks (top):")
        print("pos     der"+str(derivative)+"     value  default")
        i=0
        while i<len(tps):
            s=str(tps[i]).rjust(5)
            s+=": "
            s+=str(round(der_arrays[1][tps[i]],digits)).rjust(digits+4)
            s+="  "
            s+=str(round(yxs[tps[i]],vdigits)).rjust(5)
            if tps[i]==peak_t:
                s+="x".rjust(6)
            i+=1
            print(s)
        peak_t=inputListValue("top peak position",tps,peak_t,"Not a valid peak value!")
        if len(p)==2:
            i=tps.index(peak_t)
            p=defaultpeaks(tps[i:],bps,der_arrays[1],derivative)
            peak_b=p[1]    

# List Right peaks in X direction (Bottom)
if not autopeaks:
    if len(bps)>1:
        print("")
        print("Y direction, R peaks (bottom):")
        print("pos     der"+str(derivative)+"     value  default")
        i=0
        while i<len(rps):
            s=str(bps[i]).rjust(5)
            s+=": "
            s+=str(round(der_arrays[1][bps[i]],digits)).rjust(digits+4)
            s+="  "
            s+=str(round(yxs[bps[i]],vdigits)).rjust(5)
            if bps[i]==peak_b:
                s+="x".rjust(6)
            i+=1
            print(s)
        peak_b=inputListValue("bottom peak position",bps,peak_b,"Not a valid peak value!")
    
# Statistical calculations
x_center=round((peak_r+peak_l)/2)
x_centerv=xxs[x_center]
x_minv=xxs[peak_l:peak_r].min()
x_maxv=xxs[peak_l:peak_r].max()
x_base_meanv=(xxs[peak_l]+xxs[peak_r])/2
x_meanv=xxs[peak_l:peak_r].mean()
if x_meanv<=x_base_meanv:
    x_type="minimum"
else:
    x_type="maximum" 

y_center=round((peak_t+peak_b)/2)
y_centerv=yxs[y_center]
y_minv=yxs[peak_t:peak_b].min()
y_maxv=yxs[peak_t:peak_b].max()
y_base_meanv=(yxs[peak_t]+yxs[peak_b])/2
y_meanv=yxs[peak_t:peak_b].mean()
if y_meanv<=y_base_meanv:
    y_type="minimum"
else:
    y_type="maximum"

# Rectangle and circle coordinates
xy=(peak_l,peak_t)
xw=peak_r-peak_l
xc=(peak_l+peak_r)/2
yh=peak_b-peak_t
yc=(peak_t+peak_b)/2
xy_circle=(xc,yc)
r_circle=np.mean([xw,yh])/2
s_square=np.mean([xw,yh])
x0_square=xc-s_square/2
y0_square=yc-s_square/2

print("")
if calibration:
    print("- Length calibration mode -")
else:
    print("- Length measurement mode -")
    
tmp=input("Calibration length unit (Default=mm): ")
if tmp!="":
    unit=tmp

saveRect=False
saveCircle=False
isSSQ=False
isCir=False
    
# Measurement mode
if not calibration:
    saveRect=True
    while True:
        try:
            cal=input("Calibration value (pixels/"+unit+"): ")
            cal=float(cal)
            break
        except:
            print("Invalid value!")
    width=(peak_r-peak_l)/cal
    height=(peak_b-peak_t)/cal
    print("")
    print("Width : "+str(roundval(width,5))+" "+unit)
    print("Height: "+str(roundval(height,5))+" "+unit)

# Calibration mode
else:
    while True:
        try:
            hlength=input("Horizontal length ("+unit+"): ")
            hlength=float(hlength)
            if hlength<=0:
                print("A positive value is required.")
                continue
            break
        except:
            print("Invalid value!")    
    while True:
        try:
            vlength=input("Vertical length ("+unit+"; Default="+str(hlength)+"): ")
            if vlength=="":
                vlength=hlength
                print("default selected")
                break
            vlength=float(vlength)
            if vlength<=0:
                print("A positive value is required.")
                continue
            break
        except:
            print("Invalid value!")
    cal_width=(peak_r-peak_l)/hlength
    cal_height=(peak_b-peak_t)/vlength
    cal_mean=(cal_width+cal_height)/2
    cal_dev=deviation(cal_height,cal_width)
    print("")
    print("Horizontal calibration value: "+str(roundval(cal_width,5))+" pixels/"+unit)
    print("Vertical calibration value  : "+str(roundval(cal_height,5))+" pixels/"+unit)
    if abs(cal_dev)<cal_tolerance:
        print("\nEqual calibration values within "+str(cal_tolerance)+" tolerance: "+str(roundval(cal_dev,3)))
        print("Mean calibration value: "+str(roundval(cal_mean,5))+" pixels/"+unit+"\n")
        
        ## Determine if solid square
        isSSQ=True
        
        # Circle is also ok
        isCir=True
        
        # Test X and Y length deviation
        dev_lengths=abs(deviation(xw,yh))
        dlen=roundval(dev_lengths,3)
        if dev_lengths>xyl_tolerance:
            print("Color analysis distance tolerance exceeded : "+str(dlen)+" > "+str(xyl_tolerance))
            isSSQ=False
            isCir=False
        else:
            print("Color analysis distance tolerance subceeded: "+str(dlen)+" < "+str(xyl_tolerance))
        
        # Test maximum/minimum and mean deviation
        if x_type=="maximum":
            errx=abs(error(x_maxv,x_meanv))
        else:
            errx=abs(error(x_minv,x_meanv))
        if y_type=="maximum":
            erry=abs(error(y_maxv,y_meanv))
        else:
            erry=abs(error(y_minv,y_meanv))
            
        if errx>ssq_tolerance or erry>ssq_tolerance:
            errx=roundval(errx,3)
            erry=roundval(erry,3)
            if errx>ssq_tolerance:
                print("X direction solid square tolerance exceeded: "+str(errx)+" > "+str(ssq_tolerance))
            else:
                print("X direction solid square test passed       : "+str(errx)+" > "+str(ssq_tolerance))
            if erry>ssq_tolerance:
                print("Y direction solid square tolerance exceeded: "+str(erry)+" > "+str(ssq_tolerance))
            isSSQ=False
        if True in [saveall,patch,view]:
            if isSSQ:
                default="square"
                sel=inputYesNo("square patch","Use square patch",True)
                if sel:
                    saveRect=True
                else:
                    saveCircle=True        
            else:
                sel=inputYesNo("circle patch","Use circle patch",True)
                if sel:
                    saveCircle=True
                else:
                    saveRect=True        
    else:
        print("\nDeviation of X and Y calibration values exceeded tolerance: "+str(roundval(cal_dev,3))+" > "+str(cal_tolerance))
        saveRect=True

# Save a log file
now = datetime.now()
dt_string = now.strftime("%Y.%m.%d-%H:%M:%S")
file=open(curdir+stem+".log","w")
file.write("calen.py log file"+"\n\n")
file.write("Log created on "+dt_string+"\n\n")

# Store used arguments
tmp=""
d=vars(args)
tmp+=str(d["file"])
tmp+=" "
for key in d:
    if len(key)==1 and d[key]:
        tmp+="-"+key+" "
tmp.strip()
file.write("Program arguments: "+tmp+"\n\n")

if (path!=""):
    file.write("Analysis directory: "+str(path)+"\n\n")
else:
    file.write("File path: Not defined\n\n")
file.write("Image parameters\n")
file.write("Image name    : "+fname+"\n")
file.write("Image width   : "+str(w)+"\n")
file.write("Image height  : "+str(h)+"\n")
file.write("Color channels: "+str(ch)+"\n\n")

file.write("Savitzky-Golay filter parameters\n")  
file.write("Polynomial order: "+str(polyorder)+"\n")
file.write("Derivative      : "+str(derivative)+"\n")
file.write("Window length   : "+str(window)+"\n\n")

file.write("Peak find parameters\n")
file.write("Minimum relative height: "+str(minp)+"\n\n")

file.write("Peak X directional analysis\n")
file.write("---------------------------\n")
file.write("peaks count    : "+str(cpeaks[0])+"\n")
file.write("height mean    : "+str(roundval(hpeaks[0].mean(),5))+"\n")
file.write("height minimum : "+str(roundval(hpeaks[0].min(),5))+"\n")
file.write("height maximum : "+str(roundval(hpeaks[0].max(),5))+"\n\n")

file.write("start peak     : "+str(peak_l)+"\n")
file.write("start value    : "+str(roundval(xxs[peak_l],5))+"\n\n")

file.write("center peak    : "+str(x_center)+"\n")
file.write("center value   : "+str(roundval(x_centerv,5))+"\n\n")

file.write("end peak       : "+str(peak_r)+"\n")
file.write("end value      : "+str(roundval(xxs[peak_r],5))+"\n\n")

file.write("width          : "+str(peak_r-peak_l)+"\n\n")
file.write("min value      : "+str(roundval(x_minv,5))+"\n")
file.write("max value      : "+str(roundval(x_maxv,5))+"\n")
file.write("base mean value: "+str(roundval(x_base_meanv,5))+"\n")
file.write("extremum type  : "+x_type+"\n\n")

file.write("Peak Y directional analysis\n")
file.write("---------------------------\n")
file.write("peaks  count   : "+str(cpeaks[1])+"\n")
file.write("height mean    : "+str(roundval(hpeaks[1].mean(),5))+"\n")
file.write("height minimum : "+str(roundval(hpeaks[1].min(),5))+"\n")
file.write("height maximum : "+str(roundval(hpeaks[1].max(),5))+"\n\n")

file.write("start peak     : "+str(peak_t)+"\n")
file.write("start value    : "+str(roundval(yxs[peak_b],5))+"\n\n")

file.write("center peak    : "+str(y_center)+"\n")
file.write("center value   : "+str(roundval(y_centerv,5))+"\n\n")

file.write("end peak       : "+str(peak_b)+"\n")
file.write("end value      : "+str(roundval(yxs[peak_b],5))+"\n\n")

file.write("height         : "+str(peak_b-peak_t)+"\n\n")
file.write("min value      : "+str(roundval(y_minv,5))+"\n")
file.write("max value      : "+str(roundval(y_maxv,5))+"\n")
file.write("base mean value: "+str(roundval(y_base_meanv,5))+"\n")
file.write("extremum type  : "+y_type+"\n\n")

# Calibration mode section
if calibration:
    file.write("Calibration mode\n")
    file.write("----------------\n")
    file.write("Unit             : "+unit+"\n")
    if float(hlength).is_integer():
        hlength=int(hlength)
    if float(vlength).is_integer():
        vlength=int(vlength)
    # Equalize the length of hlen and vlen strings
    hstr=str(hlength)
    vstr=str(vlength)
    hlen=len(hstr)
    vlen=len(vstr)
    if hlen>=vlen:
        tmp=hlen
    else:
        tmp=vlen
    file.write("Horizontal length: "+str(hlength).rjust(tmp)+"\n")
    file.write("Vertical length  : "+str(vlength).rjust(tmp)+"\n\n")
    file.write("Horizontal calibration value: "+str(roundval(cal_width,5))+" pixels/"+unit+"\n")
    file.write("Vertical calibration value  : "+str(roundval(cal_height,5))+" pixels/"+unit+"\n")

    # Test calibration tolerance
    if abs(cal_dev)<cal_tolerance:
        file.write("\nEqual calibration values within "+str(cal_tolerance)+" tolerance: "+str(roundval(cal_dev,3))+"\n")
        file.write("Mean calibration value: "+str(roundval(cal_mean,5))+" pixels/"+unit+"\n\n")
               
        # Test X and Y length deviation
        if dev_lengths>xyl_tolerance:
            file.write("Color analysis distance tolerance exceeded : "+str(dlen)+" > "+str(xyl_tolerance)+"\n")
        else:
            file.write("Color analysis distance tolerance subceeded: "+str(dlen)+" < "+str(xyl_tolerance)+"\n")
        
        # Test maximum and base deviation
        if errx>ssq_tolerance:
            file.write("X direction solid square tolerance exceeded: "+str(errx)+" > "+str(ssq_tolerance)+"\n")
        else:
            file.write("X direction solid square test passed       : "+str(errx)+"\n")
        if erry>ssq_tolerance:
            file.write("Y direction solid square tolerance exceeded: "+str(erry)+" > "+str(ssq_tolerance)+"\n")
        else:
            file.write("Y direction solid square test passed       : "+str(erry)+"\n")
    else:
        file.write("\nDeviation of X and Y calibration values exceeded tolerance: "+str(roundval(cal_dev,3))+" > "+str(cal_tolerance)+"\n")

# Analysis mode section
if not calibration:
    file.write("Analysis mode\n")
    file.write("-------------\n")
    file.write("Calibration value: "+str(cal)+" pixels/"+unit+"\n\n")
    file.write("Width : "+str(roundval(width,5))+" "+unit+"\n")
    file.write("Height: "+str(roundval(height,5))+" "+unit+"\n")

file.close()

# Save a patched image with coordinates
if True in [saveall,patch,view]:
    if saveRect or saveCircle:
        if calibration:
            tmp="patchcal-"
            fcolor="g"
            if dev_lengths>xyl_tolerance:
                fcolor="b"
        else:
            tmp="patch-"
            fcolor="r"
        
        # Create an image with coordinates
        fig=plt.figure()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_plot=plt.imshow(img)  
    
        # Get the current reference
        ax = plt.gca()
        
        if saveRect:
            if calibration and (isSSQ or dev_lengths<xyl_tolerance):
                # Create a Square patch
                rect = plt.Rectangle((x0_square,y0_square),s_square,s_square,facecolor=fcolor,alpha=0.25)
            else:            
                # Create a Rectangle patch
                rect = plt.Rectangle(xy,xw,yh,linewidth=1,facecolor=fcolor,alpha=0.25)
            ax.add_patch(rect)
        else:
            # Create a Circle patch
            cir=plt.Circle(xy_circle,r_circle,facecolor=fcolor,alpha=0.25)
            ax.add_artist(cir)
        
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        if True in [patch,save,saveall]:
            print("")
            print("Saving: "+tmp+stem+".png")
            plt.savefig(curdir+tmp+stem+".png", dpi=300)
        if view:
            plt.show()
        plt.close(fig)
