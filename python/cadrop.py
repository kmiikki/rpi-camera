#!/usr/bin/env python3
# coding: utf-8

"""
Created on 2020-09-29

@authors: Kim Miikki and Alp Karakoc

Arguments:
-f measurements/01_ss4000_0001.png -res 255 -base 690 -t 5 -roi 160,,1150, -d tl4 -bp 10 -wp 220 -gamma 1.5 -fs 30
-res 255 -base 690 -t 5 -roi 160,,1150, -d ptfe/last_frames -bp 10 -wp 220 -gamma 1.5 -fs 30 -n
-res 255 -base 690 -t 5 -roi 160,,1150, -d ptfe/last_frames -bp 10 -wp 220 -gamma 1.5 -fs 30 -n -s 4920

"""
import argparse
import pathlib
import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import os
import sys
from pathlib import Path

# Global variables
res=0
base=0
tl_start=0
t=0
in_bp=0
in_wp=255
in_gamma=1.0
is_dir=False
interactive=False
path=""
file_base=""
file_type=""
file_digits=0
file_sample=""
file_w=0
file_h=0
jpg_file_base=""
png_file_base=""
jpg_sample=""
png_sample=""
apply_levels=False
apply_roi=False
show_figures=True

#THRESHOLD FOR DENOISING GO TILL ELIMINATION OF SMALL PIXELS
filter_strength=13.0

def levels(image,black_point,white_point,gamma=1.0):
    inBlack  = np.array([black_point,black_point,black_point],dtype=np.float32)
    inWhite  = np.array([white_point,white_point,white_point],dtype=np.float32)
    inGamma  = np.array([gamma, gamma, gamma], dtype=np.float32)
    outBlack = np.array([0, 0, 0], dtype=np.float32)
    outWhite = np.array([255, 255, 255], dtype=np.float32)
    
    image = np.clip((image - inBlack) / (inWhite - inBlack), 0, 255)
    image = (image ** (1/inGamma)) * (outWhite - outBlack) + outBlack
    image = np.clip(image, 0, 255).astype(np.uint8)
    return image

def get_sample_numbers(s=""):
  numbers=0
  l=len(s)
  if (l<=4):
    print("Picture name(s) is too short! Program is terminated.")
    print("")
    sys.exit(1)
  else:
    s=s[0:l-4]
  # Count numbers from end of the string
  l=len(s)
  i=l-1
  while(i>=0):
    if not s[i:l].isdigit():
      break
    i=i-1
    numbers+=1
  if (numbers<1):
    print("Picture name ("+s+") is not valid! Program is terminated.")
    print("")
    sys.exit(1)
  return numbers


print("Contact angle analysis for sessile drops")
print("")

curdir=os.getcwd()
figuresdir=curdir+"/figures"
path=Path(curdir)
print("Current directory:")
print(curdir)
print("")
try:
  if not os.path.exists(figuresdir):
    os.mkdir(figuresdir)
except OSError:
  print("Unable to create a directory or directories under following path:\n"+curdir)
  print("Program is terminated.")
  print("")
  sys.exit(1)

parser=argparse.ArgumentParser()
parser.add_argument("-f", nargs="?", type=pathlib.Path, help="path to a drop image",required=False)
parser.add_argument("-d", nargs="?", type=pathlib.Path, help="path to a drop images directory (overrides file argument)",required=False)
parser.add_argument("-res",type=int,help="resolution as integer: px/mm",required=True)
parser.add_argument("-base",type=int,help="basline y coordinate as integer",required=True)
parser.add_argument("-s",type=float,help="start time for first frame as float",required=False)
parser.add_argument("-t",type=float,help="interval between 2 consequent frames (>0 s) as float",required=False)
parser.add_argument("-roi", nargs=1, type=str,
                    help="region of interest (ROI) as integer coordinates: x0,y0,x1,y1",required=False)
parser.add_argument("-bp",type=float,help="black point (0...255) as integer",required=False)
parser.add_argument("-wp",type=float,help="white point (0...255) as integer",required=False)
parser.add_argument("-gamma",type=float,help="gamma (default=1.0) as float",required=False)
parser.add_argument("-fs",type=float,help="filter strength (default="+str(filter_strength)+" as float",required=False)
parser.add_argument("-i", action="store_true", help="interactive mode")
parser.add_argument("-n", action="store_true", help="no figures on screen")

args = parser.parse_args()
print(args)

# Mandatory arguments
res = args.res # calibarion file: 259 px/mm 
base=args.base

# First frame start time
if args.s:
    tl_start=float(args.s)
if tl_start<0:
    tl_start=0

# Interval between 2 consequent frames in s
if args.t:
    t=float(args.t)
if t<=0:
    t=1

if args.n:
    show_figures=False

if args.d is not None:
    is_dir=os.path.isdir(args.d)
    if not is_dir:
        print("Directory not found: "+str(args.d))
        sys.exit()
    interactive=True
    path=Path(args.d)

if (args.f is None) and (not is_dir):
    print("A filename or directory is required as an argument.")
    exit(0)

#Parse ROI
x0=0
y0=0
x1=0
y1=0
if args.roi is not None:
    # Parse roi    
    ROI = args.roi[0]
    ROI = ROI.replace("'", "")
    ROI=ROI.split(",")
    commas=len(ROI)-1
    if commas!=3:
        print("3 commas required for roi (i.e. 0,0,1600,1200 or 100,,,)")
        exit(0)
    i=0
    for s in ROI:
        try:
            val=int(s)
            if i==0:
                x0=val
            elif i==1:
                y0=val
            elif i==2:
                x1=val
            elif i==3:
                y1=val
        except:
            1==1
        i+=1
    apply_roi=True

if args.i:
    interactive=True
if args.bp is not None:
    in_bp=args.bp
    apply_levels=True
if args.wp is not None:
    in_wp=args.wp
    apply_levels=True
if args.gamma is not None:
    in_gamma=args.gamma
    apply_levels=True
    
error_list=[]
if in_bp<0 or in_bp>255:
    error_list.append("In black point out of range")
    in_bp=0
if in_wp<0 or in_wp>255:
    error_list.append("In white point out of range")
    in_wp=255
if in_gamma<=0:
    error_list.append("Gamma out of range (<= 0)")
    in_gamma=1.0
if in_bp>=in_wp:
    error_list.append("In black point >= in white point")
    in_bp=0
    in_wp=255

if args.fs is not None:
    hh=float(args.fs)
else:
    hh=filter_strength    
if hh<1.0 or hh>100:
    error_list.append("Filter strength out of range")
    hh=filter_strength

errors=False
if len(error_list)>0:
    errors=True
    print("Argument errors:")
    for s in error_list:
        print(s)
    print("")
    print("Auto corrected values:")
    print("In black point:  "+str(in_bp))
    print("In white point:  "+str(in_wp))
    print("In gamma:        "+str(in_gamma))
    print("Filter strength: "+str(hh))

if is_dir:
    # Count jpg files
    jpg_files=0
    jpg_digits=0
    for p in sorted(path.iterdir()):
        if p.is_file() and p.suffix.lower()=='.jpg':
          jpg_files+=1
          if jpg_files==1:
              jpg_sample=p.name
              jpg_digits=get_sample_numbers(jpg_sample)
              jpg_file_base=p.name[0:-(jpg_digits+4)]
          fname=p.name
    # Count png files
    png_files=0
    png_digits=0
    for p in sorted(path.iterdir()):
        if p.is_file() and p.suffix.lower()=='.png':
          png_files+=1
          if png_files==1:
              png_sample=p.name
              png_digits=get_sample_numbers(png_sample)
              png_file_base=p.name[0:-(png_digits+4)]
          fname=p.name
    if png_files>0 and png_digits>0:
        file_base=png_file_base
        file_type=".png"
        file_digits=png_digits
        file_sample=png_sample
    if jpg_files>0 and jpg_digits>0 and jpg_files>png_files:
        file_base=jpg_file_base
        file_type=".jpg"
        file_digits=jpg_digits
        file_sample=jpg_sample
    print("")
    print("JPG files found: "+str(jpg_files))
    print("PNG files found: "+str(png_files))
    print("Analysis file format : "+file_type)
    print("File numbering digits: "+str(file_digits))
    print("")
    
if interactive:
    from rpi.inputs2 import *
    if is_dir:
        fname=str(path)+"/"+file_sample
    else:
        fname=args.f
    with Image.open(fname) as img:
        file_w, file_h = img.size
    default_res=res
    default_base=base
    if base>file_h:
        default_base=file_h
    default_tl_start=tl_start
    default_t=t      
    default_bp=in_bp
    default_wp=in_wp
    default_gamma=in_gamma
    default_filter_strength=hh
    apply_levels=False
    apply_roi=False

    res=inputValue("resolution:",1,10000,default_res,"px/mm","Resolution is out of range!",False)
    base=inputValue("base:",0,file_h,default_base,"px","Base is out of range!",True)
    if is_dir:
        tl_start=inputValue("Start time for first frame:",0,86400,default_tl_start,"s","Time is out of range!",False)
        t=inputValue("interval between 2 consequent frames:",0.001,86400,default_t,"s","Interval is out of range!",False)

    if args.roi is None:
        default_roi=False
    else:
        default_roi=True
    ask_roi=inputYesNo("roi","Select ROI",default_roi)
    if ask_roi:
        default_x0=x0
        default_y0=y0
        default_x1=x1
        default_y1=y1
        if x1==0 or x1>file_w:
            default_x1=file_w
        if y1==0 or y1>file_h:
            default_y1=file_h
        x0=inputValue("ROI X0",0,int(file_w-1),default_x0,"","ROI X0 is out of range!",True)
        y0=inputValue("ROI Y0",0,int(file_h-1),default_y0,"","ROI Y0 is out of range!",True)
        x1=inputValue("ROI X1",x0,file_w,default_x1,"","ROI X1 is out of range!",True)
        y1=inputValue("ROI Y1",y0,file_h,default_y1,"","ROI Y1 is out of range!",True)
        apply_roi=True
    if [args.bp, args.wp, args.gamma]==[None,None,None]:
        default_levels=False
    else:
        default_levels=True

    ask_levels=inputYesNo("levels","Select levels",default_levels)
    if ask_levels:
        in_bp=inputValue("in black point",0,int(in_wp-1),default_bp,"","Black point is out of range!",True)
        if in_wp<=in_bp:
            in_wp=255
            default_wp=in_wp
        in_wp=inputValue("in white point",int(in_bp+1),255,default_wp,"","White point is out of range!",True)
        in_gamma=inputValue("in gamma",0.001,1000-1,default_gamma,"","Gamma is out of range!",False)
        apply_levels=True

    hh=inputValue("filter strength",1,100,default_filter_strength,"","Filter strength is out of range!",False)
    errors=False

file_list=[]
# Create search pattern and search all matches
import glob
if is_dir:
    pattern=str(path)+"/"+file_base
    pattern+="[0-9]"*file_digits
    pattern+=file_type
    file_list=glob.glob(pattern)
    file_list=sorted(file_list)
else:
    file_list.append(args.f)

#glob.glob("tl2b/"+file_base+"[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].jpg")

i=0
if t.is_integer:
    tl_start=int(tl_start)
tl_time=tl_start
first_frame=0
results=[]
import imageio
for f in file_list:
    current_frame=int(f[len(f)-(file_digits+4):-4])
    if i==0:
        first_frame=current_frame
    else:
        tl_time=tl_start+(int(f[len(f)-(file_digits+4):-4])-first_frame)*t
        if t.is_integer():
            tl_time=int(tl_time)
    print("\nProcessing: "+str(tl_time)+" s "+f)
    
    # Load a picture        
    image = imageio.imread(f)
    
    pic_width=image.shape[1]
    pic_height=image.shape[0]
          
    if show_figures:
        # Display original image
        plt.figure()
        plt.imshow(image)
        plt.show()
    
    if apply_levels:
        image=levels(image,in_bp,in_wp,in_gamma)    
        # Display levels image
        if show_figures:
            plt.figure()
            plt.imshow(image)
            plt.show()
    
    if apply_roi:
        image = image[y0:y1,x0:x1]    
        # Display ROI image
        if show_figures:
            plt.figure()
            plt.imshow(image)
            plt.show()
                
    # hh=13 #THRESHOLD FOR DENOISING GO TILL ELIMINATION OF SMALL PIXELS
    image = cv2.fastNlMeansDenoisingColored(image,None,hh,hh,7,21) #DENOISING FOR ELIMINATING SMALL PIXELS
    thres1 = image.min()
    thres2 = image.max()
    edges = cv2.Canny(image, thres1, thres2)
    
    # Display the edges
    if show_figures:
        plt.figure()
        plt.imshow(edges)
        plt.show()
    
    # Baseline y=442 from the calibration file
    #edges[args.base-y0:, :] = 0
    edges[base-y0:, :] = 0
    
    # Display the edges
    if show_figures:
        plt.figure()
        plt.imshow(edges)
        plt.show()
    
    ys, xs = np.where(edges)
    ys = np.asarray(-ys, dtype=float)
    xs = np.asarray(xs, dtype=float)

    if len(xs)==0 or len(ys)==0:
        print("Droplet not found!")
        break
    
    xs = xs - xs.mean()
    ys = ys - ys.min()
    
    #res = args.res # calibarion file: 259 px/mm 
    xs /= res
    ys /= res
    
    # Plot the edges
    if show_figures:
        plt.figure()
        plt.plot(xs, ys, marker='o', ls='none')
        plt.axhline(0, color='k')
        plt.axis('equal')
        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')
        plt.show()
    
    ######### SLOPE CALCULATIONS AND REPRESENTATIONS BEGIN ########################
    #print('-------------------------------')
    base_radius = xs.max() - xs.min()
    height = ys.max()
    #
    polynomialorder = 1
      
    #RIGHT hand side points
    xy = list(zip(xs, ys))
    xy_pos = list(filter(lambda crd: (crd[0] > 0.), xy)) #Taking the coordinates with positive x values
    xy_pos = sorted(xy_pos, key=lambda k: [k[1], k[0]])
    xc, yc = zip(*xy_pos)
    
    xy_pos=list(zip(xc, yc))
    
    # Coordinate limits righthand side
    minxr,maxxr = min(xc),max(xc)
    minyr,maxyr = min(yc),max(yc)
    
    xdata = np.array(xc,dtype=float)
    ydata = np.array(yc,dtype=float)
    
    #Polynomial fit and Slope calculations
    #slope,intercept,r_value,p_value,std_err=stats.linregress(xc, yc)
    z = np.polyfit(xdata, ydata, polynomialorder)
    p = np.poly1d(z)
    
    #Plot data an polynomial
    if show_figures:
        plt.plot(xdata,ydata,'.' ,xdata, p(xdata),'-')
        plt.title("Zoom Right")
        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')
        plt.axis('equal')
        plt.show()
    
    #
    slope = np.polyder(p)
    slope = slope(xc[0])
    if slope > 0.: 
       contangle = np.arctan(slope)*180./np.pi
    elif slope == 0.:
       contangle = 90.
    else:
       contangle = np.arctan(slope)*180./np.pi + 180.
    
    # Get right contact points and angle
    contangle_right = contangle 
    right_x = xc[0]
    right_y = yc[0]
    theta_right = contangle*np.pi/180.
    
    #LEFT hand side points
    xy = list(zip(xs, ys))
    xy_neg = list(filter(lambda crd: (crd[0] < 0.), xy)) #Taking the coordinates with positive x values
    xy_neg = sorted(xy_neg, key=lambda k: [k[1], k[0]])
    xc, yc = zip(*xy_neg)
    
    xy_neg=list(zip(xc, yc))
    
    # Coordinate limits righthand side
    minxl,maxxl = min(xc),max(xc)
    minyl,maxyl = min(yc),max(yc)
    
    xdata = np.array(xc,dtype=float)
    ydata = np.array(yc,dtype=float)
    
    #Polynomial fit and Slope calculations
    #slope,intercept,r_value,p_value,std_err=stats.linregress(xc, yc)
    z = np.polyfit(xdata, ydata, polynomialorder)
    p = np.poly1d(z)
    
    #Plot data an polynomial
    if show_figures:
        plt.plot(xdata,ydata,'.' ,xdata, p(xdata),'-')
        plt.title("Zoom Left")
        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')
        plt.axis('equal')
        plt.show()
    
    #
    slope = np.polyder(p)
    slope = slope(xc[0])
    if slope > 0.: 
       contangle = np.arctan(slope)*180./np.pi
    elif slope == 0.:
       contangle = 90.
    else:
       contangle = np.arctan(slope)*180./np.pi + 180.
    
    # Get right contact points and angle
    contangle_left = contangle
    left_x = xc[0]
    left_y = yc[0]
    theta_left = contangle*np.pi/180.
    
    # Display the fit
    if show_figures:    
        fig, axs = plt.subplots(1, 3, figsize=(10, 4))
        plt.sca(axs[0])
        plt.plot(xs, ys, marker='o', ls='none')
        plt.axhline(0, color='k')
        plt.xlabel('x [mm]')
        plt.ylabel('y [mm]')
        plt.axis('equal')
        # Plot a zoom on the edge
        #    left edge
        plt.sca(axs[1])
        plt.plot(xs, ys, marker='o', ls='none')
        plt.axhline(0, color='k')
        plt.axis('equal')
        plt.xlabel('x [mm]')
        plt.xlim(minxl, maxxl)
        plt.ylim(minyl, maxyl)
        plt.title("Zoom Left")
        fig.tight_layout()
        #    right edge
        plt.sca(axs[2])
        plt.plot(xs, ys, marker='o', ls='none')
        plt.axhline(0, color='k')
        plt.axis('equal')
        plt.xlabel('x [mm]')
        plt.xlim(minxr, maxxr)
        plt.ylim(minyr, maxyr)
        plt.title("Zoom Right")
        plt.show()
    
    # Print
    if is_dir:
        print("Time: {} s".format(tl_time))
    print("Drop base:   {} mm".format(round(base_radius,3)))
    print("Drop height: {} mm".format(round(height,3)))
    
    # Display the fit and the angles
    fig, axs = plt.subplots()
    plt.plot(xs, ys, marker='x', ls='none')
    plt.axhline(0, color='k')
    
    plt.xlabel('x [mm]')
    plt.ylabel('y [mm]')
    plt.axis('equal')
    
    #plt.savefig('temp1.png', dpi=1200)
    #
    
    # LEAST SQUARE CIRCLE FIT #
    # http://www.dtcenter.org/sites/default/files/community-code/met/docs/write-ups/circle_fit.pdf
    
    # coordinates of the barycenter
    x_m = np.mean(xs)
    y_m = np.mean(ys)
    # calculation of the reduced coordinates
    u = xs - x_m
    v = ys - y_m
    
    # linear system defining the center (uc, vc) in reduced coordinates:
    #    Suu * uc +  Suv * vc = (Suuu + Suvv)/2
    #    Suv * uc +  Svv * vc = (Suuv + Svvv)/2
    Suv  = np.sum(u*v)
    Suu  = np.sum(u**2)
    Svv  = np.sum(v**2)
    Suuv = np.sum(u**2 * v)
    Suvv = np.sum(u * v**2)
    Suuu = np.sum(u**3)
    Svvv = np.sum(v**3)
     
    # Solving the linear system
    A = np.array([ [ Suu, Suv ], [Suv, Svv]])
    B = np.array([ Suuu + Suvv, Svvv + Suuv ])/2.0
    try:
        uc, vc = np.linalg.solve(A, B)
    except:
        print("Drop not found!")
        break
     
    # Centroid
    xcenter = x_m + uc
    ycenter = y_m + vc
     
    # Radius calculation R
    Ri_1     = np.sqrt((xs-xcenter)**2 + (ys-ycenter)**2)
    R_1      = np.mean(Ri_1)
    residu_1 = np.sum((Ri_1-R_1)**2)
    
    circle1=plt.Circle((xcenter, ycenter), R_1, color='c')
    #plt.gcf().gca().add_artist(circle1) #Add circle to the plot
    #axs.add_artist(circle1) #Add circle to the plot 
    
    slope= 1./((right_y-ycenter)/(right_x-xcenter))
    
    if slope > 0.: 
       contangle = np.arctan(slope)*180./np.pi
    elif slope == 0.:
       contangle = 90.
    else:
       contangle = np.arctan(slope)*180./np.pi + 180.
    contangle_right = contangle
    theta_right = np.pi-contangle*np.pi/180.
    
    slope= 1./((left_y-ycenter)/(left_x-xcenter))
    
    if slope > 0.: 
       contangle = np.arctan(slope)*180./np.pi
    elif slope == 0.:
       contangle = 90.
    else:
       contangle = np.arctan(slope)*180./np.pi + 180.
    contangle_left = contangle
    theta_left = np.pi-contangle*np.pi/180.
    
    angle_len = height*2.
    (x2,y2)=(right_x + angle_len*np.cos(theta_right), 
             right_y + angle_len*np.sin(theta_right))
    plt.plot((right_x,x2),(right_y,y2))
    
    (x3,y3)=(left_x + angle_len*np.cos(theta_left), 
             left_y + angle_len*np.sin(theta_left))
    plt.plot((left_x,x3),(left_y,y3))
    
    sphericalcapvolume = np.pi*height**2/3.*(3*R_1-height)

    lca=round(180.-contangle_left,2)
    rca=round(contangle_right,2)
    volume=round(sphericalcapvolume,3)

    axs.annotate("Contact angle left: {}°".format(round(180.-contangle_left,2))
                  , xy=(0., 0.), xytext=(left_x*0.53, height*1.1)
                , fontsize=12, color='blue')
    axs.annotate("Contact angle right: {}°".format(round(contangle_right,2))
                  , xy=(0., 0.), xytext=(left_x*0.53, height*1.28)
                , fontsize=12, color='blue')
    #axs.annotate("Droplet volume: {} μl".format(round(sphericalcapvolume,3))
    #              , xy=(0., 0.), xytext=(left_x*0.8, height*1.6)
    #            , fontsize=12, color='blue')
    
    #plt.savefig('temp2.png', dpi=1200)
    
    print("Contact angle right: {}°".format(round(contangle_right,2)))
    print("Contact angle left:  {}°".format(round(180.-contangle_left,2)))
    print("Volume: {} μl".format(round(sphericalcapvolume,3)))
    plt.show()
    ######### SLOPE CALCULATIONS AND REPRESENTATIONS END ##########################

    # frame_number, time [s], base [mm], height [mm], LCA [°], RCA [°],VOL[µl]
    results.append([current_frame,tl_time,
                    round(base_radius,3),round(height,3),
                    lca,rca,volume])
    i+=1


if is_dir:
    np.savetxt(figuresdir+"/results.csv",results,delimiter=",",fmt="%s")
    # Generate base, height, lca, rca, vol graph as function of time
    r=list(zip(*results))
    if t.is_integer():
        ts=np.asarray(r[1],dtype=int)
    else:
        ts=np.asarray(r[1],dtype=float)
    bases=np.asarray(r[2],dtype=float)
    heights=np.asarray(r[3],dtype=float)
    lcas=np.asarray(r[4],dtype=float)
    rcas=np.asarray(r[5],dtype=float)
    volumes=np.asarray(r[6],dtype=float)

    # Plot base and height as f(t)
    plt.figure()
    plt.plot(ts, bases, color='r', label="base")
    plt.plot(ts, heights, color='b', label="height")
    plt.xlabel('t [s]')
    plt.ylabel('length [mm]')
    plt.legend(loc="upper right")
    plt.xlim(tl_start,ts[-1])
    plt.ylim(0,)
    plt.savefig(figuresdir+"/base-height.png", dpi=300)
    plt.show()
    
    # Plot lca and rca as f(t)
    plt.figure()
    plt.plot(ts, lcas, color='r', label="Left")
    plt.plot(ts, rcas, color='g', label="Right")
    plt.xlabel('t [s]')
    plt.ylabel('Contact angle [°]')
    plt.legend(loc="upper right")
    plt.xlim(tl_start,ts[-1])
    #plt.ylim(0,)
    plt.savefig(figuresdir+"/contact_angle.png", dpi=300)
    plt.show()
    
    # Plot lca as f(t)
    plt.figure()
    plt.plot(ts, lcas, color='k')
    plt.xlabel('t [s]')
    plt.ylabel('Left contact angle [°]')
    plt.xlim(tl_start,ts[-1])
    #lplt.ylim(0,)
    plt.savefig(figuresdir+"/lca.png", dpi=300)
    plt.show()  
    
    # Plot rca as f(t)
    plt.figure()
    plt.plot(ts, lcas, color='black')
    plt.xlabel('t [s]')
    plt.ylabel('Right contact angle [°]')
    plt.xlim(tl_start,ts[-1])
    #plt.ylim(0,)
    plt.savefig(figuresdir+"/rca.png", dpi=300)
    plt.show()
    
    # Plot lca-rca as f(t)
    plt.figure()
    plt.plot(ts, lcas-rcas, color='g')
    plt.xlabel('t [s]')
    plt.ylabel('LCA-RCA [°]')
    plt.xlim(tl_start,ts[-1])
    #plt.ylim(0,)
    plt.axhline(0, color='k')
    plt.savefig(figuresdir+"/lca-rca.png", dpi=300)
    plt.show()
    
    # Plot volume as f(t)
    plt.figure()
    plt.plot(ts, volumes, color='b')
    plt.xlabel('t [s]')
    plt.ylabel('Volume [µl]')
    plt.xlim(tl_start,ts[-1])
    plt.ylim(0,)
    plt.savefig(figuresdir+"/volume.png", dpi=300)
    plt.show()
    