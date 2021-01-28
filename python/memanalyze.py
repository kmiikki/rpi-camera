#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 24 23:46:39 2021

@author: Kim Miikki
"""

import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

units=["s","min","h","d"]

def parseRow(row):
    s=row.split()
    date_time=s[0]+" "+s[1]
    dt=datetime.strptime(date_time,"%Y-%m-%d %H:%M:%S")
    data=[]
    data.append(dt)
    for i in range(2,len(s)):
        data.append(int(s[i]))
    return data

def unit(time):
    divisor=1
    unit=0
    # Minutes
    if time/60>=5:
        unit+=1
        divisor*=60
    # Hours
    if time/(60*60)>=5:
        unit+=1
        divisor*=60
    # Days
    if time/(60*60*24)>=5:
        unit+=1
        divisor*=24   
    return units[unit],divisor

labels=[]
logfile="meminfo.log"

lines=0
table=[]

print("Memory Log File Analyzer")
print("")
print("Analyzing "+logfile)
for row in open(logfile):
    # Header line
    if lines==0:
        labels=row.split()
        lines+=1
        continue
    table.append(parseRow(row))
    lines+=1
rows=len(table)
start=table[0][0]
end=table[rows-1][0]
t=(end-start).seconds
interval=round(t/(rows-1))
u,divisor=unit(t)
t_unit=t/divisor



# Create a numpy array from available columns
arr=np.array(table).T
xs=np.linspace(0,t_unit,len(table))

invalid = '<>:"/\|?* '

print("")
print("Saving files:")
for i in range(1,len(arr)):
    label=labels[i+1]
    ytext=label[0].upper()+label[1:]+" [MB]"
    fig=plt.figure()
    plt.plot(xs,arr[i])
    plt.xlim(0,xs[len(table)-1])
    plt.xlabel("Time ["+u+"]")
    plt.ylabel(ytext)
    for char in invalid:
        label=label.replace(char, '-')
    plt.savefig("meminfo-"+label+".png",dpi=300)
    # plt.show()
    plt.close(fig)
    print(str(round(i/(len(arr)-1)*100)).rjust(3," ")+" % done")