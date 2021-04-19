#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 27 00:59:28 2021

@author: Kim M and Alp K
"""

# importing modules
import os
import csv
import cv2
import math
import numpy as np
from pathlib import Path
import sys
from shapely.geometry import Polygon
from rpi.inputs2 import *

w=0
h=0
x_default=1600
y_default=1600
x_target=0
y_target=0
ex_target=0
ey_target=0
max_width=9999
max_height=9999
markers=0
posList=[]
line_color=(0,255,0)
ptsList=[]
extPos=[]
isPNG=False
isExt=False
ptm_file="ptmdata.csv" # Perspective transformation matrix and data

x1=0
y1=0
x2=0
y2=0

def parse_ptmdata():  
    result=False
    posList=[]
    filename=""
    search=["# Calibration image","# PTS1"]
    index=0
    try:
        with open(ptm_file, "r") as file:
            reader = csv.reader(file, delimiter = ",")
            for row in reader:               
                if search[index] in row:
                    
                    # Calibration image
                    if index==0:
                        line1=next(reader)
                        if len(line1)==1:
                            filename=line1[0]
                    
                    # PTS1
                    if index==1:
                        for i in range(4):
                            line=next(reader)
                            if len(line)==2:
                                try:
                                    x=int(line[0])
                                    y=int(line[1])
                                    posList.append([x,y])
                                except:
                                    pass
                    index+=1
                if index==len(search):
                    break
    except:
        pass
    if len(posList)==4 and len(filename)>0:
        posList=valid_polygon(posList)
        result=True
    else:
        print("Invalid calibration data")
        print("Image name: "+filename)
        print("PTS1:")
        print(posList)
        posList=[]
        filename=""
    return result,posList,filename

def matprint(mat, fmt="g"):
    col_maxes = [max([len(("{:"+fmt+"}").format(x)) for x in col]) for col in mat.T]
    for x in mat:
        for i, y in enumerate(x):
            print(("{:"+str(col_maxes[i])+fmt+"}").format(y), end="  ")
        print("")

def valid_polygon(posList):
    # a valid polygon must meet following criteria:
    # 4 points
    # simple polygon (points are reordered to a simple polygon)
    # at least 2 unique x values
    # at least 2 unique y values
    # =>
    # Return CW ordered posList (TL->TR->BR->BL)
    pos=[]
    valid=True
    if len(posList)!=4:
        valid=False
    if valid:
        a=np.array(posList)
        xs=a[:,0]
        ys=a[:,1]
        if len(np.unique(xs))<2:
            valid=False
        if len(np.unique(ys))<2:
            valid=False
        if valid:
            # Get 2 top points
            ind=np.argsort(a[:,1])
            if a[ind][0,0]<a[ind][1,0]:
                pos.append(a[ind][0])
                pos.append(a[ind][1])
            else:
                pos.append(a[ind][1])
                pos.append(a[ind][0])
            # Get 2 bottom points
            if a[ind][2,0]>a[ind][3,0]:
                pos.append(a[ind][2])
                pos.append(a[ind][3])
            else:
                pos.append(a[ind][3])
                pos.append(a[ind][2])
            pos=np.array(pos).tolist()
    return pos

def polygon_points(posList):
    global img_clone
    if len(posList)!=4:
        return []
    poly=Polygon(posList)
    pts=poly.exterior.coords
    pts=np.array(pts,np.int32)
    pts=pts.reshape((-1,1,2))
    img_clone=cv2.polylines(img_clone,[pts],True,line_color)
    cv2.imshow('Image', img_clone)
    return pts

def draw_polygon(posList,width=2,color=(0,255,0)):
    global img_clone
    result=False
    i=1
    while i<=len(posList):
        x1=round(posList[i-1][0])
        y1=round(posList[i-1][1])
        if i<len(posList):
            x2=round(posList[i][0])
            y2=round(posList[i][1])
        else:
            x2=round(posList[0][0])
            y2=round(posList[0][1])
        img_clone=cv2.line(img_clone,(x1,y1),(x2,y2),color,width)
        result=True
        i+=1
    return result

def length(x1,y1,x2,y2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)

def length_rect(c=(x1,y1,x2,y2)):
    return math.sqrt((c[2]-c[0])**2+(c[3]-c[1])**2)

def coefficient(x1,y1,x2,y2):
    result=True
    value=0
    if x1!=x2:
        value=(y2-y1)/(x2-x1)
        ## Flip direction (Top <-> Bottom)
        ##value=-value
    else:
        result=False   
    return result,value

def length_correction(line1,line2,linet):
    # Extract coordinates from line, line2 and linet
    # Line format: (x1,y1,x2,y2)
    xa1=line1[0]
    ya1=line1[1]
    xa2=line1[2]
    ya2=line1[3]
    
    xb1=line2[0]
    yb1=line2[1]
    xb2=line2[2]
    yb2=line2[3]
    
    xt1=linet[0]
    yt1=linet[1]
    xt2=linet[2]
    yt2=linet[3]
    
    # Whole lines
    l2=length(xb1,yb1,xb2,yb2)
    lt=length(xa1,ya1,xa2,ya2)

    # Half lines
    a1=(xa1+xa2)/2
    b1=(ya1+ya2)/2
    a2=(xb1+xb2)/2
    b2=(yb1+yb2)/2
    a3=(xt1+xt2)/2
    b3=(yt1+yt2)/2

    # Crossing mid lines
    l12=length(a1,b1,a2,b2)
    l23=length(a2,b2,a3,b3)
    
    return (l2/lt)*(l23/l12)

def extend_polygon(polygon,w,h,horizontal=True):
    # Polygon:      ABCD
    # Corners:      1,2,3,4 = TL,TR,BR,BR
    # Coordinates:  (x1,y1), (x2,y2), (x3,y3), (x4,y4)
    # Line lengths: la,lb,lc,ld
    # Tronsformed lines: at,bt,ct,dt
    # Slope coefficients: k12,k23,k34,k41 = ka,kb,kc,kd
    
    iska=False
    iskb=False
    iskc=False
    iskd=False
    
    # Extract coordinates
    x1=polygon[0][0]
    y1=polygon[0][1]
    x2=polygon[1][0]
    y2=polygon[1][1]
    x3=polygon[2][0]
    y3=polygon[2][1]
    x4=polygon[3][0]
    y4=polygon[3][1]
    
    # Calculate coefficients
    iska,ka=coefficient(x1,y1,x2,y2)
    iskb,kb=coefficient(x2,y2,x3,y3)
    iskc,kc=coefficient(x3,y3,x4,y4)
    iskd,kd=coefficient(x4,y4,x1,y1)
    
    if horizontal:
        
        # Case TL, BL
        if round(kd,6)>=0:
            xtl=0
            ytl=-ka*x1+y1
            xbl=(kc*x4-y4+ytl)/(kc-kd)
            ybl=ytl+kd*xbl
        # Case TL, BL
        elif kd<0:
            xbl=0
            ybl=-kc*x4+y4
            xtl=(ka*x1-y1+ybl)/(ka-kd)
            ytl=ybl+kd*xtl
        # Case TR, BR
        if kb<0:
            xtr=w
            ytr=ka*(xtr-x1)+y1
            xbr=(-kc*x4+kb*xtr+y4-ytr)/(kb-kc)
            ybr=kb*(xbr-xtr)+ytr
        # Case TR, BR
        elif round(kb,6)>=0:
            xbr=w
            ybr=kc*(xbr-x4)+y4
            xtr=(ka*x1-kb*xbr-y1+ybr)/(ka-kb)
            ytr=kb*(xtr-xbr)+ybr
    elif not horizontal:
        # vertical
        
        # Case TL, TR
        if round(ka,6)>=0:
            xtl=x1-y1/kd
            ytl=0
            xtr=(ka*xtl-kb*x2+y2)/(ka-kb)
            ytr=ka*(xtr-xtl)
        # Case TL, TR
        elif ka<0:
            xtr=x2-y2/kb           
            ytr=0
            xtl=(ka*xtr-kd*x1+y1)/(ka-kd)
            ytl=ka*(xtl-xtr)
        # Case BL, BR
        if kc<0:
            xbl=(h-y4)/kd+x4
            ybl=h
            xbr=(kb*x3-kc*xbl-y3+ybl)/(kb-kc)
            ybr=kc*(xbr-xbl)+ybl
        # Case BL, BR
        elif round(kc,6)>=0:
            xbr=(h-y3)/kb+x3
            ybr=h
            xbl=(kc*xbr-kd*x4+y4-ybr)/(kc-kd)
            ybl=kc*(xbl-xbr)+ybr

    ar=[]
    ar.append((xtl,ytl))
    ar.append((xtr,ytr))
    ar.append((xbr,ybr))
    ar.append((xbl,ybl))
    ar=np.array(ar).tolist()
    return ar

def click_event(event, x, y, flags, param):
    global img_clone
    global markers
    global posList
    global ptsList
    
    if event == cv2.EVENT_LBUTTONDOWN:
        
        # Enable selection only from the image area
        if x<0 or x>w:
            return
        if y<0 or y>h:
            return
        if x==w:
            x=w-1
        if y==h:
            y=h-1
            
        if markers<4:
            # Do not accept existing marker points
            if (x,y) in posList:
                return
            print ("("+str(x)+","+str(y)+")")
            posList.append((x, y))
            red = img[y,x,2]
            blue = img[y,x,0]
            green = img[y,x,1]        
            markercolor =( int(255-blue),int(255-green),int(255-red))
            cv2.drawMarker(img_clone,(x,y),tuple(markercolor),markerType=cv2.MARKER_CROSS,markerSize=20,thickness=1)
            markers+=1
            cv2.imshow('Image', img_clone)
            if markers==4:
                posList=valid_polygon(posList)
                if len(posList)==4:
                    points=polygon_points(posList)
                    ptsList=points[:-1]
                    print("Press any key to accept the selected perspective.")
                else:
                    print("Invalid selection!")
                    img_clone=img.copy()
                    cv2.imshow('Image', img_clone)
                    markers=0
                    posList=[]

    elif event == cv2.EVENT_RBUTTONDOWN:
        # Clear all markers
        img_clone=img.copy()
        cv2.imshow('Image', img_clone)
        markers=0
        posList=[]

# Get initial image filename
arguments=len(sys.argv)
if arguments==1:
    result=False
    if os.path.isfile(ptm_file):
        result,posList,filename=parse_ptmdata()
        if result:
            img = cv2.imread(filename)
            markers=4
            print("Calibration file with perspective selection loaded.")
    if result==False:
        print("Usage: ptransform.py image_filename")
        sys.exit(0)
elif arguments>2:
    print("Too many arguments!")
    sys.exit(1)

if arguments==2:
    filename=sys.argv[1]
    img = cv2.imread(filename)

# Calibration image with markers alredy loaded
img_clone=img.copy()
if len(img.shape)==2:
    h,w=img.shape
elif len(img.shape)==3:
    h,w,ch=img.shape
cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
cv2.imshow('Image', img_clone)

if arguments==1:
    polygon_points(posList)
    print("Clear selection by pressing the mouse second button.")
else:
    print("Select perspective with 4 markers:")

cv2.setMouseCallback("Image", click_event)
cv2.waitKey(0)

# All these waitkeys are a hack to get the OpenCV window to close
cv2.waitKey(1)
cv2.destroyAllWindows()
for i in range (1,5):
    cv2.waitKey(1)

selectionOk=True
if len(posList)!=4:
    print("Perspective selection canceled.")
    selectionOk=False

if selectionOk:
    # Ask if extrapolate in x or y direction
    # 2 questions, only one is allowed (or not?)
    print("")
    tmp="Accept default target resolution: "+str(x_default)+"x"+str(y_default)
    isDefault=inputYesNo("default resolution",tmp,True)
    if isDefault:
        x_target=x_default
        y_target=y_default
    else:
        top_width=posList[1][0]-posList[0][0]
        bottom_width=posList[2][0]-posList[3][0]
        if top_width>=bottom_width:
            x_default=top_width
        else:
            x_default=bottom_width
        left_height=posList[2][1]-posList[0][1]
        right_height=posList[3][1]-posList[1][1]
        if left_height>=right_height:
            y_default=left_height
        else:
            y_default=right_height
        x_target=inputValue("target width",1,max_width,x_default,"","Value out of range!",True)
        y_target=inputValue("target height",1,max_width,y_default,"","Value out of range!",True)

    print("")
    isPNG=inputYesNo("png mode","Override default file format with PNG",isPNG)
    
    # Extend perspective markers
    extPrefix=""
    tmp="Extend perspective in horizontal direction"
    isHorizontal=inputYesNo("horizontal perspective extension",tmp,False)
    if not isHorizontal:
            tmp="Extend perspective in vertical direction"
            isVertical=inputYesNo("vertical perspective extension",tmp,False)

    # Source reference points
    tl=posList[0]
    tr=posList[1]
    bl=posList[3]
    br=posList[2]
    
    # Target reference points
    ttl=[0,0]
    ttr=[x_target,0]
    tbl=[0,y_target]
    tbr=[x_target,y_target]
    
    # Transformation matrix
    pts1=np.float32([tl,tr,bl,br])
    pts2=np.float32([ttl,ttr,tbl,tbr])
    M=cv2.getPerspectiveTransform(pts1,pts2)
    print("")
    print("Perspective transformation matrix:")
    matprint(M)
    
    # Perspective tranformation
    dst=cv2.warpPerspective(img,M,(x_target,y_target))
    # PT = Perspective Transformed
    dst_filename=Path(filename).stem
    if isPNG:
        dst_filename+=".png"
    else:
        dst_filename+=Path(filename).suffix
    cv2.imwrite("pt-"+dst_filename,dst)

    isExt=isHorizontal or isVertical
    if isExt:      
        extPos=extend_polygon(posList,w,h,isHorizontal)
        if isHorizontal:
            # Lines 14 and 23, l = left and r = right
            line1=(posList[0][0],posList[0][1],posList[3][0],posList[3][1])
            line2=(posList[1][0],posList[1][1],posList[2][0],posList[2][1])
            extl=(extPos[0][0],extPos[0][1],extPos[3][0],extPos[3][1])
            extr=(extPos[1][0],extPos[1][1],extPos[2][0],extPos[2][1])
            ll=length_correction(line2,line1,extl)
            lr=length_correction(line1,line2,extr)
            ey_target=y_target
            if (ll+lr)>0:
                ex_target=round((ll+lr+1)*x_target)
            else:
                ex_target=x_target
            extPrefix="m-exth-"
        else:
            # Lines 43 and 12, b = bottom and t = top
            line1=(posList[3][0],posList[3][1],posList[2][0],posList[2][1])
            line2=(posList[0][0],posList[0][1],posList[1][0],posList[1][1])
            extb=(extPos[3][0],extPos[3][1],extPos[2][0],extPos[2][1])
            extt=(extPos[0][0],extPos[0][1],extPos[1][0],extPos[1][1])
            lb=length_correction(line2,line1,extb)
            lt=length_correction(line1,line2,extt)
            ex_target=x_target
            if (lb+lt)>0:
                ey_target=round((lb+lt+1)*y_target)
            else:
                ey_target=y_target
            extPrefix="m-extv-"
        
        # Extended source reference points
        etl=extPos[0]
        etr=extPos[1]
        ebl=extPos[3]
        ebr=extPos[2]
        
        # Target reference points
        ettl=[0,0]
        ettr=[ex_target,0]
        etbl=[0,ey_target]
        etbr=[ex_target,ey_target]

        # Extended transformation matrix
        epts1=np.float32([etl,etr,ebl,ebr])
        epts2=np.float32([ettl,ettr,etbl,etbr])
        EM=cv2.getPerspectiveTransform(epts1,epts2)
        print("")
        print("Extended perspective transformation matrix:")
        matprint(EM)

        # Perspective tranformation
        edst=cv2.warpPerspective(img,EM,(ex_target,ey_target))
    
        # Save extended perspective transformed image
        cv2.imwrite("pte-"+dst_filename,edst)
    
    # Save transformation matrix and data
    f=open(ptm_file,"w")
    f.write("# Calibration image\n")
    f.write( filename+"\n")
    f.write("\n")
    writer=csv.writer(f,delimiter=",")
    f.write("# Perspective transformation matrix\n")
    writer.writerows(M)
    f.write("\n")
    f.write("# PTS1\n")
    writer.writerows(np.array(pts1,np.int32))
    f.write("\n")
    f.write("# PTS2\n")
    writer.writerows(np.array(pts2,np.int32))
    f.write("\n")
    
    # Write extended perspective matrix and data
    if isExt:   
        f.write("# Extended perspective transformation matrix\n")
        writer.writerows(EM)
        f.write("\n")
        f.write("# EPTS1\n")
        writer.writerows(np.array(epts1,np.int32))
        f.write("\n")
        f.write("# EPTS2\n")
        writer.writerows(np.array(epts2,np.int32))
        f.write("\n")
        
        # Perspective length correction section
        f.write("# Extended perspective length correction data\n")
        f.write("Extension direction,")
        if isHorizontal:
            f.write("horizontal\n")
            f.write("L factor,"+str(ll)+"\n")
            f.write("R factor,"+str(lr)+"\n")
            f.write("E factor,"+str(ll+lr+1)+"\n")
        else:
            f.write("vertical\n")
            f.write("B factor,"+str(lb)+"\n")
            f.write("T factor,"+str(lt)+"\n")
            f.write("E factor,"+str(lb+lt+1)+"\n")
        f.write("\n")   
    
    f.write("# PNG mode\n")
    if isPNG:
        f.write("Enabled\n")
    else:
        f.write("Disabled\n")
    f.close()

    if isExt:
        # m   = markers
        # ext = extended
        cv2.imwrite("m-"+dst_filename,img_clone)
        extPos=extend_polygon(posList,w,h,isHorizontal)
        if draw_polygon(extPos):
            cv2.imwrite(extPrefix+dst_filename,img_clone)
