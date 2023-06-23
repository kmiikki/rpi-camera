#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 21:39:44 2023

@author: Kim Miikki 2023

File format: awbgains-trials-XXX.csv
Columns: calibration,rgain(0),bgain(0),rgain_opt,bgain_opt,distance,evaluations,position,time (s)
Required columns: rgain_opt,bgain_opt

"""

import argparse
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import scipy.stats as stats
from scipy.stats import chi2
from scipy.stats import norm
from scipy.stats import shapiro
import seaborn as sns
import statsmodels.api as sm

isShow=False
max_series=1
n_series=0
series=[]
trials=0
p=0.95

method_names=[]
startpass_filter='awbgains-trials-'
keys=['rgain_opt','bgain_opt']

decimals=3
isShow=False
isSave=True

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

def calculate_tolerance_interval(data, p, proportion):
    alpha = 1-p
    n = len(data)
    mean = np.mean(data)
    s = np.std(data, ddof=1)  # Using Bessel's correction for sample standard deviation
    ny = n-1
    z_critical=norm.ppf((1+p)/2)
    chi_2 = chi2.ppf(1-alpha,ny)
    k2=z_critical*np.sqrt( ny*(1+1/n) / chi_2)
    
    # Calculate the tolerance interval
    lower_bound = mean - k2*s
    upper_bound = mean + k2*s

    return lower_bound, upper_bound

print('Normality test for AWB series - (C) Kim Miikki 2023')
print('')

parser=argparse.ArgumentParser()
parser.add_argument('csvfile', nargs='?', help='specify name of the csv file', default='')
parser.add_argument('-s',action='store_true',help='create all figures',required=False)
parser.add_argument('-nsave',action='store_true',help='create all figures',required=False)
args = parser.parse_args()

filename=startpass_filter+'*.csv'
if len(args.csvfile)>0:
    filename=args.csvfile

if args.s:
    isShow=True

if args.nsave:
    isSave=False

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
                method_names.append(Path(name).stem)
                n_series+=1

# Print method names
i=0
n=0
for name in method_names:
    print('Data file: '+name)
    n=len(series[i][0])
    df=n-1
    print('N        : '+str(n))
    print('df       : '+str(df))
    i+=1

                
distances=[]
ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M%S')

if i==1:
    rgains=np.array(series[0][0])
    rmean=np.mean(rgains)
    rstd=np.std(rgains)
    bgains=np.array(series[0][1])
    bmean=np.mean(bgains)
    bstd=np.std(bgains)
    
    
    # Check if rgain and bgain distributions follows are normally distributed
    print('')
    print('Shapiro-Wilk Test')
    print('-----------------')
    print('H0 : p > 0.05: H0 cannot be rejected and varaible may be normally distributed')
    print('HA : p ≤ 0.05: H0 can be rejected and the variable is not normally distributed')
    print('')
   
    # rgain
    W, p = shapiro(rgains)
    tmp='rgain: W('+str(df)+') = '
    tmp+=str(round(W,decimals))+', p = '
    tmp+=str(round(p,decimals))+' '
    tmp+='=> '
    if p>0.05:
        tmp+='H0, normal distribution'
    else:
        tmp+='HA, not normal distribution'
    print(tmp)
             
    # bgain
    W, p = shapiro(bgains)
    tmp='bgain: W('+str(df)+') = '
    tmp+=str(round(W,decimals))+', p = '
    tmp+=str(round(p,decimals))+' '
    tmp+='=> '
    if p>0.05:
        tmp+='H0, normal distribution'
    else:
        tmp+='HA, not normal distribution'
    print(tmp)

    
    if True in [isShow,isSave]:
        z = sns.histplot(x=rgains, color = "red", alpha = 0.6, kde = True, line_kws = {'color':'black','linestyle': 'dashed'})
        plt.xlabel('rgain')
        plt.title('Distribution')
        figfile=curdir+'hist-rgain-'+dt_part+'-'+method_names[0]+'.png'
        if isSave:
            plt.savefig(figfile,dpi=300)
        if isShow:
            plt.show()
        plt.close()
        
        z = sns.histplot(x=bgains, color = "blue", alpha = 0.6, kde = True, line_kws = {'color':'black','linestyle': 'dashed'})
        plt.xlabel('bgain')
        plt.title('Distribution')
        figfile=curdir+'hist-bgain-'+dt_part+'-'+method_names[0]+'.png'
        if isSave:
            plt.savefig(figfile,dpi=300)
        if isShow:
            plt.show()
        plt.close()
    
        fig = sm.qqplot(rgains,norm, fit=True, marker='o', markerfacecolor='r', alpha=0.3)
        sm.qqline(fig.axes[0], line='45', fmt='k')
        plt.grid()
        plt.title('Normal Q-Q Plot: rgains')
        figfile=curdir+'qqplot-rgain-'+dt_part+'-'+method_names[0]+'.png'
        if isSave:
            plt.savefig(figfile,dpi=300)
        if isShow:
            plt.show()
        plt.close()
        
        fig = sm.qqplot(bgains,norm, fit=True, marker='o', markerfacecolor='b', alpha=0.3)
        sm.qqline(fig.axes[0], line='45', fmt='k')
        plt.grid()
        plt.title('Normal Q-Q Plot: bgains')
        figfile=curdir+'qqplot-bgain-'+dt_part+'-'+method_names[0]+'.png'
        if isSave:
            plt.savefig(figfile,dpi=300)        
        if isShow:
            plt.show()
        plt.close()
    
        # Calculate series tolerance limits for x and y axes
        factor=0.5
        p=0.95
        proportion=0.99
        ptext=str(int(p*100))+'%'
    
        # Plot a series rgain TI figure
        fig=plt.figure()
        tmp='Red gain with two-sided TI ('+ptext+','+str(proportion)+')'+'\n'
        tmp+='N= '+str(n)
        plt.title(tmp)
        plt.ylabel('rgain')
        plt.xlabel('Calibration')
        plt.xlim(1,n)
        
        ymin=np.min(rgains)
        ymax=np.max(rgains)
        ydelta=ymax-ymin
        ymin-=ydelta*factor
        ymax+=ydelta*factor
        
        lower, upper=calculate_tolerance_interval(rgains,p,proportion)
        
        plt.ylim(ymin,ymax)
        plt.axhline(lower,color='k',linestyle=':')
        plt.axhline(rmean,color='k')
        plt.axhline(upper,color='k',linestyle=':')
        xs=generate_xlist(n)
        plt.xticks(xs)
        plt.plot(range(1,n+1),rgains,'ro')
        plt.grid()
        figfile=curdir+'ti-rgain-'+dt_part+'-'+method_names[0]+'.png'
        if isSave:
            plt.savefig(figfile,dpi=300)
        if isShow:
            plt.show()
        plt.close(fig)
    
        # Plot a series bgain TI figure
        fig=plt.figure()
        tmp='Blue gain with two-sided TI ('+ptext+','+str(proportion)+')'+'\n'
        tmp+='N= '+str(n)
        plt.title(tmp)
        plt.ylabel('bgain')
        plt.xlabel('Calibration')
        plt.xlim(1,n)
        
        ymin=np.min(bgains)
        ymax=np.max(bgains)
        ydelta=ymax-ymin
        ymin-=ydelta*factor
        ymax+=ydelta*factor
        
        lower, upper=calculate_tolerance_interval(bgains,p,proportion)
        
        plt.ylim(ymin,ymax)
        plt.axhline(lower,color='k',linestyle=':')
        plt.axhline(bmean,color='k')
        plt.axhline(upper,color='k',linestyle=':')
        xs=generate_xlist(n)
        plt.xticks(xs)
        plt.plot(range(1,n+1),bgains,'bo')
        plt.grid()
        figfile=curdir+'ti-bgain-'+dt_part+'-'+method_names[0]+'.png'
        if isSave:
            plt.savefig(figfile,dpi=300)
        if isShow:
            plt.show()
        plt.close(fig)
    
