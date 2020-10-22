#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Real time graph of image sharpness
Method: Variance of the Laplacian

Requirements: Client and server has to be ran in the same directory
Role:         Client
Server:       capture-sharpness.py

Created on Thu Oct 21 2020

@author: Kim Miikki
"""

import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.animation as animation
import pathlib

MAX_VALUES=20

serverFound=False
notification=False

def animate(i,xs,ys):   
    global notification
    global serverFound
    
    var=read_variance()
    if var<0:
        if (not notification) and (not serverFound):
            print("Waiting for server...")
            notification=True
        return
    if not serverFound:
        print("Server found and monitoring started.")
        serverFound=True
    xs.append(i)
    ys.append(var)
    xs=xs[-MAX_VALUES:]
    ys=ys[-MAX_VALUES:]
    ax.clear()
    plt.title("Variance of the Laplacian")
    plt.xlabel("t [s]")
    plt.ylabel("Variance")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.plot(xs,ys)

def read_variance():
    # List '-var;' files in current directory
    for file in curdir.glob(searchPattern):
        if file.name!="":
            tmp=file.name
            break
    try:
        pos=tmp.rfind(delimiter)
        tmp=tmp[pos+1:]
        variance=float(tmp)
    except:
        variance=-1
    return variance

curdir=pathlib.Path(".")    
searchPattern="_var;*"
delimiter=";"

print("Sharpness live graph monitor")
print("")
print("Data source directory: ",end="")
path = os.getcwd()
print(path)

# Create figure for plotting
fig=plt.figure("Image Sharpness Monitor")
ax=fig.add_subplot(1,1,1)
xs=[]
ys=[]


# Start animation
ani=animation.FuncAnimation(fig,animate,fargs=(xs,ys),interval=500)
plt.show()
