#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 10 18:05:32 2021

@author: Kim Miikki

Mandatory files (input/output):
rgbmap-DT.pkl
rgbmap-b-gains-DT.csv
rgbmap-r-gains-DT.csv

Mandatory files (output):
rgbmap-cal-DT.txt
rgbmap-mdist-DT.png

where DT="YYYYMMDD-hhmmss"
"""
import argparse
import os
import sys
import csv
import pickle
import cv2
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import picamera.array
from time import sleep
from rpi.camerainfo import *
from rpi.roi import *
from rpi.inputs2 import *

version=2.2

# Camera settings
exposure=20000 # µs
exp_mode="off"
awb_mode="off"
iso=100
width=320
height=240
pip=(0,0,width,height)

# R and B gains ranges
rs=[0.5,8]
r_step=0.5
bs=[0.5,8]
b_step=0.5
decimals=10
rgb_decimals=3

# Interactive values
red_gain_start=0.0001
red_gain_min=rs[0]
red_gain_max=rs[1]
red_step=1

blue_gain_start=0.0001
blue_gain_min=bs[0]
blue_gain_max=bs[1]
blue_step=1

rmap=[]
gmap=[]
bmap=[]
bwmap=[]
rlist=[]
blist=[]

pklfile=""
pkllist=[]
pklfiles=0
dt_part=""
curdirPrinted=False
auto_calibration=False
precision_scan=False
precision_scan_wide=False
previewImage=True
file_mode=False
interactive=True
all_files=True
short_dtstr=False
quick_calibration=False
isIteration=False
method="Calibration"

results=[]
# adir = analysis dir: "" in capture mode, "%Y%m%d-%H%M%S" in file_mode
adir=""
red=1.0
blue=1.0
gains_RGB=[]
distances_min=[]
cal_number=0

def analyze_data(count=0,max_count=0):    
    global results
    global red,blue
    global gains_RGB
    global distances_min
    global cal_number

    cal_number+=1
    pklname="rgbmap-"+dt_part+".pkl"
    
    print("")
    print("Analyzing data",end="")
    if file_mode:
        if count>0:
            print(" "+str(count)+"/"+str(max_count))
        else:
            print("")
    else:
        print(" "+str(count))
    at0=datetime.now()
    # Flatten RGB maps
    isMin=False
    rvals=np.array(rmap).ravel()
    gvals=np.array(gmap).ravel()
    bvals=np.array(bmap).ravel()
    rg=abs(rvals-gvals)
    rb=abs(rvals-bvals)
    gb=abs(gvals-bvals)
    mdist=(rg+rb+gb)/3
    mmin=mdist.min()
    mmax=mdist.max()
    mmean=mdist.mean()
    mvar=mdist.var()
    mmedian=np.median(mdist)
    # Get an array from the tuple
    mpos=list(np.where(mdist==mmin))[0]
    # Select first element from the array
    if len(mpos>0):
        mpos=mpos[0]
        isMin=True
        rindex=mpos // len(blist)
        bindex=mpos % len(blist)
        red=rlist[rindex]
        blue=blist[bindex]
        rmean=rmap[rindex][bindex]
        gmean=gmap[rindex][bindex]
        bmean=bmap[rindex][bindex]
        gains_RGB.append([cal_number,red,blue,rmean,gmean,bmean,rg[mpos],rb[mpos],gb[mpos],mmean])
        
        # Camera section
        # --------------
        if not file_mode:
            # Capture a sample picture
            camera.awb_gains=(red,blue)
            with picamera.array.PiRGBArray(camera) as output:
                camera.capture(output,"rgb")
                cv2.imwrite("rgbmap-cal-image-"+dt_part+".png",np.array(output.array))
                output.truncate(0)
    else:
        print("Index of minimum distance not found!")
        print("mmin: "+str(mmin))
    
    # Add the minimal distance to a list
    distances_min.append(mmin)
    
    # Save data in pickle format
    data=np.dstack((rmap,gmap,bmap,bwmap))
    with open(adir+pklname,"wb") as f:
        pickle.dump(data,f)
    
    # Write R and B gain ranges to files
    with open(adir+"rgbmap-r-gains-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(rlist)
    with open(adir+"rgbmap-b-gains-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(blist)
    
    if all_files:
        # Write R, G, B channel data to files
        with open(adir+"rgbmap-r-"+dt_part+".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(rmap)
        with open(adir+"rgbmap-g-"+dt_part+".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(gmap)
        with open(adir+"rgbmap-b-"+dt_part+".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(bmap)
        with open(adir+"rgbmap-bw-"+dt_part+".csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(bwmap)
    
        # Save R,G ,B channel data to gray scale image files
        fig=plt.figure()
        plt.title("Red mean response")
        plt.ylabel("Red gain")
        plt.xlabel("Blue gain")
        plt.imshow(rmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
        plt.gca().invert_yaxis()
        plt.savefig(adir+"rgbmap-r-im-"+dt_part+".png",dpi=300)
        plt.close(fig)
        
        fig=plt.figure()
        plt.title("Green mean response")
        plt.ylabel("Red gain")
        plt.xlabel("Blue gain")
        plt.imshow(gmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
        plt.gca().invert_yaxis()
        plt.savefig(adir+"rgbmap-g-im-"+dt_part+".png",dpi=300)
        plt.close(fig)
        
        fig=plt.figure()
        plt.title("Blue mean response")
        plt.ylabel("Red gain")
        plt.xlabel("Blue gain")
        plt.imshow(bmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
        plt.gca().invert_yaxis()
        plt.savefig(adir+"rgbmap-b-im-"+dt_part+".png",dpi=300)
        plt.close(fig)
        
        fig=plt.figure()
        plt.title("Gray mean response")
        plt.ylabel("Red gain")
        plt.xlabel("Blue gain")
        plt.imshow(bwmap,"gray",extent=[blist[0],blist[-1],rlist[-1],rlist[0]])
        plt.gca().invert_yaxis()
        plt.savefig(adir+"rgbmap-bw-im-"+dt_part+".png",dpi=300)
        plt.close(fig)
    
    if isMin:
        ctext="["+str(rindex)+","+str(bindex)+"]"
        
        # Create a RGB mean distance plot
        fig=plt.figure()
        plt.title("RGB mean distance")
        plt.ylabel("Distance")
        plt.xlabel("Index number")
        plt.xlim(0,len(mdist)-1)
        plt.plot(mdist)
        plt.plot(mpos,mmin,marker="o",mec="r",mfc="red")
        plt.text(mpos,mmin,ctext)
        plt.savefig(adir+"rgbmap-mdist-"+dt_part+".png",dpi=300)
        plt.close(fig)
        
        if all_files:
            with open(adir+"rgbmap-mdist-"+dt_part+".csv", "w") as f:
                writer = csv.writer(f)
                writer.writerow(mdist)
    
    at1=datetime.now()
    
    if isMin:    
        results.append("")
        tmp="Mode: "
        if not file_mode:
            tmp+="capture and "
        tmp+="analyze"
        results.append(tmp)
        results.append("Time: "+str(at1))
        results.append("")
        if not file_mode:
            results.append("Capture time: "+str(ct1-ct0))
        results.append("Analyze time: "+str(at1-at0))
        results.append("")
        if not file_mode:
            results.append("Shutter speed: "+str(exposure)+" µs")
            results.append("")
        results.append("Calibration")
        results.append("-----------")
        results.append("Red gain : "+str(rlist[rindex]))
        results.append("Blue gain: "+str(blist[bindex]))
        results.append("Minimal distance: "+str(round(mmin,rgb_decimals)))
        results.append("")
        results.append("Red and blue gains")
        results.append("-------------------")
        results.append("R gain min : "+str(round(red_gain_min,decimals)))
        results.append("R gain max : "+str(round(red_gain_max,decimals)))
        results.append("R gain step: "+str(round(r_step,decimals)))
        results.append("")
        results.append("B gain min : "+str(round(blue_gain_min,decimals)))
        results.append("B gain max : "+str(round(blue_gain_max,decimals)))
        results.append("B gain step: "+str(round(b_step,decimals)))    
        results.append("")
        results.append("Matrix   : "+str(len(rlist))+"x"+str(len(blist)))
        results.append("Position : "+ctext)
        results.append("Index    : "+str(mpos))
        results.append("")
        results.append("RGB values")
        results.append("----------")
        results.append("R: "+str(rmean))
        results.append("G: "+str(gmean))
        results.append("B: "+str(bmean))
        results.append("")
        results.append("Distance distribution")
        results.append("---------------------")
        results.append("N     : "+str(len(mdist)))
        results.append("Min   : "+str(round(mmin,rgb_decimals)))
        results.append("Max   : "+str(round(mmax,rgb_decimals)))
        results.append("Mean  : "+str(round(mmean,rgb_decimals)))
        results.append("Median: "+str(round(mmedian,rgb_decimals)))
        results.append("Var   : "+str(round(mvar,rgb_decimals)))
    
        # Print calibration results
        for line in results:
            print(line)
    
        # Save calibration results
        with open (adir+"rgbmap-cal-"+dt_part+".txt","w") as f:
            f.write("Mapgains Log File\n")
            for line in results:
                f.write(line+"\n")

        results=[]

print("Mapgains - Map Raspberry Pi gamera gains and calibration")
print("Version: "+str(version))
print("(C) Kim Miikki 2021")
print("")

parser=argparse.ArgumentParser()
parser.add_argument("-f", type=Path, help="file mode: read rgbmap-YYYYMMDD-hhmm.pkl")
parser.add_argument("-a", action="store_true", help="auto, non-interactive mode")
parser.add_argument("-c", action="store_true", help="auto calibration")
parser.add_argument("-q", action="store_true", help="quick calibration")
parser.add_argument("-p", action="store_true", help="precision scan")
parser.add_argument("-pw", action="store_true", help="precision scan wide")
parser.add_argument("-d", action="store_true", help="disable image preview")
parser.add_argument("-n", action="store_true", help="do not create all analysis files")
parser.add_argument("-s", action="store_true", help="use short date-time string")
parser.add_argument("-i", action="store_true", help="x axis label: Iteration")
args = parser.parse_args()

if args.f:
    pklfile=args.f
    error=False
    if pklfile.is_dir():
        print(str(pklfile)+" is not a valid filename!")
        error=True
    elif not pklfile.exists():
        print(str(pklfile)+" does not exist!")
        error=True
    if error:
        sys.exit(1)
    if (pklfile.parent != pklfile.name) and not (str(pklfile.parent) == "."):
        os.chdir(pklfile.parent)
        print("Current directory set to: "+str(pklfile.parent))
        pklfile=pklfile.name
        curdirPrinted=True
    pklfile=str(pklfile)
    file_mode=True

if args.a:
    interactive=False

if args.c:
    auto_calibration=True

if args.q:
    quick_calibration=True

if args.p:
    precision_scan=True
    auto_calibration=True

if args.pw:
    precision_scan=True
    precision_scan_wide=True
    auto_calibration=True

if args.d:
    previewImage=False

if args.n:
    all_files=False

if args.s:
    short_dtstr=True

if args.i:
    isIteration=True

if file_mode and auto_calibration:
    print("File mode and auto calibration are not allowed simultaneously.")
    sys.exit(0)
    
if precision_scan and True in [file_mode,quick_calibration]:
    print("Presicion scan must run without any of following arguments: -f and -q.")
    sys.exit(0)
    
if not file_mode:
    # ROI
    roi_result=validate_roi_values()
    if roi_result:
        display_roi_status()
        print("")

if not curdirPrinted:
    print("Current directory:")
    curdir=os.getcwd()
    path=Path(curdir)
    print(curdir)
    print("")

now=datetime.now()
now_stack=now

# Execute only one time
if file_mode:
    short_sample="rgbmap-20211024-1521.pkl"
    long_sample ="rgbmap-20211024-152145.pkl"
    len_short=len(short_sample)
    len_long=len(long_sample)
    
    pklExists=False
    for p in sorted(path.iterdir()):
        if not pklExists:
            if str(p.name) == pklfile:
                print("PKL files found:")
                pklExists=True
        if pklExists:    
            suffix=p.suffix.lower()
            if suffix != ".pkl":
                continue
            if short_dtstr and (len(p.name) != len_short):
                continue
            if (not short_dtstr) and (len(p.name) != len_long):
                continue
            if len(p.name) != len(pklfile):
                continue
            pkllist.append(str(p.name))
            pklfiles+=1
            print(p)

    # Change analysis dir    
    adir=now.strftime("%Y%m%d-%H%M%S")+"/"
    try:
        if not os.path.exists(adir):
            os.mkdir(adir)
    except OSError:
        print("Unable to create a directory or directories under following path:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)

if file_mode:
    count=0
    for pklfile in pkllist:
        # Templates:
        # rgbmap-20211014-1639.pkl
        # rgbmap-20211014-163959.pkl
        # dt (short):   4+2+2+1+4 + ext: 4 = 17 
        # dt (default): 4+2+2+1+6 + ext: 4 = 19
        if short_dtstr:
            dt_part=(pklfile[-17:])[:-4]
        else:
            dt_part=(pklfile[-19:])[:-4]
            
        # Read data
        with open(pklfile,"rb") as f:
            data=pickle.load(f)
            
        # Check data.shape and pklfile length
        error=False
        x=0
        y=0
        z=0
        error=False
        try:
            y,x,z=data.shape
            if x==0 or y==0:
                print("Incorrect table size: ("+str(x)+","+str(y)+")")
                error=True
            if z!=4:
                print("Incorrect number of layers (4 required): "+str(z))
                error=True
        except:
            print("Invalid data shape in the pickle file.")
            error=True
        if error:
            sys.exit(1)
        
        rmap=data[:,:,0]
        gmap=data[:,:,1]
        bmap=data[:,:,2]        
        bwmap=data[:,:,3]
    
        ## Read R and B gain ranges from files
        try:
            with open("rgbmap-r-gains-"+dt_part+".csv", "r") as f:
                reader = csv.reader(f)
                rlist=next(reader)
            rlist=list(np.array(rlist).astype(float))
        except:
            print("rgbmap-r-gains-"+dt_part+".csv not found!")
            sys.exit(1)
        try:
            with open("rgbmap-b-gains-"+dt_part+".csv", "r") as f:
                reader = csv.reader(f)
                blist=next(reader)
            blist=list(np.array(blist).astype(float))
        except:
            print("rgbmap-b-gains-"+dt_part+".csv not found!")
            sys.exit(1)
    
        # Check gain lists lengths
        error=False
        if y!=len(rlist):
            print("R gain list length mismatch with data rows")
            error=True
        if x!=len(blist):
            print("B gain list length mismatch with data columns")
            error=True
        if error:
            sys.exit(1)

        # Calculate ranges and steps
        red_gain_min=min(rlist)
        red_gain_max=max(rlist)
        r_step=round((rlist[-1]-rlist[0])/(len(rlist)-1),10)

        blue_gain_min=min(blist)
        blue_gain_max=max(blist)
        b_step=round((blist[-1]-blist[0])/(len(rlist)-1),10)
        
        count+=1
        analyze_data(count,pklfiles)
       
elif True in [interactive,auto_calibration,precision_scan]:
    if interactive or precision_scan:
        if camera_revision=="imx477":
            exp_min=250
        elif camera_revision=="imx219":
            exp_min=1
        exp_max=camera_max_exposure
        exp_default=exposure
        exposure=inputValue("exposure time",exp_min,exp_max,exp_default,"µs","Exposure is out of range!",True)
        print("")
    
    if not auto_calibration:
        # Red gain range and step
        red_gain_min=inputValue("red gain min",red_gain_start,red_gain_max,red_gain_min,"","Gain out of range!",False)
        if red_gain_max<red_gain_min:
            red_gain_max=red_gain_min
        red_gain_max=inputValue("red gain max",red_gain_min,red_gain_max,red_gain_max,"","Gain out of range!",False)
        red_max_step=round(red_gain_max-red_gain_min,10)
        if red_max_step<red_step:
            red_step=red_max_step
        if red_max_step==0.0:
            print("Red gain min and max are equal. Red step auto adjusted to 1.0.")
            red_step=1.0
        else:
            red_step=inputValue("red gain step",red_gain_start,red_max_step,red_step,"","Step out of range!",False)
        print("")
    
        # Blue gain range and step
        blue_gain_min=inputValue("blue gain min",blue_gain_start,blue_gain_max,blue_gain_min,"","Gain out of range!",False)
        if blue_gain_max<blue_gain_min:
            blue_gain_max=blue_gain_min
        blue_gain_max=inputValue("blue gain max",blue_gain_min,blue_gain_max,blue_gain_max,"","Gain out of range!",False)
        blue_max_step=round(blue_gain_max-blue_gain_min,3)
        if blue_max_step<blue_step:
            blue_step=blue_max_step
        if blue_max_step==0.0:
            print("Blue gain min and max are equal. Blue step auto adjusted to 1.0.")
            blue_step=1.0
        else:
            blue_step=inputValue("blue gain step",blue_gain_start,blue_max_step,blue_step,"","Step out of range!",False)
    else:
        if not precision_scan:
            # Auto calibration: round 1 values
            red_step=r_step
            red_gain_min=red_step
            blue_step=b_step
            blue_gain_min=blue_step
        else:
            # Precision scan
            if not precision_scan_wide:
                rstep=0.001
                rmin=0.01
                rmax=7.99
            else:
                rstep=0.01
                rmin=0.1
                rmax=7.9
            rdefault=1
            red_target=inputValue("red gain target",rmin,rmax,rdefault,"","Gain out of range!",False)
            red_gain_min=round(red_target-10*rstep,10)
            if red_gain_min<=0:
                red_gain_min=rstep
            red_gain_max=round(red_target+10*rstep,10)
            red_step=rstep
            
            if not precision_scan_wide:
                bstep=0.001
                bmin=0.01
                bmax=7.99
            else:
                bstep=0.01
                bmin=0.1
                bmax=7.9
            bdefault=1
            blue_target=inputValue("blue gain target",bmin,bmax,bdefault,"","Gain out of range!",False)
            blue_gain_min=round(blue_target-10*rstep,10)
            if blue_gain_min<=0:
                blue_gain_min=bstep
            blue_gain_max=round(blue_target+10*bstep,10)
            blue_step=bstep

if not file_mode:
    from picamera import PiCamera

    #print("")
    print("Capture mode")
    print("")
    
    if not roi_result:
        roi_x0=0.5-width/(2*camera_maxx)
        roi_y0=0.5-height/(2*camera_maxy)
        roi_w=width/camera_maxx
        roi_h=height/camera_maxy
    zoom=(roi_x0,roi_y0,roi_w,roi_h)
        
    # Set camera options
    camera=PiCamera(resolution=(width,height))
    camera.iso=iso
    if previewImage:
        camera.start_preview(fullscreen=False,window=pip)
    # Wait for the automatic gain control to settle
    sleep(2)
    # Now fix the values
    camera.exposure_mode=exp_mode
    camera.awb_mode=awb_mode
    camera.shutter_speed=int(exposure)
    camera.zoom=zoom

    rdivisor=10
    bdivisor=10
    target_decimals=4
    cur_decimals=0
    if precision_scan:
        if not precision_scan_wide:
            cur_decimals=3
        else:
            cur_decimals=2
    if auto_calibration:
        method="Iteration"
    while (cur_decimals<target_decimals+1):
        ct0=datetime.now()
        if str(red_step).find(".")>=0:
            rdecimals=len(str(red_step))-(str(red_step).rfind(".")+1)
        else:
            rdecimals=0
        if str(blue_step).find(".")>=0:
            bdecimals=len(str(blue_step))-(str(blue_step).rfind(".")+1)
        else:
            bdecimals=0
        # Template 1.34, 1.56:
        gainlen=2+rdecimals+2+2+bdecimals+1
        # Template: 128.nnn
        chlen=4+rgb_decimals       
        
        # Set rgain and bgain ranges
        rs=[red_gain_min,red_gain_max]
        r_step=red_step
        bs=[blue_gain_min,blue_gain_max]
        b_step=blue_step
    
        # Create R and B gains lists
        rlist=list(np.linspace(rs[0],rs[1],round((rs[1]-rs[0])/r_step+1)))
        rlist=[round(num,decimals) for num in rlist]
        blist=list(np.linspace(bs[0],bs[1],round((bs[1]-bs[0])/b_step+1)))
        blist=[round(num,decimals) for num in blist]
        
        i=0
        rmap=[]
        gmap=[]
        bmap=[]
        bwmap=[]
        print(method+" "+str(cal_number+1))
        print("")
        header="rg, bg:".ljust(gainlen," ")+"  "
        header+="red".rjust(chlen," ")+"  "
        header+="green".rjust(chlen," ")+"  "
        header+="blue".rjust(chlen," ")+"  "
        header+="distance".rjust(chlen," ")
        print(header)
        idata=[]
        with picamera.array.PiRGBArray(camera) as output:            
            for red in rlist:
                rl=[]
                gl=[]
                bl=[]
                bwl=[]
                for blue in blist:
                    camera.awb_gains=(red,blue)
                    camera.capture(output,"rgb")
                    # output.array.shape: (240, 320, 3)
                    rgb_means=np.array(output.array).mean(axis=(0,1))
                    r_avg=round(rgb_means[0],rgb_decimals)
                    g_avg=round(rgb_means[1],rgb_decimals)
                    b_avg=round(rgb_means[2],rgb_decimals)
                    bw_avg=round(rgb_means.mean(),rgb_decimals)
                    dist=(abs(r_avg-g_avg)+abs(r_avg-b_avg)+abs(g_avg-b_avg))/3
                    i+=1
                    # Create print string
                    # Template: 1.90, 1.81: 123.456  111.111    2.222  123.345
                    out=format(red,"."+str(rdecimals)+"f")
                    out+=", "
                    out+=format(blue,"."+str(bdecimals)+"f")
                    out+=":"
                    out=out.ljust(7," ")
                    out+="  "
                    out+=format(r_avg,"."+str(rgb_decimals)+"f").rjust(chlen," ")+"  "
                    out+=format(g_avg,"."+str(rgb_decimals)+"f").rjust(chlen," ")+"  "
                    out+=format(b_avg,"."+str(rgb_decimals)+"f").rjust(chlen," ")+"  "
                    out+=format(dist,"."+str(rgb_decimals)+"f").rjust(chlen+1," ")
                    print(out)
                    idata.append(out)
                    rl.append(r_avg)
                    gl.append(g_avg)
                    bl.append(b_avg)
                    bwl.append(bw_avg)
                    output.truncate(0)
                rmap.append(rl)
                gmap.append(gl)
                bmap.append(bl)
                bwmap.append(bwl)
        ct1=datetime.now()
        if short_dtstr:
            dt_part=ct0.strftime("%Y%m%d-%H%M")
        else:
            dt_part=ct0.strftime("%Y%m%d-%H%M%S")
        with open(adir+"rgbcal-iteration-"+dt_part+".txt", "w") as f:
            for row in idata:
                f.writelines(row+"\n")
        analyze_data(cal_number+1,pklfiles)
        if (cal_number==1) and (not precision_scan):
            # Adjust step for round 2
            red_step=1
            blue_step=1
        
        if not auto_calibration:
            break
        
        cur_decimals+=1
        if quick_calibration:
            fdiv=2
        else:
            fdiv=1
        red_gain_min=red-red_step/fdiv
        red_gain_max=red+red_step/fdiv
        blue_gain_min=blue-blue_step/fdiv
        blue_gain_max=blue+blue_step/fdiv
        if red_gain_min<=0:
            red_gain_min=red_step/rdivisor
            red_gain_max=red+red_step
        if blue_gain_min<=0:
            blue_gain_min=blue_step/bdivisor
            blue_gain_max=blue+blue_step
        if red_gain_max>8:
            red_gain_max=8
            red_gain_min=red-red_step
        if blue_gain_max>8:
            blue_gain_max=8
            blue_gain_min=blue-blue_step
        red_step/=rdivisor
        blue_step/=bdivisor

        print("")
                        
    camera.close()

# Prepare series data
now=now_stack
gains_RGB=np.round(gains_RGB,10)

# Save calibration series data to a csv file
if len(gains_RGB)>0:
    with open(adir+"rgbcals-data-"+dt_part+".csv", "w") as f:
        writer = csv.writer(f)
        header=["Iteration","rgain","bgain","R mean","G mean","B mean","ABS(RG)","ABS(RB)","ABS(GB)","mdist"]
        writer.writerow(header)
        writer.writerows(gains_RGB)
    
# Plot calibration series data plots
if len(gains_RGB)>1:    
    xlabel="Iteration"
    if file_mode and (not isIteration):
        xlabel="Calibration"
    gains_RGB=np.array(gains_RGB).T
    cal_min=gains_RGB[0].min()
    cal_max=gains_RGB[0].max()

    # Create a calibration series gains plot
    fig=plt.figure()
    plt.title("Red and blue gains")
    plt.ylabel("Gain value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],gains_RGB[1],color="red")
    plt.plot(gains_RGB[0],gains_RGB[2],color="blue")
    plt.grid()
    plt.savefig(adir+"rgbcals-gains-"+dt_part+".png",dpi=300)
    plt.close(fig)    

    fig=plt.figure()
    plt.title("Red gain")
    plt.ylabel("Gain value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],gains_RGB[1],color="red")
    plt.grid()
    plt.savefig(adir+"rgbcals-rgain-"+dt_part+".png",dpi=300)
    plt.close(fig)    

    fig=plt.figure()
    plt.title("Blue gain")
    plt.ylabel("Gain value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],gains_RGB[2],color="blue")
    plt.grid()
    plt.savefig(adir+"rgbcals-bgain-"+dt_part+".png",dpi=300)
    plt.close(fig)    

    # Create a calibration series RGB mean value plot
    fig=plt.figure()
    plt.title("RGB mean values")
    plt.ylabel("RGB mean value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    ymin=min([gains_RGB[3].min(),gains_RGB[4].min(),gains_RGB[5].min()])
    ymax=max([gains_RGB[3].max(),gains_RGB[4].max(),gains_RGB[5].max()])
    plt.ylim(ymin,ymax)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],gains_RGB[3],color="red")
    plt.plot(gains_RGB[0],gains_RGB[4],color="green")
    plt.plot(gains_RGB[0],gains_RGB[5],color="blue")
    plt.grid()
    plt.savefig(adir+"rgbcals-rgb-"+dt_part+".png",dpi=300)
    plt.close(fig)    

    # Create a calibration series for ABS(RG), ABS(RB) and ABS(GB)
    fig=plt.figure()
    plt.title("RGB mean absolute distances")
    plt.ylabel("RGB mean absolute distance value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    ymin=min([gains_RGB[6].min(),gains_RGB[7].min(),gains_RGB[8].min()])
    ymax=max([gains_RGB[6].max(),gains_RGB[7].max(),gains_RGB[8].max()])
    plt.ylim(ymin,ymax)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],gains_RGB[6],color="y",label="ABS(RG)") # RG: yellow
    plt.plot(gains_RGB[0],gains_RGB[7],color="m",label="ABS(RB)") # RB: magenta
    plt.plot(gains_RGB[0],gains_RGB[8],color="c",label="ABS(GB)") # BG: cyan
    plt.legend (loc=2)
    plt.grid()
    plt.savefig(adir+"rgbcals-rgbdist-"+dt_part+".png",dpi=300)
    plt.close(fig)    
    
     # Create a calibration series for ABS(gray)
    fig=plt.figure()
    plt.title("Gray mean absolute distance")
    plt.ylabel("Gray mean absolute distance value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    ymin=gains_RGB[9].min()
    ymax=gains_RGB[9].max()
    plt.ylim(ymin,ymax)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],gains_RGB[9],color="k") # RG: yellow
    plt.grid()
    plt.savefig(adir+"rgbcals-graydist-"+dt_part+".png",dpi=300)
    plt.close(fig)    

     # Create a minimum distances plot
    fig=plt.figure()
    plt.title("Minimal distance")
    plt.ylabel("Minimal distance value")
    plt.xlabel(xlabel)
    plt.xlim(cal_min,cal_max)
    ymin=min(distances_min)
    ymax=max(distances_min)
    plt.ylim(ymin,ymax)
    plt.gca().xaxis.set_major_locator(mticker.MultipleLocator(1))
    plt.plot(gains_RGB[0],distances_min,color="k") # RG: yellow
    plt.grid()
    plt.savefig(adir+"rgbcals-mindist-"+dt_part+".png",dpi=300)
    plt.close(fig)
