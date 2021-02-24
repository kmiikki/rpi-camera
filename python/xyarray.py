#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 22 13:30:30 2021

@author: Kim Miikki

Usage:
Combine two data list to one file array

Arguments:
name1.pts = First argument is a PTS file for x-axis
name1     = First argument is x-axis data file
name2     = Second argument is y-axis data file

Header line is omitted if extension for name1 os pts. Default unit string for
a PTS file is: Time [ms]

Other extensions and name2:
Unit [u] or Unit (u)
y1
y2
y3

x and y data are numbers in float format

Typical xydata array:
Unit1 [u1],Unit2 [u2]
x1,y1
x2,y1
x3,y3
...

"""
import os
import sys
from pathlib import Path
from rpi.inputs2 import *

def get_label(text,unit,brackets):
    if len(text)==0:
        return ""
    text=text[0].upper()+text[1:]
    text+=" "
    if brackets=="()":
        text+="("+unit+")"
    else:
        text+="["+unit+"]"
    return text

def get_label_u(text,brackets):
    br=bracket_type[0]
    a=text.find(br[0])
    b=text.rfind(br[1])
    if a<0 and b<0:
        br=bracket_type[1]
        a=text.find(br[0])
        b=text.rfind(br[1])
    unit=""
    label=""
    if a>=0 and b>a:
        label=text[:a]
        unit=text[a+1:b]
    if len(label):
        label=text[0].upper()+label[1:]
        label=label.strip()
    if len(unit)>0:
        label+=" "
        if brackets=="()":
            label+="("+unit+")"
        else:
            label+="["+unit+"]"
    return label

outfile="xydata.csv"
xlabel=""
ylabel=""
ptslabel="Time"
ptsunit="ms"
isPTS=False
errors=[]
xs=[]
ys=[]
xys=[]

bracket_type=["()","[]"]
brackets="[]"

print("xyarray - concate x and y data into a single array")
curdir=os.getcwd()
path=Path(curdir)
print("")
print("Current directory:")
print(curdir)
print("")

a=sys.argv
args=len(a)
out=None
in1=None
in2=None
if args!=3:
    errors.append("Incorrect number of arguments")
else:
    if a[1].lower().endswith(".pts"):
        isPTS=True
    try:
        in1=open(a[1],"r")
        xs=in1.readlines()
    except:
        errors.append("Unable to open file: "+a[1])
    try:
        in2=open(a[2],"r")
        ys=in2.readlines()
    except:
        errors.append("Unable to open file: "+a[2])
    try:
        out=open(outfile,"w")
    except:
        errors.append("Unable to open "+outfile)

if len(xs)<2 and in1 is not None:
    errors.append("File 1: At least two x rows are required (header + x1)")
if len(ys)>len(xs):
    errors.append("Data y rows > x rows")
if len(ys)<2 and in2 is not None:
    errors.append("File 2: At least two y rows are required (header + y1)")

if len(errors)==0 and len(xs)>1:
    brackets=inputListValue("bracket type",bracket_type,brackets,"Not valid brackets",True)
    print("")
    i=0
    j=0
    for x in xs:
        x=x.strip()
        if i<len(ys):
            y=ys[i]
            y=y.strip()
        else:
            errors.append("Data y rows < x rows")
            print("No more y data. List is cut at row: "+str(i))
            break
        if i==0:
            if isPTS:
                xlabel=get_label(ptslabel,ptsunit,brackets)
            else:
                xlabel=get_label_u(x,brackets)
            ylabel=get_label_u(y,brackets)
            x=xlabel
            y=ylabel
        #print(x+","+y)
        out.write(x+","+y+"\n")
        i+=1
    print(outfile+": "+str(i)+" data rows merged")
else:
    print("Unable to merge data!")
    print("")

if len(errors)>0:
    print("Issues:")
    for row in errors:
        print(row)

if out is not None:
    out.close()
if in2 is not None:
    in2.close()
if in1 is not None:
    in1.close()