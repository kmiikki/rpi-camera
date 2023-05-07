#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Wed Mar  8 19:19:01 2023

@author: Kim Miikki
'''

import argparse
import csv
import numpy as np
import os
import sys
from datetime import datetime
from pathlib import Path
from pathlib import PurePath

np.set_printoptions(suppress=True)

roiname='roixy.ini'

in_ext='.txt'
out_ext='.txt'
out_dir='crop'
is_numbering=False

start_filter=''

def get_roixy_dir(curdir,fname):
    level=-1
    
    # Check if fname exists in current directory
    cur_dir=PurePath(curdir)
    tmp='/'
    if str(cur_dir)=='/':
        tmp=''
    if Path(str(cur_dir)+tmp+fname).is_file():
        level=0
        return curdir, level
    
    # Check if fname exists in parent directory
    parent_dir=PurePath(curdir).parent
    tmp='/'
    if str(parent_dir)=='/':
        tmp=''
    if Path(str(parent_dir)+tmp+fname).is_file():
        level=1
        return curdir, level
    
    # File not found
    return '', level
    
    
print('ROIXY batch crop utility - (C) Kim Miikki 2023')

# Get current directory
curdir = os.getcwd()
path = Path(curdir)
print('')
print('Current directory:')
print(curdir)
print('')
if curdir != '/':
    curdir += '/'
    
# Try to find the roixy.ini file
roi_path, level = is_roixy_file=get_roixy_dir(curdir,roiname)
if level>=0:
    print('File '+roiname+' found in ',end='')
    if level==0:
        print('current directory.')
    else:
        print('parent directory.')
else:
    print('No '+roiname+' found.')
    sys.exit(0)
    
# Read ini file into a dictionary
roidict={}
try:    
    with open(roi_path+roiname, mode='r') as infile:
        reader = csv.reader(infile)
        for row in reader:
           k, v = row
           roidict[k] = int(v)
except:
    print('Unable to read the '+roiname+'.')
    sys.exit(0)

# Validate that all keys exists and values are >= 0
keys=['width','height','roi_x0','roi_y0','roi_w','roi_h']
is_ok=True
for key in keys:
    if key in roidict.keys():
        if roidict[key]<0:
            is_ok=False
            break
if not is_ok:
    print('Invalid '+roiname+'.')
    sys.exit(0)

roi_x0=roidict['roi_x0']
roi_y0=roidict['roi_y0']
roi_w=roidict['roi_w']
roi_h=roidict['roi_h']

try:
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
except OSError:
    print("Unable to create a directory or directories under following path:\n"+curdir)
    print("Program is terminated.")
    print("")
    sys.exit(1) 

parser = argparse.ArgumentParser()
parser.add_argument('-ext', help='data file extension (.ext, ext or .= no extension)', type=str, required=False)
parser.add_argument('-s', help='start pass filter for data files', type=str, required=False)
parser.add_argument('-n', action='store_true', help='use consequent numbering for output files', required=False)
args = parser.parse_args()

if args.ext != None:
    tmp=args.ext
    tmp=tmp.lower()
    if tmp=='':
        tmp='.'
    elif tmp[0]!='.':
        tmp='.'+tmp
    in_ext=tmp

if args.s != None:
    start_filter=str(args.s)

if args.n:
    is_numbering=True

if len(out_dir)>0:
    if out_dir[-1] != '/':
        out_dir+='/'
        
if len(out_ext)>0:
    if out_ext[0] != '.':
        out_ext='.'+out_ext

# Create a list of all data files
data_files=[]
for name in sorted(path.iterdir()):
    if name.is_file():
        if len(start_filter)>0:
            if str(name.name).find(start_filter) != 0:
                continue
        if name.suffix.lower()==in_ext:
            data_files.append(name.name)
        elif name.suffix=='' and in_ext=='.' and (not name.name[-1]=='.'):
            # Do not accept filnames of this type: stem.
            # Accept if type is: stem
            data_files.append(name.name)
print('Data files found: '+str(len(data_files)))
digits=len(str(len(data_files)))
if digits<4:
    digits=4

if len(data_files)>0:
    # Read data files to numpy arrays, crop and then save the cropped arrays as CSV files
    i=0
    ok=0
    t1=datetime.now()
    print('')
    print('Processing:')
    for infile in data_files:
        # Generate output filename
        if is_numbering:
            stem=str(i).zfill(digits)
        else:
            stem=Path(infile).stem
        outfile=curdir+out_dir+stem+out_ext
        
        # Read data file
        data = np.genfromtxt(infile, delimiter=',')
        h,w=data.shape
        
        is_ok=True
        if roi_x0>w-1:
            is_ok=False
        if roi_y0>h-1:
            is_ok=False
        
        # Trim crop dimensions to fit
        roi_x1=roi_x0+roi_w-1
        roi_y1=roi_y0+roi_h-1
        if  roi_x1 > w-1:
            roi_x1=w-1
        if roi_y1 > h-1:
            roi_y1=h-1
        if roi_x1 <= roi_x0:
            is_ok=False
        if roi_y1 <= roi_y0:
            is_ok=False
        
        if is_ok:
            print(infile)
            # Crop the data matrix
            crop = data[roi_y0:roi_y1+1,roi_x0:roi_x1+1]
            # Save the cropped data
            np.savetxt(outfile, crop, delimiter=',', fmt='%g')
            ok+=1
        else:
            print('Unable to crop: '+infile)
            
        i+=1
    
    t2=datetime.now()
    print("")
    print('Files processed: '+str(ok))
    print("Time elapsed: "+str(t2-t1))
