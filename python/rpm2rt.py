#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Progra name: rpm2rt (RPM to Revolution Time)
Created on Thu Sep  2 08:44:15 2021

@author: Kim
"""
# Include standard modules
import getopt, sys

s_decimals=4
ms_decimals=2
my_decimals=0

allUnits=False
bareTime=False
isOk=True

def rtime(rpm,unit="s"):
    # units: s ,ms and µs
    # RPM = 1/min
    # 1/RPM = 1 min = 60 s
    rt=60/rpm # Revolution time in s
    decimals=s_decimals
    if unit=="ms":
        rt*=1000
        decimals=ms_decimals
    elif unit=="µs":
        rt*=1e6
        decimals=my_decimals
    
    if decimals<1:
        return str(round(rt))
    else:
        rt=str(round(rt,decimals))
        pos=rt.rfind(".")
        rt=rt+"0"*(decimals-len(rt[pos+1:]))
        return rt

# Get full command-line arguments
full_cmd_arguments = sys.argv

# Keep all but the first
argument_list = full_cmd_arguments[1:]


if len(argument_list)==0 or "-h" in argument_list:
    print("Usage: rpm2rt.py RPM [-a] [-b] [-h]")
    print("")
    print("positional arguments:")
    print("  RPM"+" "*9+"revolutions per minute (integer value)")
    print("")
    print("optional arguments:")
    print("  -h"+" "*10+"show this help message and exit")
    print("  -a"+" "*10+"print all units")
    print("  -b"+" "*10+"print the bare time value in seconds")
else:       
    # search for an integer in the argument list
    count=0
    value=-1
    errors=[]
    for v in argument_list:
        if v=="-a":
            allUnits=True
            continue
        elif v=="-b":
            bareTime=True
            continue
        else:
            try:
                value=float(v)
                if value.is_integer():
                    value=int(value)
                    count+=1
                else:
                    errors.append("Value "+str(value)+" is discarded")
            except:
                pass

    if not bareTime:
        print("RPM to Revolution Time")
        if len(errors)>0:
            for line in errors:
                print(line)
        
    if count!=1:
        print("\nOne positional argument as integer is required!")
        print("Provided integers: "+str(count))
        isOk=False
    
    if not False in [allUnits,bareTime]:
        print("Select only -a or -b")
        isOk=False
    
    if isOk and value<=0:
        print("Invalid RPM value (=<0)")
        isOk=False
    
    if isOk:
        list=[]
        if allUnits:
            print("")
            print("RPM: "+str(value))
            print("")
            print("=>")
            list.append([rtime(value,"s"),"s"])
            list.append([rtime(value,"ms"),"ms"])
            list.append([rtime(value,"µs"),"µs"])
        elif bareTime:
            print(rtime(value,"s"))
        else:
            list.append([rtime(value,"ms"),"ms"])
        if len(list)>0:
            print("")
            print("Revolution time:")
            # Get max number length
            maxl=0
            for v,u in list:
                l=len(v)
                if l>maxl:
                    maxl=l
            # Print formated numbers
            for v,u in list:
                l=len(v)
                print(" "*(maxl-l)+v+" "+u)

