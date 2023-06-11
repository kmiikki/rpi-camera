#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 21:39:44 2023

@author: Kim Miikki 2023

File format: awbgains-trials-XXX.csv
Columns: calibration,rgain(0),bgain(0),rgain_opt,bgain_opt,distance,evaluations,position,time (s)
Required columns: rgain_opt,bgain_opt

"""

import glob
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
import scipy.stats as st

max_series=5
n_series=0
series=[]
trials=0
p=0.95
crop_trials=True
markers=['o','s','D','*','P']
colors=['b','r','g','k','gray']

startpass_filter='awbgains-trials-'
keys=['rgain_opt','bgain_opt']

rgb_decimals=3
isShow=False

def generate_xlist(number):
    n=int(number)
    xlist=[]
    if number<=10:
        xlist=list(range(0,n+1)) 
    elif number<=50:
        i=n
        while i % 5 != 0:
            i+=1
        xlist=list(range(0,i+1,5))
    elif number<=100:
        i=n
        while i % 10 != 0:
            i+=1
        xlist=list(range(0,i+1,10))
    return xlist[1:]

print('Optimal AWB plotter - (C) Kim Miikki 2023')
print('')

print('Current directory:')
curdir=os.getcwd()
path=Path(curdir)
print(curdir)
if curdir[-1] != '/':
    curdir+='/'
print('')

# Search for valid series
csv_files=sorted(glob.glob(startpass_filter+'*.csv'))
for name in csv_files:
    if n_series>=max_series:
        break
    result=False
    try:
        df=pd.read_csv(name)
    except:
        pass
    required_keys=True
    c=0
    for key in keys:
        if key not in df.keys():
            required_keys=False
            break
        else:
            c+=1
    if c==len(keys):
        result=True
    if not result:
        print (name+': invalid data file')
    else:
        rgains=list(df['rgain_opt'])
        bgains=list(df['bgain_opt'])
        if len(rgains) == len(bgains):
            if len(rgains)>1:
                length=len(rgains)
                series.append([rgains,bgains])
                n_series+=1
                if trials==0:
                    trials=length
                elif length<trials:
                    trials=length
                print('Series '+str(n_series)+' trials: '+str(length))
if n_series>0:
    print('Series common trials count: '+str(trials))
else:
    print('No valid series found!')
    sys.exit(0)
                
# Calculate CIs and plot all series
fig=plt.figure()
ax=fig.add_subplot(111)
plt.ylabel('rgain')
plt.xlabel('bgain')
plt.grid()

i=0
max_n=0
while i<n_series:
    r_gains=series[i][0]
    b_gains=series[i][1]
    if crop_trials:
        # Crop the data
        r_gains=r_gains[:trials]
        b_gains=b_gains[:trials]
    
    N=len(rgains)
    if N>max_n:
        max_n=N
    method=''
    if N>1 and N<=30:
        # Use Student-t distribution
        method="Student's t-distribution"
        #if (use_scipy_confidence()):
        ci_rgain=st.t.interval(p, df=N-1,
                  loc=np.mean(r_gains),
                  scale=st.sem(r_gains))
        ci_bgain=st.t.interval(p, df=N-1,
                  loc=np.mean(b_gains),
                  scale=st.sem(b_gains))
    elif N>30:
        # Use normal distribution
        method='Normal distribution'
        ci_rgain=st.norm.interval(alpha=p,
                  loc=np.mean(r_gains),
                  scale=st.sem(r_gains))
        ci_bgain=st.norm.interval(alpha=p,
                  loc=np.mean(b_gains),
                  scale=st.sem(b_gains))
    rmean=np.mean(r_gains)
    bmean=np.mean(b_gains)
    frmean=round(np.mean(r_gains),rgb_decimals)
    fbmean=round(np.mean(b_gains),rgb_decimals)
    
    # Plot a series optimal gains
    plt.plot(b_gains,r_gains,markers[i],markerfacecolor=colors[i],markeredgecolor=colors[i], label='Series '+str(i+1))
    
    # Draw CI rectangle
    rect=matplotlib.patches.Rectangle((ci_bgain[0],ci_rgain[0]),
                                      ci_bgain[1]-ci_bgain[0],
                                      ci_rgain[1]-ci_rgain[0],
                                      facecolor=colors[i],
                                      edgecolor=colors[i],
                                      alpha=0.2)
    ax.add_patch(rect)
    plt.plot(np.mean(b_gains),np.mean(r_gains),'+',color=colors[i],markerfacecolor='None')
    
    i+=1

ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M%S')
figfile=curdir+'awbgains-ci-'+dt_part+'.png'
plt.legend()
plt.savefig(figfile,dpi=300)
if isShow:
    plt.show()              