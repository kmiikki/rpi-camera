#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 08:24:37 2023

@author: Kim Miikki
"""
import argparse
import csv
import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
from numpy.random import seed
from numpy.random import normal
from pathlib import Path

np.set_printoptions(suppress=True)

rgain=2.5
bgain=2.0

rgain_scale=0.002
bgain_scale=0.005

n=100
decimals=8
startpass_filter='awbgains-trials-'
isShow=False

print('Generate normal distributed rgains and bgains - Kim Miikki 2023')
print('')

parser=argparse.ArgumentParser()
parser.add_argument('-r', type=float, help='rgain mean value (default: '+str(rgain)+')',required=False)
parser.add_argument('-b', type=float, help='bgain mean value (default: '+str(bgain)+')',required=False)
parser.add_argument('-rs', type=float, help='rgain scale (default: '+str(rgain_scale)+')',required=False)
parser.add_argument('-bs', type=float, help='rgain scale (default: '+str(rgain_scale)+')',required=False)
parser.add_argument('-n', type=int, help='trials (n > 0, default: '+str(n)+')',required=False)
args = parser.parse_args()

# Override default values to argument values
if args.r != None:
    rgain=args.r
if args.b != None:
    bgain=args.b

if args.rs != None:
    if args.rs > 0:
        rgain=args.rs
if args.bs != None:
    if args.bs > 0:
        rgain=args.bs

if args.n != None:
    if n > 1:
        n=args.n

print('Current directory:')
curdir=os.getcwd()
path=Path(curdir)
print(curdir)
print('')
if curdir[-1] != '/':
    curdir+='/'

# Make this example reproducible
seed(1)

# Generate rgains and bgains distribuytrions that follow a normal distribution 
rgains = normal(loc=rgain, scale=rgain_scale, size=n)
bgains = normal(loc=bgain, scale=bgain_scale, size=n)

# Calculate statistics
r_mean=np.mean(rgains)
r_delta=r_mean-rgain
r_re=r_delta/rgain
r_std=np.std(rgains)

b_mean=np.mean(bgains)
b_delta=b_mean-bgain
b_re=b_delta/bgain
b_std=np.std(bgains)

# Print statistics
print('Statistics')
print('n: '+str(n))
print('')
print('rgain')
print('-----')
print('loc:   '+str(rgain))
print('scale: '+str(rgain_scale))
print('µ  :   '+str(round(r_mean,decimals)))
print(f'ΔR :  {r_delta:+.{decimals}f}')
print(f'RE :  {r_re:+.{decimals}f}')
print(f'std:   {r_std:.{decimals}f}')

print('')

print('bgain')
print('-----')
print('loc:   ' +str(bgain))
print('scale: '+str(bgain_scale))
print('µ  :   '+str(round(b_mean,decimals)))
print(f'ΔB :  {b_delta:+.{decimals}f}')
print(f'RE :  {b_re:+.{decimals}f}')
print(f'std:   {b_std:.{decimals}f}')

ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M%S')

# Save the generated calibration series data to a csv file
csvfile=curdir+startpass_filter+'n'+str(n)+'-'+dt_part+'.csv'
with open(csvfile, 'w') as f:
    writer = csv.writer(f,delimiter=',')
    header=['calibration','rgain','bgain']
    writer.writerow(header)
    i=1
    for r,b in zip(rgains,bgains):
        writer.writerow([i,r,b])
        i+=1

# Create a distribution graph of the gains
figfile=curdir+startpass_filter+'n'+str(n)+'-'+dt_part+'.png'
plt.scatter(bgains, rgains, marker='.', color='k')
plt.title('Normal distributed random gains, N='+str(n))
plt.xlabel('bgain')
plt.ylabel('rgain')
plt.grid()
plt.savefig(figfile,dpi=300)
if isShow:
    plt.show()
plt.close()           