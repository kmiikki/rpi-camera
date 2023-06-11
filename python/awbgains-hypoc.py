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

print('Paired samples t-test for rgains and bgains as coordinates - Kim Miikki 2023')
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

# Define the rgain and bgain values from Method A and Method B, respectively
x_A = np.array(series[0][0][:trials])
x_B = np.array(series[1][0][:trials])
y_A = np.array(series[0][1][:trials])
y_B = np.array(series[1][1][:trials])

# Calculate the differences between coordinates
differences_x = np.array(x_A) - np.array(x_B)
differences_y = np.array(y_A) - np.array(y_B)

# Calculate the mean differences and standard deviations
mean_difference_x = np.mean(differences_x)
mean_difference_y = np.mean(differences_y)
std_dev_x = np.std(differences_x, ddof=1)
std_dev_y = np.std(differences_y, ddof=1)

# Calculate the standard errors of the mean differences
se_x = std_dev_x / np.sqrt(len(differences_x))
se_y = std_dev_y / np.sqrt(len(differences_y))

# Perform the t-test for x coordinates
t_statistic_x, p_value_x = stats.ttest_rel(x_A, x_B)

# Perform the t-test for y coordinates
t_statistic_y, p_value_y = stats.ttest_rel(y_A, y_B)

# Define the significance level (alpha)
alpha = 0.05

# Make a decision based on the p-values
if p_value_x < alpha or p_value_y < alpha:
    print("Reject the null hypothesis. There is a significant difference in the mean coordinates.")
else:
    print("Fail to reject the null hypothesis. There is no significant difference in the mean coordinates.")

# Print the t-statistics and p-values for x coordinates
print("t-statistic (x):", round_3d(t_statistic_x))
print("p-value (x)    :", round_3d(p_value_x))

# Print the t-statistics and p-values for y coordinates
print("t-statistic (y):", round_3d(t_statistic_y))
print("p-value (y)    :", round_3d(p_value_y))

