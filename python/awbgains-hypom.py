#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 08:33:30 2023

@author: Kim Miikki
@co-pilot: ChatGPT
"""
import glob
import os
import sys
import scipy.stats as stats
import numpy as np
import pandas as pd
from pathlib import Path

series=[]
max_series=2
n_series=0
trials=0
startpass_filter='awbgains-trials-'
keys=['rgain_opt','bgain_opt']

method_names=[]
method_n=['A','B']

def round_3d(value):
    return round(value,3)

print('Paired samples t-test for rgains and bgains - Kim Miikki 2023')
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
                if trials==0:
                    trials=length
                elif length<trials:
                    trials=length
                print('Series '+method_n[n_series-1]+' trials: '+str(length))

print('')
if n_series != 2:
    print('Two files are required for the hypothesis testing!')
    sys.exit(0)

if n_series>0:
    print('Series common trials count: '+str(trials))
    print('')
else:
    print('No valid series found!')
    sys.exit(0)

# Print method names
i=0
for name in method_names:
    print('Method '+method_n[i]+': '+name)
    i+=1
print('')

print('Null Hypothesis H0        : µ1-µ2 = 0')
print('Alternative Hypothesis HA : µ1-µ2 ≠ 0')
print('')

i=0    
for gain in keys:
    # Define the rgain and bgain values from Method A and Method B, respectively
    gains1 = np.array(series[0][i][:trials])
    gains2 = np.array(series[1][i][:trials])
    
    # Calculate the differences
    differences = gains1-gains2
    
    # Calculate the mean difference and standard deviation
    mean_difference = np.mean(differences)
    std_dev = np.std(differences, ddof=1)  # ddof=1 for sample standard deviation
    
    # Calculate the standard error of the mean difference
    se = std_dev / np.sqrt(len(differences))
    
    # Perform the t-test
    t_statistic, p_value = stats.ttest_rel(gains1, gains2)
    
    # Define the significance level (alpha)
    alpha = 0.05
    
    if i==0:
        print('Compare rgains')
    else:
        print('Compare bgains')
    print('--------------')
    
    # Make a decision based on the p-value
    if p_value < alpha:
        print("Reject the null hypothesis. There is a significant difference between Method 1 and Method 2.")
    else:
        print("Fail to reject the null hypothesis. There is no significant difference between Method 1 and Method 2.")
    
    # Print the t-statistic and p-value
    print("t-statistic:", round_3d(t_statistic))
    print("p-value    :", round_3d(p_value))
    if i==0:
        print('')
    i+=1
