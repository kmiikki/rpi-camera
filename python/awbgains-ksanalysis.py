#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 21:39:44 2023

@author: Kim Miikki 2023
@co-pilot: ChatGPT

File format: awbgains-trials-XXX.csv
Columns: calibration,rgain(0),bgain(0),rgain_opt,bgain_opt,distance,evaluations,position,time (s)
Required columns: rgain_opt,bgain_opt

"""

import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import scipy.stats as stats

isShow=False
max_series=2
n_series=0
series=[]
trials=0
p=0.95

method_names=[]
startpass_filter='awbgains-trials-'
keys=['rgain_opt','bgain_opt']

rgb_decimals=3

def calculate_distances(coordinates):
    distances = []
    for i in range(len(coordinates)):
        for j in range(i + 1, len(coordinates)):
            point1 = coordinates[i]
            point2 = coordinates[j]
            distance = np.linalg.norm(point2 - point1)
            distances.append(distance)
    return distances

print('Kolmogorov-Smirnov test for AWB series - (C) Kim Miikki 2023')
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
                method_names.append(Path(name).stem)
                n_series+=1
                print('Series '+str(n_series)+' trials: '+str(length))


# Print method names
i=0
print('')
for name in method_names:
    print('Method '+str(i+1)+': '+name)
    i+=1
print('')
                
i=0
distances=[]
ct=datetime.now()
dt_part=ct.strftime('%Y%m%d-%H%M%S')
while i<n_series:
    r_gains=series[i][0]
    b_gains=series[i][1]
    distances.append(calculate_distances(np.array(list((zip(b_gains,r_gains))))))
    
    # Plot the distances histogram
    plt.hist(distances[i], bins=10, color='black', alpha=0.5, label='Distances '+str(i+1))
    plt.xlabel('Length')
    plt.ylabel('Frequency')
    plt.title('Length Distribution of Method '+str(i+1))
    plt.legend()
    figfile=curdir+'awbgains-dists-m'+str(i+1)+'-'+dt_part+'.png'
    plt.savefig(figfile,dpi=300)
    if isShow:
        plt.show()
    plt.close()
    i+=1

if i==2:
    # Perform the Kolmogorov-Smirnov test
    statistic, p_value = stats.ks_2samp(distances[0], distances[1])
    
    alpha = 1-p # Significance level 0.05 as default
    alpha = round(alpha,10)
    
    # Check if the two distributions are similar
    print('Kolmogorov-Smirnov test, alpha= '+str(alpha))
    print('D= '+str(statistic))
    print('p= '+str(p_value))
    if p_value > alpha:
        print("The distributions are similar.")
    else:
        print("The distributions are different.")
    
    # Plot the distances histograms
    plt.hist(distances[0], bins=10, color='blue', alpha=0.5, label='Distances 1')
    plt.hist(distances[1], bins=10, color='red', alpha=0.5, label='Distances 2')
    plt.xlabel('Length')
    plt.ylabel('Frequency')
    plt.title('Length Distribution')
    plt.legend()
    figfile=curdir+'awbgains-dists-m1,2-'+dt_part+'.png'
    plt.savefig(figfile,dpi=300)
    if isShow:
        plt.show()
    plt.close()
    
    # Calculate the empirical cumulative distribution functions (ECDFs)
    x1 = np.sort(distances[0])
    y1 = np.arange(1, len(x1) + 1) / len(x1)
    
    x2 = np.sort(distances[1])
    y2 = np.arange(1, len(x2) + 1) / len(x2)
    
    # Calculate the position of statistic on the x-axis
    sorted_distances1 = np.sort(distances[0])
    index = np.searchsorted(sorted_distances1, statistic, side='right')
    position = index / len(sorted_distances1)
    
    # Plot the ECDFs
    plt.step(x1, y1, marker='', color='blue', linestyle='-', label='Distances 1')
    plt.step(x2, y2, marker='', color='red', linestyle='-', label='Distances 2')

    plt.grid()
    plt.xlabel('Distance')
    plt.ylabel('Cumulative Probability')
    plt.title('Cumulative Distribution Functions')
    plt.legend()
    figfile=curdir+'awbgains-ecdf-'+dt_part+'.png'
    plt.savefig(figfile,dpi=300)
    if isShow:
        plt.show()
    plt.close()