#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Created on Tue Mar  7 10:01:56 2023

@author: Kim Miikki

Thermal ASC data files parser and converter to CSV files

ASC filename:
irdata_000m_nnn.asc
    
ASC file structure :
[Settings]
Version=3
ImageWidth=482
ImageHeight=480
ShotRange=16.85;36.85
CalibRange=-20.00;150.00
TempUnit=°C
StartPos=51;0
EndPos=532;479

[Data]
24,29	24,29	24,25

'''

import argparse
import codecs
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

separator='\t'


isExt=False
isSubdir=True

min_digits=4
in_ext='.asc'
out_ext='.txt'
newdir='files'

print("Thermal ASC data parser and converter to CSV format - (C) Kim Miikki 2023")

# Get current directory
curdir = os.getcwd()
path = Path(curdir)
print('')
print('Current directory:')
print(curdir)
print('')
if curdir != '/':
    curdir += '/'

parser = argparse.ArgumentParser()
parser.add_argument('-ext', help='ASC file extension (.ext, ext or .= no extension)', type=str, required=False)
parser.add_argument('-c', action='store_true', help='store output files in current directory', required=False)
args = parser.parse_args()

if args.ext != None:
    tmp=args.ext
    tmp=tmp.lower()
    if tmp=='':
        tmp='.'
    if tmp[0]!='.':
        tmp='.'+tmp
    in_ext=tmp

if args.c:
    isSubdir=False
    newdir=''

outdir=curdir+newdir

if isSubdir:
    try:
        if not os.path.exists(outdir):
            os.mkdir(outdir)
    
    except OSError:
        print("Unable to create a directory or directories under following path:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)

# Find all ASC files
infiles=[]
for name in sorted(path.iterdir()):
    if name.is_file():
        if name.suffix.lower()==in_ext:
            infiles.append(name.name)
        elif name.suffix=='' and in_ext=='.' and (not name.name[-1]=='.'):
            # Do not accept filnames of this type: stem.
            # Accept if type is: stem
            infiles.append(name.name)
files=len(infiles)
digits=len(str(files))
if digits<min_digits:
    digits=min_digits

if len(in_ext)>1: 
    print(in_ext[1:].upper()+' files found: '+str(files))
else:
    print('Input files found: '+str(files))

# Parse all files in the list
i=0
t1=datetime.now()
print('')
print('Processing:')
log=[]
for ifile in infiles:
    with codecs.open(ifile,'r',encoding='utf-8',errors='ignore') as f:
        print(ifile+' ',end='')
        isData=False
        rows=[]
        error=False
        cs=0
        rs=0
        for line in f:
            row=line.strip()
            if row=='[Data]':
                isData=True
                continue
            if not isData:
                continue
            row=row.replace(',','.')
            row=row.replace(separator,',')
            row=row.split(',')
            columns=len(row)
            if cs==0 and columns>0:
                cs=columns
            elif cs>0 and cs != columns:
                error=True
                i+=1
                print('Fail')
                log.append([ifile,'Fail'])
                break
            rows.append(row)
    if not error:
        csvname=str(i).zfill(digits)+out_ext
        if isSubdir:
            csvname=newdir+'/'+csvname
        with open(csvname, "w") as f:
            write = csv.writer(f)
            write.writerows(rows)
            log.append([ifile,csvname])
        i+=1
        print('-> '+csvname)

if len(log)>0:
    tmp='files.log'
    if isSubdir:
        tmp=newdir+'/'+tmp
        with open(tmp,'w') as f:
            write=csv.writer(f)
            write.writerows(log)
        
t2=datetime.now()
print("")
print("Time elapsed: "+str(t2-t1))