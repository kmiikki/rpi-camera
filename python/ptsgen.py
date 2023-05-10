#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 18 16:37:30 2023

@author: Kim Miikki
"""

import argparse
import numpy as np
import os
from datetime import datetime
from pathlib import Path

project='video'
pts_name='video.pts'
ext='.txt'
separator=','

is_mtime=True   # Primary method: modified time
is_zero=False   # Adjust start time to 0
is_both=False   # Export data with 2 time columns
is_fnames=False # Export data with filenames

def get_pts_from_files(directory_path,ext):
    ext_files = [f for f in sorted(os.listdir(directory_path)) if f.endswith(ext)]
    modified_times = []
    
    for f in ext_files:
        file_path = os.path.join(directory_path, f)
        stat_info = os.stat(file_path)
        modify_time = round(stat_info.st_mtime_ns / 1000000, 3)  # convert to milliseconds
        modified_times.append(modify_time)    

    return modified_times,ext_files

def save_pts_file(pts_list, file_names, name, both=False):
    file_path=os.path.join(curdir, name)
    with open(file_path, 'w') as f:
        i=0
        
        # Header section
        header=''
        
        # Column 1
        if is_fnames:
            header='Filename'
            header+=separator
        
        # Column 2
        header+='# timecode format v2'
        
        # Column 3
        if is_both:
            header+=separator
            header+='Datetime'
        f.write(header+'\n')
        
        for pts in pts_list:
            tmp=''
            if is_fnames:
                tmp=file_names[i]+separator
            
            # Add pts column
            tmp+=str(pts)
            
            # Add second data column
            if both:
                dt=datetime.fromtimestamp(pts/1000).strftime('%Y-%m-%d %H:%M:%S')
                tmp+=separator
                tmp+=dt
            tmp+='\n'

            f.write(tmp)
            i+=1

def last_number_pos(s):
    ''' Return the position where the last number starts in a string and
        the length of the number. Return (-1, -1) if no number is found.
        String should as a filename: 'stem.ext'.
    '''
    numpos=-1
    length=-1
    ext_length=4
    stem=s[:len(s)-ext_length]
    
    i=0
    for ch in reversed(stem):
        if not ch.isdigit():
            break
        i+=1
        
    if i>0:
        numpos=len(s)-(ext_length+i)
        length=i
    
    return numpos, length

parser=argparse.ArgumentParser()
parser.add_argument('-name', type=str, help='project name (default=video)',required=False)
parser.add_argument('-ext',type=str,help='specify extension (default=txt)',required=False)
parser.add_argument('-z',action='store_true',help='start time: 0',required=False)
parser.add_argument('-f',action='store_true',help='export filenames',required=False)
parser.add_argument('-two',action='store_true',help='export two columns',required=False)
args = parser.parse_args()

if args.name != None:
    stem=Path(args.name).stem
    if len(stem)>0:
        pts_name=stem+'.pts'

if args.ext != None:
    tmp=args.ext
    if tmp[0]!='.':
        tmp='.'+tmp
    ext=tmp

if args.z:
    is_zero=True

if args.f:
    is_fnames=True

if args.two:
    is_both=True

print('Generate a PTS file from mtimes')

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print('')

files_pts,fnames=get_pts_from_files(curdir, ext)

# Get first stem without number and '-', '_' or' '
sample=fnames[0]
npos, nlen = last_number_pos(sample)

if args.name == None:
    if npos > 0:
        str_start=Path(sample).stem[:npos]
        chars=['-', '_', ' ']
        if str_start[-1] in chars:
            str_start=str_start[:-1]
        pts_name=str_start+'.pts'

if is_zero:
    files_pts=np.array(files_pts)
    files_pts-=files_pts[0]
    files_pts=np.round(files_pts,3)
    #files_pts=list(files_pts)
save_pts_file(files_pts, fnames, pts_name, is_both)
    
print('File '+pts_name+' generated with '+str(len(files_pts))+' rows of data.')
