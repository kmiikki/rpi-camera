#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 18 17:27:00 2023

@author: Kim Miikki 2023
@co-pilot: ChatGPT
"""

import argparse
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from datetime import datetime
from pathlib import Path

np.set_printoptions(suppress=True)

perfect_gray_threshold=2000
isLog=True

def parse_arguments():
    parser = argparse.ArgumentParser(description='Open an RGB image file using OpenCV')
    parser.add_argument('filename', type=str, help='Path to the RGB image file')
    return parser.parse_args()

def create_distribution_lists(image_path):
    # Load the image
    image = cv2.imread(image_path)

    # Calculate the histograms for each color channel
    hist_r = cv2.calcHist([image], [0], None, [256], [0, 256])
    hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
    hist_b = cv2.calcHist([image], [2], None, [256], [0, 256])

    # Convert the histograms to simple numpy arrays
    r_counts = np.squeeze(hist_r)
    g_counts = np.squeeze(hist_g)
    b_counts = np.squeeze(hist_b)

    return r_counts, g_counts, b_counts

    #return hist_r, hist_g, hist_b

def create_diff_distribution_lists(r,g,b):
    rg_diff=abs(r-g)
    rb_diff=abs(r-b)
    gb_diff=abs(g-b)
    return rg_diff, rb_diff, gb_diff

def calculate_mse(r_counts, g_counts, b_counts):
    mse = np.mean((r_counts - g_counts) ** 2) + np.mean((r_counts - b_counts) ** 2) + np.mean((g_counts - b_counts) ** 2)
    mse /= 3
    return mse

def determine_grayness(mse, threshold=perfect_gray_threshold):
    if mse <= threshold:
        return 'Perfectly Gray'
    else:
        return 'Not Gray'

def xrange_for_plot(r,g,b):
    min_pos=0
    max_pos=0
    marginal=1
    tmp=r+g+b
    min_pos, max_pos = np.nonzero(tmp > 0)[0][[0,-1]]
    if min_pos-marginal>=0:
        min_pos-=marginal
    if max_pos+marginal<=len(tmp)-1:
        max_pos+=marginal
    return min_pos, max_pos
        
def plot_distribution_lists(r_counts, g_counts, b_counts, fname):
    global curdir
    global rg,rb,gb
    
    x = np.arange(256)

    plt.plot(x, r_counts, color='red', label='Red')
    plt.plot(x, g_counts, color='green', label='Green')
    plt.plot(x, b_counts, color='blue', label='Blue')

    plt.xlabel('Color Value')
    plt.ylabel('Pixel Count')
    plt.title('Color Channel Distribution')
    plt.legend()
    if isLog:
        plt.yscale('log')
    plt.xlim(xrange_for_plot(rg,rb,gb))
    plt.grid()
    plt.savefig(curdir+fname,dpi=300)
    plt.close()

def plot_differences_lists(rg, rb, gb, fname):
    global curdir
    
    x = np.arange(256)

    plt.plot(x, rg, color='green', label='ABS(R-G)')
    plt.plot(x, rb, color='red', label='ABS(R-B)')
    plt.plot(x, gb, color='blue', label='ABS(B-G)')
    plt.plot(x, (rg+rb+gb)/3, color='black', linewidth=2, label='Mean')

    plt.xlabel('Color Value')
    plt.ylabel('Pixel Count')
    plt.title('Color Channel Differences')
    plt.legend()
    plt.xlim(xrange_for_plot(rg,rb,gb))
    plt.grid()
    plt.savefig(curdir+fname,dpi=300)
    plt.close()


# Main program
print('RGB grayness estimator - Kim Miikki 2023')
args=parse_arguments()

print('Current directory:')
curdir=os.getcwd()
path=Path(curdir)
print('')
print(curdir)
print('')
if curdir[-1] != '/':
    curdir+='/'

# Check if the file exists
if not os.path.exists(args.filename):
    print(f"File '{args.filename}' not found.")
    sys.exit(0)

# Open the image using OpenCV
image = cv2.imread(args.filename)

# Check if the image is successfully loaded
if image is None:
    print(f"Failed to open '{args.filename}'. Make sure it is a valid RGB image.")
    sys.exit(0)

image_path = args.filename
ct1=datetime.now()
dt_part=ct1.strftime('%Y%m%d-%H%M')
fstem=Path(args.filename).stem
fnames=[]
fnames.append('rgb-hist-'+dt_part+'-'+fstem+'.png')
fnames.append('rgb-diffhist-'+dt_part+'-'+fstem+'.png')

r_counts, g_counts, b_counts = create_distribution_lists(image_path)
rg, rb, gb=create_diff_distribution_lists(r_counts, g_counts, b_counts)

# Plot the distribution graphs
print('Generating distribution plots...')
plot_distribution_lists(r_counts, g_counts, b_counts, fnames[0])
plot_differences_lists(rg, rb, gb, fnames[1])
print('')

mse = calculate_mse(r_counts, g_counts, b_counts)
grayness = determine_grayness(mse)

print("MSE:", mse)
print("Grayness:", grayness)