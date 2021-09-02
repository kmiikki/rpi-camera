#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
(C) Kim Miikki 2021
This script is a derivative from ssocr.py
URL: https://github.com/jiweibo/SSOCR, 19.8.2021
License: GPLv3
"""

from decimal import *
import csv
import os
#import datetime
from datetime import datetime,timedelta
from time import sleep
import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
from rpi.roi import *
from rpi.inputs2 import *

ESC=27
SPACE=32
O=79
R=82
T=84

def display_roi_status():
    if roi_dir!="":
        print("ROI file found in "+roi_dir+" directory: "+str(roi_x0)+","+str(roi_y0)+","+str(roi_w)+","+str(roi_h))
    else:
        print("ROI file not found!")

def ask_ext(image_type="",default="png",searchdir=True):
    if image_type!="":
        image_type+=" "
    askExt=True
    ext_text="Extension for "+image_type+"images "
    if searchdir:
        ext_text+="included in search "
    ext_text+="(Default "+default+": <ENTER>)? "
    while askExt:
        
        ext=input(ext_text)
        if ext=="":
            ext=default
            print("Default selected: "+ext)
        if ext=="" or ext=="." or ext.count(".")>1:
            print("Invalid extension!")
            continue
        if len(ext)<1:
            print("Extension too short!")
            continue
        if ext.find(".")<0:
            ext="."+ext
            askExt=False
        elif ext.find(".")==0:
            askExt=False
        else:
            print("Invalid extension!")
    return ext

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

def levels_gray(image,black_point,white_point,gamma=1.0):
    inBlack  = np.array([black_point],dtype=np.float32)
    inWhite  = np.array([white_point],dtype=np.float32)
    inGamma  = np.array([gamma], dtype=np.float32)
    outBlack = np.array([0], dtype=np.float32)
    outWhite = np.array([255], dtype=np.float32)
    
    image = np.clip((image - inBlack) / (inWhite - inBlack), 0, 255)
    image = (image ** (1/inGamma)) * (outWhite - outBlack) + outBlack
    image = np.clip(image, 0, 255).astype(np.uint8)
    return image

def decimal_digits(number):
    decimals=10
    sign,digits,exp=round(Decimal(number),decimals).as_tuple()
    i=0
    for n in reversed(digits):
        if n!=0:
            break
        i+=1
    d=decimals-i
    if d>0:
        return d
    else:
        return 0

DIGITS_LOOKUP = {
    (1, 1, 1, 1, 1, 1, 0): 0,
    (1, 1, 0, 0, 0, 0, 0): 1,
    (1, 0, 1, 1, 0, 1, 1): 2,
    (1, 1, 1, 0, 0, 1, 1): 3,
    (1, 1, 0, 0, 1, 0, 1): 4,
    (0, 1, 1, 0, 1, 1, 1): 5,
    (0, 1, 1, 1, 1, 1, 1): 6,
    (1, 1, 0, 0, 0, 1, 0): 7,
    (1, 1, 1, 1, 1, 1, 1): 8,
    (1, 1, 1, 0, 1, 1, 1): 9,
    (0, 0, 0, 0, 0, 1, 1): '-'
}
H_W_Ratio = 2 # 1.9, 2.75
THRESHOLD = 35   # 35
#thresh=32
inverse=True
thres_filter=True
arc_tan_theta = 10  # Digital tube tilt angle # 16
numbers=-1
decimals=0
crop_y0 = 0
crop_y1 = 480
crop_x0 = 0
crop_x1 = 640
file_ext="jpg"
in_bp=0
in_wp=255
in_gamma=1.0
isLevels=False
toi_result=False

parser = argparse.ArgumentParser()
parser.add_argument('image_path',type=str,nargs="?",help='path to image')
parser.add_argument('-b', '--batch_ocr', action='store_const', const=True, help='batch mode OCR')
parser.add_argument('-c', '--capture_image', action='store_const', const=True, help='capture an image')
parser.add_argument('-r', '--real_time_logger', action='store_const', const=True, help='real-time data logger')
parser.add_argument('-s', '--show_image', action='store_const', const=True, help='whether to show image')
parser.add_argument('-d', '--is_debug', action='store_const', const=True, help='True or False')
parser.add_argument('-i', '--inverse_display', action='store_const', const=True, help='inverse display mode (bright digits)')
parser.add_argument('-hw', '--hw_ratio', type=float, required=False, help='H/W ratio')
parser.add_argument('-a', '--tilt_angle', type=float, required=False, help='tilt angle')
parser.add_argument('-t', '--threshold', type=int, required=False, help='threshold (0-255)')
parser.add_argument('-n', '--digits', type=int, required=False, help='digits')
parser.add_argument('-p', '--decimals', type=int, required=False, help='decimal point position (digits >= pos >= 0)')
parser.add_argument("-bp",type=float,help="black point (0...255) as integer",required=False)
parser.add_argument("-wp",type=float,help="white point (0...255) as integer",required=False)
parser.add_argument("-gamma",type=float,help="gamma (default=1.0) as float",required=False)

def load_image(path, show=False, isLevels=False):
    #global in_bp,in_wp,in_gamma
    # todo: crop image and clear dc and ac signal
    #img = cv2.imread(path,cv2.IMREAD_COLOR)
    gray_img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    h, w = gray_img.shape
    # crop_y0 = 0 if h <= crop_y0_init else crop_y0_init
    # crop_y1 = h if h <= crop_y1_init else crop_y1_init
    # crop_x0 = 0 if w <= crop_x0_init else crop_x0_init
    # crop_x1 = w if w <= crop_x1_init else crop_x1_init
    #gray_img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if roi_result:
        gray_img = gray_img[crop_y0:crop_y1, crop_x0:crop_x1]
    if isLevels:
        gray_img=levels_gray(gray_img,in_bp,in_wp,in_gamma)
    #gray_img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_img, (7, 7), 0)
    if show:
        cv2.imshow('gray_img', gray_img)
        cv2.imshow('blurred_img', blurred)
    return blurred, gray_img

def preprocess(img, threshold, show=False, kernel_size=(5, 5)):
    # Histogram partial equalization
    clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(6, 6))
    img = clahe.apply(img)
    # Adaptive threshold binarization
    if inverse:
        img=cv2.bitwise_not(img)
    
    dst = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 127, threshold)
           
    # Closed operation open operation
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, kernel_size)
    dst = cv2.morphologyEx(dst, cv2.MORPH_CLOSE, kernel)
    dst = cv2.morphologyEx(dst, cv2.MORPH_OPEN, kernel)

    if show:
        cv2.imshow('equlizeHist', img)
        cv2.imshow('threshold', dst)
    return dst

def helper_extract(one_d_array, threshold=20):
    res = []
    flag = 0
    temp = 0
    for i in range(len(one_d_array)):
        if one_d_array[i] < 12 * 255:
            if flag > threshold:
                start = i - flag
                end = i
                temp = end
                if end - start > 20:
                    res.append((start, end))
            flag = 0
        else:
            flag += 1

    else:
        if flag > threshold:
            start = temp
            end = len(one_d_array)
            if end - start > 50:
                res.append((start, end))
    return res


def find_digits_positions(img, reserved_threshold=20):
    # reserved_thershold=20
#    cnts = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#    digits_positions = []
#    for c in cnts[1]:
#        (x, y, w, h) = cv2.boundingRect(c)
#        cv2.rectangle(img, (x, y), (x + w, y + h), (128, 0, 0), 2)
#        cv2.imshow('test', img)
#        cv2.waitKey(0)
#        cv2.destroyWindow('test')
#        if w >= reserved_threshold and h >= reserved_threshold:
#            digit_cnts.append(c)
#    if digit_cnts:
#        digit_cnts = contours.sort_contours(digit_cnts)[0]

    digits_positions = []
    img_array = np.sum(img, axis=0)
    horizon_position = helper_extract(img_array, threshold=reserved_threshold)
    img_array = np.sum(img, axis=1)
    vertical_position = helper_extract(img_array, threshold=reserved_threshold * 4)
    # make vertical_position has only one element
    if len(vertical_position) > 1:
        vertical_position = [(vertical_position[0][0], vertical_position[len(vertical_position) - 1][1])]
    for h in horizon_position:
        for v in vertical_position:
            digits_positions.append(list(zip(h, v)))
    assert len(digits_positions) > 0, "Failed to find digits's positions"

    return digits_positions


def recognize_digits_area_method(digits_positions, output_img, input_img):
    digits = []
    for c in digits_positions:
        x0, y0 = c[0]
        x1, y1 = c[1]
        roi = input_img[y0:y1, x0:x1]
        h, w = roi.shape
        suppose_W = max(1, int(h / H_W_Ratio))
        # Individually identify the case of 1 
        if w < suppose_W / 2:
            x0 = x0 + w - suppose_W
            w = suppose_W
            roi = input_img[y0:y1, x0:x1]
        width = (max(int(w * 0.15), 1) + max(int(h * 0.15), 1)) // 2
        dhc = int(width * 0.8)
        # print('width :', width)
        # print('dhc :', dhc)

        small_delta = int(h / arc_tan_theta) // 4
        # print('small_delta : ', small_delta)
        segments = [
            # # version 1
            # ((w - width, width // 2), (w, (h - dhc) // 2)),
            # ((w - width - small_delta, (h + dhc) // 2), (w - small_delta, h - width // 2)),
            # ((width // 2, h - width), (w - width // 2, h)),
            # ((0, (h + dhc) // 2), (width, h - width // 2)),
            # ((small_delta, width // 2), (small_delta + width, (h - dhc) // 2)),
            # ((small_delta, 0), (w, width)),
            # ((width, (h - dhc) // 2), (w - width, (h + dhc) // 2))

            # # version 2
            ((w - width - small_delta, width // 2), (w, (h - dhc) // 2)),
            ((w - width - 2 * small_delta, (h + dhc) // 2), (w - small_delta, h - width // 2)),
            ((width - small_delta, h - width), (w - width - small_delta, h)),
            ((0, (h + dhc) // 2), (width, h - width // 2)),
            ((small_delta, width // 2), (small_delta + width, (h - dhc) // 2)),
            ((small_delta, 0), (w + small_delta, width)),
            ((width - small_delta, (h - dhc) // 2), (w - width - small_delta, (h + dhc) // 2))
        ]
        # cv2.rectangle(roi, segments[0][0], segments[0][1], (128, 0, 0), 2)
        # cv2.rectangle(roi, segments[1][0], segments[1][1], (128, 0, 0), 2)
        # cv2.rectangle(roi, segments[2][0], segments[2][1], (128, 0, 0), 2)
        # cv2.rectangle(roi, segments[3][0], segments[3][1], (128, 0, 0), 2)
        # cv2.rectangle(roi, segments[4][0], segments[4][1], (128, 0, 0), 2)
        # cv2.rectangle(roi, segments[5][0], segments[5][1], (128, 0, 0), 2)
        # cv2.rectangle(roi, segments[6][0], segments[6][1], (128, 0, 0), 2)
        # cv2.imshow('i', roi)
        # cv2.waitKey()
        # cv2.destroyWindow('i')
        on = [0] * len(segments)

        for (i, ((xa, ya), (xb, yb))) in enumerate(segments):
            seg_roi = roi[ya:yb, xa:xb]
            # plt.imshow(seg_roi)
            # plt.show()
            total = cv2.countNonZero(seg_roi)
            area = (xb - xa) * (yb - ya) * 0.9
            print(total / float(area))
            if total / float(area) > 0.45:
                on[i] = 1

        # print(on)

        if tuple(on) in DIGITS_LOOKUP.keys():
            digit = DIGITS_LOOKUP[tuple(on)]
        else:
            digit = '*'
        digits.append(digit)
        cv2.rectangle(output_img, (x0, y0), (x1, y1), (0, 128, 0), 2)
        cv2.putText(output_img, str(digit), (x0 - 10, y0 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 128, 0), 2)

    return digits

def recognize_digits_line_method(digits_positions, output_img, input_img):
    digits = []
    color=(128,128,128)
    for c in digits_positions:
        x0, y0 = c[0]
        x1, y1 = c[1]
        roi = input_img[y0:y1, x0:x1]
        h, w = roi.shape
        suppose_W = max(1, int(h / H_W_Ratio))

        # Eliminate extraneous symbol interference
        if x1 - x0 < 25 and cv2.countNonZero(roi) / ((y1 - y0) * (x1 - x0)) < 0.2:
            continue

        # Individually identify the case of 1
        if w < suppose_W / 2:
            x0 = max(x0 + w - suppose_W, 0)
            roi = input_img[y0:y1, x0:x1]
            w = roi.shape[1]

        center_y = h // 2
        quater_y_1 = h // 4
        quater_y_3 = quater_y_1 * 3
        center_x = w // 2
        line_width = 5  # line's width
        width = (max(int(w * 0.15), 1) + max(int(h * 0.15), 1)) // 2
        small_delta = int(h / arc_tan_theta) // 4
        segments = [
            ((w - 2 * width, quater_y_1 - line_width), (w, quater_y_1 + line_width)),
            ((w - 2 * width, quater_y_3 - line_width), (w, quater_y_3 + line_width)),
            ((center_x - line_width - small_delta, h - 2 * width), (center_x - small_delta + line_width, h)),
            ((0, quater_y_3 - line_width), (2 * width, quater_y_3 + line_width)),
            ((0, quater_y_1 - line_width), (2 * width, quater_y_1 + line_width)),
            ((center_x - line_width, 0), (center_x + line_width, 2 * width)),
            ((center_x - line_width, center_y - line_width), (center_x + line_width, center_y + line_width)),
        ]
        on = [0] * len(segments)

        for (i, ((xa, ya), (xb, yb))) in enumerate(segments):
            seg_roi = roi[ya:yb, xa:xb]
            # plt.imshow(seg_roi, 'gray')
            # plt.show()
            total = cv2.countNonZero(seg_roi)
            area = (xb - xa) * (yb - ya) * 0.9
            # print('prob: ', total / float(area))
            if total / float(area) > 0.25:
                on[i] = 1
        # print('encode: ', on)
        if tuple(on) in DIGITS_LOOKUP.keys():
            digit = DIGITS_LOOKUP[tuple(on)]
        else:
            digit = '*'

        digits.append(digit)

        # Decimal point recognition
        # print('dot signal: ',cv2.countNonZero(roi[h - int(3 * width / 4):h, w - int(3 * width / 4):w]) / (9 / 16 * width * width))
        if cv2.countNonZero(roi[h - int(3 * width / 4):h, w - int(3 * width / 4):w]) / (9. / 16 * width * width) > 0.65:
            digits.append('.')
            cv2.rectangle(output_img,
                          (x0 + w - int(3 * width / 4), y0 + h - int(3 * width / 4)),
                          (x1, y1), color, 2)
            cv2.putText(output_img, 'dot',
                        (x0 + w - int(3 * width / 4), y0 + h - int(3 * width / 4) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

        cv2.rectangle(output_img, (x0, y0), (x1, y1), color, 2)
        cv2.putText(output_img, str(digit), (x0 + 3, y0 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    return digits

def numstr(digits,numbers=-1,decimals=0):
    tmp=""
    for s in digits:
        if str(s).isdigit():
            tmp+=str(s)
    if numbers>0:
        if numbers != len(tmp):
            tmp=""
    if decimals>0:
        length=len(tmp)
        if decimals<length:
            tmp=tmp[:length-decimals]+"."+tmp[-decimals:]
    return tmp

def main():
    global crop_x0,crop_y0,crop_x1,crop_y1
    global inverse,THRESHOLD,H_W_Ratio,thres_filter,arc_tan_theta
    global numbers,decimals
    global in_bp, in_wp, in_gamma,isLevels
    global roi_result
    
    args = parser.parse_args()

    print("Seven segment LCD number logger")
    curdir=os.getcwd()
    path=Path(curdir)
    print("")
    print("Current directory:")
    print(curdir)
    print("")
    
    roi_result=validate_roi_values()
    if roi_result:
        crop_y0 = roi_crop_y0
        crop_y1 = roi_crop_y1
        crop_x0 = roi_crop_x0
        crop_x1 = roi_crop_x1
    display_roi_status()
    
    unit_default="s"
    unit=""
    interval_mode_default=True
    interval_mode=True
    interval_default=1
    interval=1
    decimals_batch=0
    isROI=roi_result
    yaxes="Value"
    ext=""
    filter_start=""
    start_time=0
    saveNames=False
    cursor=0
    log_all=False

    file_list=[]
    results=[]

    # Arguments section start    
    if args.inverse_display:
        inverse=True
    else:
        inverse=False
    if args.hw_ratio:
        H_W_Ratio=float(args.hw_ratio)
        thres_filter=True        
    if args.threshold:
        THRESHOLD=int(args.threshold)
        thres_filter=True
    if args.tilt_angle:
        arc_tan_theta=float(args.tilt_angle)
    
    if args.digits:
        if args.digits>0:
            numbers=int(args.digits)    
    if args.decimals:
        if args.decimals>0 and args.decimals<=numbers:
            decimals=int(args.decimals)
        
    if args.bp is not None:
        in_bp=args.bp
        isLevels=True
    if args.wp is not None:
        in_wp=args.wp
        isLevels=True
    if args.gamma is not None:
        in_gamma=args.gamma
        isLevels=True
    # Arguments section end

    # Levels section START   
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
    
    if len(error_list)>0:
        print("Levels fuction argument errors:")
        for s in error_list:
            print(s)
        print("")
        print("Auto corrected values:")
        print("In black point:  "+str(in_bp))
        print("In white point:  "+str(in_wp))
        print("In gamma:        "+str(in_gamma))    
    # Levels section END

    if True in [args.real_time_logger,args.batch_ocr]:
        count=0
        if args.batch_ocr:
            interval_min=1e-9
            interval_max=1e9
            intvalue=False
            count+=1
        if args.capture_image:
            count+=1
        if args.real_time_logger:
            interval_min=0  # 0 = no delay between frames
            interval_max=30*24*3600
            intvalue=True
            count+=1
        if count>1:
            print("Only one of -b, -c or -r options can be selected!")
            print("The program is terminated.")
            sys.exit(0)

        if args.batch_ocr:
            # Ask for unit
            while True:
                try:
                    tmp=input("Enter unit (Default="+str(unit_default)+": <Enter>): ")
                    if tmp=="":
                        unit=unit_default
                        print("Default unit selected: "+str(unit_default))
                        break
                    unit=tmp
                    break
                except:
                    print("Not a valid unit.")
                    continue
            
            # Select file extension
            ext=ask_ext("analysis",file_ext)
        
            # Select start pass filter
            filter_start=input("Select start pass filter for analysis file names (Enter=None)? ")
            
            # Creat a list of all analysis files
            for p in sorted(path.iterdir()):
              if p.is_file():
                if ext==p.suffix:
                    fname=p.name
                    if len(filter_start)>0:
                        if fname.find(filter_start)!=0:
                            continue
                    file_list.append(fname)            

        # Ask for y axes text
        while True:
            try:
                tmp=input("Enter y axes text (Default="+str(yaxes)+": <Enter>): ")
                if tmp=="":
                    print("Default text selected: "+str(yaxes))
                    break
                yaxes=tmp
                break
            except:
                print("Not a valid text.")
                continue

        if True in [args.capture_image,args.real_time_logger]:
            interval_mode=inputYesNo("Interval","Use interval",interval_mode_default)
        
        if (not interval_mode) and args.real_time_logger:
            unit=unit_default
            log_all=inputYesNo("all values logging","Log all values",log_all)
        
        if interval_mode and args.real_time_logger:
            unit=unit_default
        
        if interval_mode or args.batch_ocr:
            interval=inputValue("interval:",interval_min,interval_max,interval_default,unit,"Interval is out of range!",intvalue)
        
        if args.batch_ocr:
            # Select first image start time
            while True:
                try:
                    tmp=input("First image start time (Default=0 "+unit+": <Enter>)? ")
                    if tmp=="":
                        start_time=0
                        break
                    start_time=float(tmp)
                    break
                except:
                    print("Not a valid value for time!")
            saveNames=inputYesNo("Filename column","Add filename column to data",False)
            if saveNames:
                cursor=1
        tmp=[]
        if saveNames:
            tmp=["Filename"]
        tmp.append("Time ("+unit+")")
        tmp.append(yaxes)
        results.append(tmp)
        
    if True in [args.capture_image,args.real_time_logger]:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
                print("Cannot open camera")
                exit()
    
    t0=datetime.now()
    if args.real_time_logger:
        i=0 # counter for interval mode
        j=0 # counter for change mode
        counter_digits=6
        # Create a status image
        text="Exit: ESC"
        font=cv2.FONT_HERSHEY_SIMPLEX
        (label_width,label_height),baseline=cv2.getTextSize(text,font,1,2)
        img=np.zeros((label_height*2,label_width+200,3),np.uint8)
        # print(label_width,label_height,label_height)
        cv2.putText(img,"Exit: ESC",(100,label_height+baseline),font,1,(0,0,255),2)
        cv2.imshow("Data logging started",img)

        # Capture a dummy frame
        ret, frame = cap.read()
    
        oldvalue=""
        t0=datetime.now()
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            if isROI:
                frame = frame[crop_y0:crop_y1, crop_x0:crop_x1]
            if isLevels:
                frame=levels(frame,in_bp,in_wp,in_gamma)
            img=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(img, (7, 7), 0)
            # clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(6, 6))
            # img = clahe.apply(img)
            img=preprocess(blurred, THRESHOLD, show=args.show_image)
            
            key=cv2.waitKey(1)
            if key==ESC:
                break

            if interval_mode:
                i+=1
                print(str(i).zfill(counter_digits)+": ",end="")
            digits=[]
            value=""
            try:
                digits_positions = find_digits_positions(img)
                digits = recognize_digits_line_method(digits_positions, blurred, img)
                value=numstr(digits,numbers,decimals)
            except:
                pass

            new_value=False
            if not interval_mode:
                if len(value)>0:
                    if (value != oldvalue) or log_all==True:
                        j+=1
                        print(str(j).zfill(counter_digits)+": ",end="")
                        print(value)
                        oldvalue=value
                        new_value=True
            t1=datetime.now()
            capture_time=(t1-(t0+timedelta(seconds=(i-1)*interval))).total_seconds()
            delay=float(interval-capture_time)        


            if len(value)>0:
                if value.find(".")>0:
                    value=float(value)
                else:
                    value=int(value)

            if interval_mode:
                print(value,end="")
                if interval>0:
                    results.append([int(i-1)*interval,value])
                    if delay<0:
                        print(": frame delayed "+format(round(abs(delay),3),".3f")+" s")
                        #lags.append([i,round(abs(delay),3)])
                    if delay>0:
                        sleep(delay)
                else:
                    results.append([(t1-t0).total_seconds(),value])
                print("")
            else:
                if len(str(value))>0 and (new_value or log_all):
                    results.append([(t1-t0).total_seconds(),value])

    elif args.capture_image:
        if isROI:
            print("")
            print("Remove ROI area:        R")
        print("Capture an image:       SPACE")
        print("Toggle processed image: T")
        print("OCR digits:             O")
        print("Exit preview:           ESC")
        isToggle=False
        isOCR=True
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            if isROI:
                frame = frame[crop_y0:crop_y1, crop_x0:crop_x1]
            if isLevels:
                frame=levels(frame,in_bp,in_wp,in_gamma)
            img=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            if isToggle:
                blurred = cv2.GaussianBlur(img, (7, 7), 0)
                img=preprocess(blurred, THRESHOLD, show=True)
                #cv2.imshow('preprocessed',img)
                if isOCR:
                    try:
                        digits_positions = find_digits_positions(img)
                        digits = recognize_digits_line_method(digits_positions, blurred, img)
                        print(digits)
                    except:
                        pass
            cv2.imshow('Capture an image of digits',img)
            key=cv2.waitKey(1)
            if key==ESC:
                break
            if key==SPACE:
                cv2.imwrite("lcd.png",frame)
                break
            if key in [R,R+32]:
                isROI=False
            if key in [T,T+32]:
                isToggle=not isToggle
            if key in [O,O+32]:
                isOCR=not isOCR

    elif args.batch_ocr:
        i=0
        files=len(file_list)
        files_digits=len(str(files))
        d1=decimal_digits(start_time)
        d2=decimal_digits(interval)
        if d1>d2:
            decimals_batch=d1
        else:
            decimals_batch=d2
        for fname in file_list:
            print(str(i+1).zfill(files_digits)+"/"+str(files).zfill(files_digits)+": ",end="")
            if isLevels:
                img=cv2.imread(fname)
            else:
                img=cv2.imread(fname,cv2.IMREAD_GRAYSCALE)
            w=img.shape[1]
            h=img.shape[0]
            #print(w,h)
            if roi_result:
                crop_x0=int(roi_x0*w)
                crop_x1=int((roi_x0+roi_w)*w)
                crop_y0=int(roi_y0*h)
                crop_y1=int((roi_y0+roi_h)*h)                
                img = img[crop_y0:crop_y1, crop_x0:crop_x1]
            if isLevels:
                img=levels(img,in_bp,in_wp,in_gamma)
                img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(img, (7, 7), 0)
            img=preprocess(blurred, THRESHOLD, show=args.show_image)
            if args.is_debug is not None:
                cv2.imwrite(Path(fname).stem+".png",img)
            
            # Detect digits
            digits=[]
            value=""
            try:
                digits_positions = find_digits_positions(img)
                digits = recognize_digits_line_method(digits_positions, blurred, img)
                value=numstr(digits,numbers,decimals)
            except:
                pass
            
            # Add detected numbers to a list
            t=round(start_time+i*interval,decimals_batch)
            if len(value)>0:
                if value.find(".")>0:
                    value=float(value)
                else:
                    value=int(value)
                if not saveNames:
                    results.append([t,value])
                else:
                    results.append([fname,t,value])
                print(value)
            else:
                print("N/A: "+fname)
            i+=1
    
    # OCR for a single image
    else:
        if args.image_path is not None:
            if os.path.exists(args.image_path):
                blurred, gray_img = load_image(args.image_path, show=args.show_image, isLevels=True)
                output = blurred
                dst = preprocess(blurred, THRESHOLD, show=args.show_image)
                digits_positions = find_digits_positions(dst)
                digits = recognize_digits_line_method(digits_positions, output, dst)
                value=numstr(digits,numbers,decimals)
                print("Digits:",digits)
                print("Value: ",value)
                if args.show_image:
                    cv2.imshow('output', output)
                    cv2.waitKey()
            else:
                print("File not found!")
        else:
            print("Filename not specified as an argument.")

    if True in [args.capture_image,args.real_time_logger]:
        cap.release()

    # All these waitkeys are a hack to get the OpenCV window to close
    cv2.waitKey(1)
    cv2.destroyAllWindows()
    for i in range (1,5):
        cv2.waitKey(1)
    
    if len(results)>1:
        # Create data filename
        fname="numlog"+t0.strftime("%Y%m%d_%H%M%S")
        header=results[0]
        data=results[1:]
        # Save the data
        with open(curdir+"/"+fname+".csv","w",newline="\n") as csvfile:
            writer=csv.writer(csvfile,delimiter=',',quotechar='"')
            writer.writerow(header)
            writer.writerows(data)
        # Create a data plot and save it
        ar=np.array(data).T
        if args.batch_ocr:
            if decimals_batch==0:
                xs=ar[cursor+0].astype(int)
            else:
                xs=ar[cursor+0].astype(float)
        else:
            if interval_mode and interval>0:
                xs=ar[cursor+0].astype(int)
            else:
                xs=ar[cursor+0].astype(float)
        try:
            ys=ar[cursor+1].astype(float)
            fig=plt.figure()
            plt.xlim(xs[0],xs[-1])
            plt.plot(xs,ys)
            plt.xlabel(header[cursor+0])
            plt.ylabel(header[cursor+1])
            plt.savefig(curdir+"/"+fname+".png", dpi=300)
        except:
            print("Missing y data. Plot not created!")
        plt.close()
        
        # Save a log file
        alist=[]
        with open(fname+".log", 'w') as f:
            f.write("Log name: "+fname+"\n\n")
            f.write("Image name: ")
            if args.image_path is not None:
                f.write(args.image_path)
                alist.append(args.image_path)
            f.write("\n\n")
            f.write("Batch OCR       : ")
            if args.batch_ocr:
                f.write("Enabled")
                alist.append("-b")
            else:
                f.write("-")
            f.write("\n")
            f.write("Capture image   : ")
            if args.capture_image:
                f.write("Enabled")
                alist.append("-c")
            else:
                f.write("-")
            f.write("\n")
            f.write("Real-time logger: ")
            if args.real_time_logger:
                f.write("Enabled")
                alist.append("-r")
            else:
                f.write("-")
            
            if args.real_time_logger:
                f.write("\n\n")
                f.write("Interval mode   : ")
                if interval_mode:
                    f.write("Yes\n")
                    f.write("Interval        : "+str(interval)+" "+unit+"\n")
                else:
                    f.write("No\n")
                    f.write("Log all values  : ")
                    if log_all:
                        f.write("Yes")
                    else:
                        f.write("No")
                    f.write("\n")
            elif args.batch_ocr:
                f.write("\n\n")
                f.write("Unit                : "+unit+"\n")
                f.write("Extension           : "+ext+"\n")
                f.write("Start pass filter   : "+filter_start+"\n")
                f.write("Interval            : "+str(interval)+" "+unit+"\n")
                f.write("Start time          : "+str(start_time)+" "+unit+"\n")
                f.write("Add filename column : ")
                if saveNames:
                    f.write("Yes")
                else:
                    f.write("No")
                f.write("\n")
                        
            f.write("\n")
            f.write("Inverse display : ")
            if args.inverse_display:
                f.write("Yes")
                alist.append("-i")
            else:
                f.write("No")
            f.write("\n")
            f.write("H/W ratio       : "+str(float(H_W_Ratio)))
            if args.hw_ratio is not None:
                tmp=float(args.hw_ratio)
                if tmp.is_integer:
                    tmp=int(args.hw_ratio)
                alist.append("-hw "+str(tmp))
            f.write("\n")
            f.write("Tilt angle      : "+str(float(arc_tan_theta)))
            if args.tilt_angle is not None:
                alist.append("-a "+str(int(args.tilt_angle)))
            f.write("\n")
            f.write("Threshold       : "+str(int(THRESHOLD)))
            if args.threshold is not None:
                alist.append("-t "+str(int(args.threshold)))
            f.write("\n\n")
            
            f.write("Digits     : ")
            if args.digits is not None:
                f.write(str(int(args.digits)))
                alist.append("-n "+str(int(args.digits)))
            else:
                f.write("-")
            f.write("\n")
            f.write("Decimals   : ")
            if args.decimals is not None:
                f.write(str(int(args.decimals)))
                alist.append("-p "+str(int(args.decimals)))
            else:
                f.write("-")
            f.write("\n\n")
            
            f.write("Black point: ")
            if args.bp is not None:
                f.write(str(int(args.bp)))
                alist.append("-bp "+str(int(args.bp)))
            else:
                f.write("-")
            f.write("\n")
            f.write("White point: ")
            if args.wp is not None:
                f.write(str(int(args.wp)))
                alist.append("-wp "+str(int(args.wp)))
            else:
                f.write("-")
            f.write("\n")
            f.write("Gamma      : ")
            if args.gamma:
                f.write(str(float(args.gamma)))
                alist.append("-gamma "+str(float(args.gamma)))
            else:
                f.write("-")
            f.write("\n\n")

            f.write("Show image : ")
            if args.show_image:
                f.write("Yes")
                alist.append("-s")
            else:
                f.write("No")
            f.write("\n")    
            f.write("Debug      : " )
            if args.is_debug:
                f.write("Yes")
                alist.append("-d")
            else:
                f.write("No")
            f.write("\n\n")
            
            f.write("Command:\n")
            tmp=""
            for item in alist:
                tmp+=item
                tmp+=" "
            tmp=tmp.strip()
            if len(tmp)>0:
                f.write("numlog.py "+tmp+"\n")
    else:
        if True in [args.real_time_logger,args.batch_ocr]:
            print("\nNo data to save or to create a plot.")    
        
if __name__ == '__main__':
    main()
