#!/usr/bin/python3
# (C) Kim Miikki 2020

import csv
from pathlib import Path

roi_decimals=4
roi_delimiter=";"
roi_filename="roi.ini"
roi_file_exists=False
roi_img_x0=0
roi_img_y0=0
roi_img_x1=0
roi_img_y1=0
roi_crop_x0=0
roi_crop_x1=0
roi_crop_y0=0
roi_crop_y1=0
roi_x0=0
roi_y0=0
roi_w=0
roi_h=0
roi_dir=""
roi_errors=[]

roilist=[]

roi_dict={
    "img_x0":0,
    "img_x1":0,
    "img_y0":0,
    "img_y1":0,
    "crop_x0":0,
    "crop_x1":0,
    "crop_y0":0,
    "crop_y1":0,
    "roi_x0":0,
    "roi_y0":0,
    "roi_w":0,
    "roi_h":0}

def dict_to_int(key):
    return int(roi_dict[key])

def dict_to_float(key):
    return float(roi_dict[key])

def roix(value,width):
    return round(value/width,roi_decimals)

def roiy(value,height):
    return round(value/height,roi_decimals)
    
def validate_img_crop():
    # Validate image and crop values
    
    img_x0=int(roi_dict["img_x0"])
    img_y0=int(roi_dict["img_y0"])
    img_x1=int(roi_dict["img_x1"])
    img_y1=int(roi_dict["img_y1"])
    crop_x0=int(roi_dict["crop_x0"])
    crop_y0=int(roi_dict["crop_y0"])
    crop_x1=int(roi_dict["crop_x1"])
    crop_y1=int(roi_dict["crop_y1"])

    error_list=[]

    if img_x0<0:
        error_list.append("img_x0 < 0")
    elif img_x1<=img_x0:
        error_list.append("img_x1 <= img_x0")
    if img_y0<0:
        error_list.append("img_y0 < 0")
    elif img_y1<=img_y0:
        error_list.append("img_y1 <= img_y0")

    elif crop_x0<img_x0 or crop_x0>(img_x1):
        error_list.append("crop_x0 out of range")
    elif crop_x1<(img_x0+1) or crop_x1>(img_x1):
        error_list.append("crop_x1 out of range")
    elif crop_x0>=crop_x1:
        error_list.append("crop_x0 >= crop_x1")
        
    elif crop_y0<img_y0 or crop_y0>(img_y1-1):
        error_list.append("crop_y0 out of range")
    elif crop_y1<(img_y0+1) or crop_y1>(img_y1):
        error_list.append("crop_y1 out of range")
    elif crop_y0>=crop_y1:
        error_list.append("crop_y0 >= crop_y1")
    return error_list

def validate_roi_values():
    if roi_file_exists:            
        roi_errors=validate_img_crop()
        if len(roi_errors)>0:
            print("Invalid coordinates:")
            for item in roi_errors:
                print(item)
            exit(0)
        return True
    else:
        return False


def dict_to_localvariables():
    # Copy roi_dict values to image and crop variables
    global roi_img_x0
    global roi_img_y0
    global roi_img_x1
    global roi_img_y1
    global roi_crop_x0
    global roi_crop_x1
    global roi_crop_y0
    global roi_crop_y1
    global roi_x0
    global roi_y0
    global roi_w
    global roi_h

    roi_img_x0=dict_to_int("img_x0")
    roi_img_x1=dict_to_int("img_x1")
    roi_img_y0=dict_to_int("img_y0")
    roi_img_y1=dict_to_int("img_y1")
    roi_crop_x0=dict_to_int("crop_x0")
    roi_crop_x1=dict_to_int("crop_x1")
    roi_crop_y0=dict_to_int("crop_y0")
    roi_crop_y1=dict_to_int("crop_y1")
    roi_x0=dict_to_float("roi_x0")
    roi_w=dict_to_float("roi_w")
    roi_y0=dict_to_float("roi_y0")
    roi_h=dict_to_float("roi_h")

def read_roi_file(filename,file_path=""):
        
    # Template
    # scale; coordinate name; value
    # original;img_x1;4055
    # original;crop_x1;1920 
    # normalized;x1;1.0
    result=False
    if len(file_path)>0:
        filename=file_path+"/"+filename
    try:
        with open(filename,"r",newline="") as csvfile:
            csvreader=csv.reader(csvfile,delimiter=";")
            for row in csvreader:
                if row[1] in roi_dict:
                    roi_dict[row[1]]=row[2]
            dict_to_localvariables()
            result=True
    except:
        result=False
    return result

def display_roi_status():
    if roi_dir!="":
        print("ROI file found in "+roi_dir+" directory: "+str(roi_x0)+","+str(roi_y0)+","+str(roi_w)+","+str(roi_h))
    else:
        print("ROI file not found!")

# Get current path
p=Path(".").resolve()

roi_file_exists=read_roi_file(roi_filename)
if roi_file_exists:
    roi_dir="current"
else:
    # Check if roi.ini exists in parent path
    pp=p.parent.resolve()   
    if pp!=p:
        roi_file_exists=read_roi_file(str(pp)+"/"+roi_filename)
    if roi_file_exists:
        roi_dir="parent"

if roi_file_exists:
    dict_to_localvariables()
