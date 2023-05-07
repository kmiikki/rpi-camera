#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  1 08:47:10 2023

@author: Kim Miikki

Subdirectories:
hhmmss-NAME,
NAME=figures,data,results

figures:

data:
    - csv data of each series: stem(name)+.'.csv'
results:
    - csv summary data of each series as function of time

Test arguments: -g 710 -th m15 -ymin 20 -mask
                -g 710-719 -th m17 -ymin 20 -type
                
TTB (threshold temperature bracketing)
Two types of outputs of the mask: scatter plot and imshow

Lower median
------------
th_lmin              = tlmin
th_lmedian           = tlmedian
th_mean_lmd_lm       = (tlmedian+tlmean)/2
th_lmean             = tlmean
th_mean_lmd_md       = (tmedian+tlmedian)/2

Globals
-------
th_mean_tmin_hmax    = (thmin+thmax)/2
th_median            = tmedian
th_mean              = tmean
th_mean_lmd_hmd      = (tlmedian+thmedian)/2

Upper median
------------
th_mean_md_hmd       = (tmedian+thmedian)/2
th_hmean             = thmean
th_mean_hmd_hm       = (thmean+thmedian)/2
th_hmedian           = thmedian
th_mean_hm_hmax      = (thmedian+thmax)/2
th_hmax              = thmax

Other
----
th_temp              = threshold

List of thresholds:
    Min
    MedianL
    Mean(MedianL, MeanL)
    MeanL
    Mean(MedianL, Median)
    Mean(Min, Max)
    Median
    Mean
    Mean(MedianL, MedianH)
    Mean(Median, MedianH)
    MeanH
    Mean(MeanH, MedianH)
    MedianH
    Mean(MedianH, Max)
    Max
    Temperature

                
"""

import argparse
import cv2
import csv
import math
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from scipy.signal import medfilt
from sklearn.metrics import auc

# Set the print options to suppress scientific notation
np.set_printoptions(suppress=True)

# Supported image formats:
exts = ['.txt', '.csv']
primary = '.txt'
secondary = list(set(exts)-set([primary]))[0]
pts = []
ptsfile = ''
ptsfile_default = 'video.pts'
isPTS = False
isPTSfile = False
isPTSarg = False
isInterval = True
isHeader = False
isCalibration = False
              
tg_xlabel='X coordinate'                
tg_ylabel='Y coordinate'
threshold = 20
pixels_th = 1
pixels_ymargin = 10
isNumSort = True
isGrid = True
isLimits = False
isWidths = False

isMasks = False
isDeciles = False
selection = -1      # Selected number for masks or deciles
method='mask'

isYmin = False
isYmax = False
isHot_object = True
isAuto_temp = True
isThreshhold_bracketing = True
preferHot_object = True
normalTemps = [18, 30]  # Normal room temperature range 18-30°C

delimiter = ','

tstart = 0
interval = 1
tunit = 's'
tfactor = 1
cal = 1
unit = 'mm'

dpi = 300

isDebug = False

def multiplot(xs,
              xlabel,
              ys,
              ylabel,
              yattr,
              name,
              title='',
              legend=-1):
    '''
    Parameters
    ----------
    xs : array
        1D list of x values
    xlabel : str
        x label string
    ys : array of y series
        a stacked array of y data
    xlabel : str
        y label string
    yattr : array
        y data sereis attribute array
        [color, width, type, yname]
    name : str
        filename
    ymin : float
        graph minimum y value
    ymax : float
        graph maximum y value
    title : str
        optional title for the graph (default: no title)
    legend : value, optional
        -1 : no legend (= default)
        0-8 : legend position in lengends array

    Returns
    -------
    None.

    '''

    legends=['upper left','upper center','upper right',
           'center left','center','center right',
           'lower left','lower center','lower right']    
    
    fig=plt.figure()
    tgname=name+'.png'
    
    plt.xlim(xs[0],xs[-1])
    if ylabel == 'Proportion':
        y0=ys.min()
        y1=ys.max()
        if abs(y1-y0)>=0.1:       
            plt.ylim(0,1)
        elif y1==y0:
            plt.ylim(y0-0.01,y0+0.01)
        else:
            plt.ylim(y0,y1)
    else:
        if isYmin:
            y0=ymin
        else:
            y0=ys.min()
        if isYmax:
            y1=ymax
        else:
            y1=ys.max()
        if y0==y1:
            if y0==0:
                dy=0.01
            else:
                dy=abs(y0/100)
        else:
            dy=0
        plt.ylim(y0-dy,y1+dy)
    
    i=0
    lines=[]
    labels=[]
    for row in yattr:
        col=row[0]
        w=row[1]
        t=row[2]
        if len(yattr)>1:
            line,=plt.plot(xs,ys[i],color=col,linewidth=w,linestyle=t) 
        else:
            line,=plt.plot(xs,ys,color=col,linewidth=w,linestyle=t) 
        lines.append(line)
        labels.append(row[3])
        i+=1
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if isGrid:
        plt.grid()
    if legend>=0 and legend<len(legends)-1:
        loc=legends[legend]
        plt.legend(handles=lines, labels=labels, loc=loc)
    if len(title)>0:
        plt.title(title)
        
    plt.savefig(dt_part+'-'+dirs[3]+'/'+tgname,dpi=300)
    plt.close()

def unique(arglist):
    x = np.array(arglist)
    return np.unique(x)


def get_ranges(argstr):
    nums = []
    s = argstr.strip()
    # Find character ','
    list1 = s.split(',')
    list1 = unique(list1)

    # Find ranges and add all numbers into a list
    for element in list1:
        isNumeric = element.isnumeric()
        # Test if element is a range
        error = False
        if not isNumeric:
            tmp = element.split('-')
            if len(tmp) != 2:
                error = True
            else:
                isFirst = True
                a = -1
                b = -1
                for n in tmp:
                    if not n.isnumeric():
                        error = True
                    else:
                        if isFirst:
                            a = int(n)
                            isFirst = False
                        else:
                            b = int(n)
                if not error:
                    if b <= a:
                        error = True
                if not error:
                    i = a
                    while i <= b:
                        nums.append(i)
                        i += 1
        else:
            nums.append(int(element))
    return unique(nums)


def first_digit_pos(s):
    for i, c in enumerate(s):
        if c.isdigit():
            return i
    return -1


def last_number_pos(s):
    ''' Return the position where the last number starts in a string and
        the length of the number. Return (-1, -1) if no number is found.
        String should as a filename: 'stem.ext'.
    '''
    numpos = -1
    length = -1
    ext_length = len(primary)
    stem = s[:len(s)-ext_length]

    i = 0
    for ch in reversed(stem):
        if not ch.isdigit():
            break
        i += 1
    if i > 0:
        numpos = len(s)-(ext_length+i)
        length = i

    return numpos, length


def swap(a, b):
    return b, a


def most_abundant_string_length(strings):
    lengths = [len(s) for s in strings]
    length_counts = {}
    for length in lengths:
        if length in length_counts:
            length_counts[length] += 1
        else:
            length_counts[length] = 1
    return max(length_counts, key=length_counts.get)


def get_time(tstart, pos, interval):
    return tstart+pos*interval


def plot_graph(path_name, ts, ys, time_unit, ylabel, cal=isCalibration, grid=isGrid, dpi=dpi):
    fig = plt.figure()
    plt.xlim(ts.min(), ts.max())
    plt.ylim(ys.min(), ys.max())
    plt.plot(ts, ys, color="k")
    plt.xlabel('Time ('+time_unit+')')
    if not cal:
        plt.ylabel(ylabel)
    else:
        plt.ylabel('Y coordinate')
    if grid:
        plt.grid()
    plt.tight_layout()
    plt.savefig(path_name, dpi=dpi)
    plt.close(fig)


def read_thermogram_csv(csv_filename):
    data = np.genfromtxt(csv_filename, delimiter=delimiter, dtype=float)
    return data


def find_indices_over_threshold(thermogram, threshold):
    over_threshold = thermogram >= threshold
    row_indices, col_indices = np.where(over_threshold)
    return row_indices, col_indices


def find_indices_under_threshold(thermogram, threshold):
    under_threshold = thermogram < threshold
    row_indices, col_indices = np.where(under_threshold)
    return row_indices, col_indices


def find_indices_of_highest_temperatures(thermogram, percentage):
    # Flatten the thermogram array and sort the values in descending order
    flattened = np.sort(thermogram.flatten())[::-1]
    # Compute the number of values that correspond to the specified percentage
    num_values = int(len(flattened) * percentage / 100)
    # Get the highest temperature values
    highest_values = flattened[:num_values]
    # Create a boolean array that is True for elements in the thermogram that are in the highest_values array
    is_highest = np.isin(thermogram, highest_values)
    # Get the row and column indices of the True elements in the is_highest array
    row_indices, col_indices = np.where(is_highest)
    return row_indices, col_indices


def find_indices_of_highest_temperatures_nums(thermogram, num_values):
    flattened = np.sort(thermogram.flatten())[::-1]
    highest_values = flattened[:num_values]
    is_highest = np.isin(thermogram, highest_values)
    row_indices, col_indices = np.where(is_highest)
    return row_indices, col_indices


def find_indices_of_lowest_temperatures(thermogram, percentage):
    flattened = np.sort(thermogram.flatten())
    num_values = int(len(flattened) * percentage / 100)
    lowest_values = flattened[:num_values]
    is_lowest = np.isin(thermogram, lowest_values)
    row_indices, col_indices = np.where(is_lowest)
    return row_indices, col_indices


def find_indices_of_lowest_temperatures_nums(thermogram, num_values):
    flattened = np.sort(thermogram.flatten())
    lowest_values = flattened[:num_values]
    is_lowest = np.isin(thermogram, lowest_values)
    row_indices, col_indices = np.where(is_lowest)
    return row_indices, col_indices


def get_mean_distance_of_coordinates(xy_list):
    numerator = 0
    denominator = 0
    rows = xy_list[0]
    cols = xy_list[1]
    xys = list(zip(cols, rows))
    
    for p1 in xys:
        for p2 in xys:
            distance = math.sqrt((p2[0]-p1[0])**2+(p2[1]-p1[1])**2)
            numerator += distance
            denominator += 1
    return numerator / denominator


def get_mean_distance_from_center(xy_list, rows, columns):
    xc = columns / 2
    yc = rows / 2
    numerator = 0
    denominator = 0
    rows = xy_list[0]
    cols = xy_list[1]
    xys = list(zip(cols, rows))

    for p in xys:
        distance = math.sqrt((p[0]-xc)**2+(p[1]-yc)**2)
        numerator += distance
        denominator += 1
    return numerator / denominator

def parse_threshold(string):
    global threshold
    
    method='mask'
    string.strip()
    selection=-1
    isOk=False
    
    # Test if threshold is a number
    try:
        value=float(string)
        threshold=value
        selection=0
        isOk=True
    except:
        pass
    
    if not isOk and len(string)>1:
        ch=string[0].lower()
        if ch in ['m','d']:
            if ch=='m':
                method='mask'
            else:
                method='deciles'
            string=string[1:]
            # Test if the rest is an integer
            try:
                value=int(string)
                selection=value
                isOk=True
            except:
                pass
    return method, selection

print("Thermograms analysis - (C) Kim Miikki 2023")

# Get current directory
curdir = os.getcwd()
path = Path(curdir)
foldername = os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print('')
if curdir != '/':
    curdir += '/'

isTFactor = False
isPSeries = False
isNoSeries = False
parser = argparse.ArgumentParser()
parser.add_argument('-ymin', help='y axis minimum value', type=float, required=False)
parser.add_argument('-ymax', help='y axis maximum value', type=float, required=False)
parser.add_argument('-hot', action='store_true', help='object is hot (Tobj > Tenv)', required=False)
parser.add_argument('-cold', action='store_true', help='object is hot (Tobj > Tenv)', required=False)
parser.add_argument('-pts', type=str, help='pts file name', required=False)
parser.add_argument('-s', type=float, help="start time for first frame", required=False)
parser.add_argument('-i', type=float, help="interval between two frames", required=False)
parser.add_argument("-t", type=str, help="time unit", required=False)
parser.add_argument("-f", type=float, help="time factor (only PTS file)", required=False)
parser.add_argument('-masks', action='store_true', help='plot masks', required=False)
parser.add_argument('-dec', action='store_true', help='mask by deciles', required=False)  # Used only in mask mode
parser.add_argument('-th', help='threshold: temperature, mN or dN, where N is mask (m) or decile (d) number', type=str, required=False)
parser.add_argument('-g', help='create graphs based on numbered image positions (a = all or num1, num2-num3, ...)', type=str, required=False)
parser.add_argument('-type', action='store_true', help='start file name with type (default= number)', required=False)
parser.add_argument('-n', action='store_true', help='do not store series data', required=False)
args = parser.parse_args()


if args.ymin != None:
    ymin = float(args.ymin)
    isYmin = True
if args.ymax != None:
    ymax = float(args.ymax)
    isYmax = True

if args.hot:
    isHot_object = True
    isAuto_temp = False
if args.cold:
    isHot_object = False
    isAuto_temp = False
if args.hot and args.cold:
    isHot_object = preferHot_object
    print('Both cold and hot object specified. Selecting preferred mode: ', end='')
    if isHot_object:
        print('HOT')
    else:
        print('COLD')
    print('')

if args.pts != None:
    ptsfile = args.pts
    isPTSarg = True

if args.s != None:
    tstart = float(args.s)

if args.i != None:
    tmp = float(args.i)
    if interval > 0:
        interval = tmp
        isInterval = True

if args.t != None:
    tmp = args.t
    if len(tmp) > 0:
        tunit = tmp

if args.f != None:
    isTFactor = True
    tmp = float(args.f)
    if tmp.is_integer():
        tfactor = int(round(tmp, 0))
    else:
        tfactor = float(tmp)


masks=['00_thres',
              '01_min',
              '02_pct05',
              '03_mean_lm_min',
              '04_tlmedian',
              '05_mean_lmd_lm',
              '06_lmean',
              '07_mean_lmd_md,',
              '08_mean_min_max',
              '09_median',
              '10_mean',
              '11_mean_lmd_hmd',
              '12_mean_md_hmd',
              '13_hmean',
              '14_mean_hmd_hm',
              '15_hmedian',
              '16_mean_hm_max',
              '17_pct95',
              '18_max']

deciles=[]
for i in range(0,10):
    numstr=str(i)
    deciles.append(numstr+'_decile')

if args.masks:
    mask_names = masks
    isMasks = True
    
if args.dec:
    mask_names=deciles
    isDeciles = True

if (not isMasks) and (not isDeciles):
    mask_names=masks

if args.th != None:
    method,selection=parse_threshold(args.th)
    methods=len(mask_names)
    if selection<0 or selection>methods-1:
        print('Invalid selection of method. The program is terminated.')
        sys.exit(0)
    if method=='mask':
        mask_names = masks
    else:
        mask_names = deciles
        
if args.type:
    isNumSort = False

if args.n:
    isNoSeries = True

# Determine which file format is the most abundant
pris = []
secs = []
prinums = []
secnums = []
for name in sorted(path.iterdir()):
    if name.is_file() and name.suffix in exts:
        tmp = name.name
        pos, numlen = last_number_pos(tmp)
        if pos >= 0:
            num = tmp[pos:pos+numlen]
            if name.suffix == primary:
                pris.append(tmp)
                prinums.append(num)
            elif name.suffix == secondary:
                secs.append(tmp)
                secnums.append(num)
countpris = len(pris)
countsecs = len(secs)

if countpris >= countsecs:
    frames = pris
    nums = prinums
else:
    primary, secondary = swap(primary, secondary)
    countpris, countsecs = swap(countpris, countsecs)
    frames = secs
    nums = secnums

if countpris == 0:
    print('No suitable TXT or CSV files found in current directory.')
    print('Program is terminated.')
    print('')
    sys.exit(0)

namelen = most_abundant_string_length(frames)
numlen = most_abundant_string_length(nums)

# Remove all strings that do not belong the time-lapse set
i = 0
reminds = []
for s in frames:
    remove = False
    if len(s) != namelen:
        remove = True
    if not remove:
        pos, nlen = last_number_pos(s)
        if nlen != numlen:
            remove = True
    if remove:
        reminds.append(i)
    i += 1
for idx in sorted(reminds, reverse=True):
    frames.pop(idx)
    nums.pop(idx)

# The stem is assumed to be same => not checked

# Analyze first frame
if len(frames) > 0:
    # Get first stem without number and '-', '_' or' '
    sample = frames[0]
    npos, nlen = last_number_pos(sample)
    if npos > 0:
        str_start = Path(sample).stem[:npos]
        chars = ['-', '_', ' ']
        if str_start[-1] in chars:
            str_start = str_start[:-1]
        pts_name = str_start+'.pts'

# Create an integer list of the number strings
nums_int = list(map(int, nums))
nums_graph = []

# Create a list of the images from which graphs will be created
if args.g != None:
    tmp = args.g
    if tmp.lower() == 'a':
        nums_graph = nums_int
    else:
        nums_range = get_ranges(tmp)
        nums_graph = sorted(list(set(nums_range).intersection(nums_int)))
    if len(nums_graph) > 0:
        isPSeries = True

if not isInterval:
    # Find a PTS file, if it exists
    if isPTSarg:
        if os.path.isfile(curdir+ptsfile):
            ptsfile = Path(curdir+ptsfile)
            isPTSfile = True
    else:
        # List all PTS files
        ptslst = []
        for f in sorted(path.iterdir()):
            suffix = f.suffix.lower()
            if f.is_file():
                if suffix == '.pts':
                    ptslst.append(f.name)

        if len(ptslst) > 0:
            isPTSfile = True

            # Check if projectname.pts or video.pts exists
            if len(pts_name) > 0:
                if pts_name in ptslst:
                    ptsfile = Path(curdir+pts_name)
                elif ptsfile_default in ptslst:
                    ptsfile = Path(curdir+ptsfile_default)
                else:
                    # If not found, use the first PTS file in ptslst
                    if len(ptslst) > 1:
                        print('Found more than 1 PTS file, using first!')
                    ptsfile = Path(curdir+ptslst[0])

    if isPTSfile:
        with open(ptsfile) as file:
            reader = csv.reader(file)
            header = next(file)
            for row in reader:
                try:
                    pts.append(float(row[0]))
                except:
                    pass
        if len(pts) != len(nums):
            print('PTS count differs from image count. PTS disabled.')
            isPTS = False
        else:
            print('PTS file found: '+ptsfile.name)
            isPTS = True
        print('')

    print('Digits in images    : '+str(numlen))
    print('Valid images found  : '+str(len(nums)))
    print('Image extension type: '+primary)
    print('')

    # Multiply PTS values with the factor
    if isPTS:
        if len(pts) > 0:
            if not isTFactor:
                tfactor = 1/1000
            pts = np.array(pts)
            pts = pts*tfactor
else:
    nums_int = np.array(nums_int)
    pts = np.copy(nums_int)
    if float(interval).is_integer():
        pts = (pts*interval).astype(int)
    else:
        pts = (pts*interval).astype(float)
    pts = pts+tstart-pts[0]

# Create project name and sub directories
ct = datetime.now()
dt_part = ct.strftime('%Y%m%d-%H%M%S')
# figdir=dt_part+'figures'
# datadir=dt_part+'data'
# resultsdir=dt_part+'results'

print('Creating directories:')
dirs = ['masks', 'figures', 'data', 'results']
for name in dirs:
    newdir = dt_part+'-'+name
    if name == 'masks' and (not isMasks) and (not isDeciles):
        continue
    if name == 'figures' and (not isPSeries):
        continue
    if name == 'data' and isNoSeries:
        continue
    print(newdir)
    try:
        if not os.path.exists(curdir+newdir):
            os.mkdir(curdir+newdir)

    except OSError:
        print("Unable to create a directory or directories under following path:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)
    if isMasks or isDeciles:
        # Special mode: create only masks
        break
print('')

# Process all thermograms
results=[]
index=0
t1=datetime.now()
print('Processing:')
for frame in frames:
    if (isMasks or isDeciles) and (not (nums_int[index] in nums_graph)):
        index+=1
        continue
    print(frame)
    data = read_thermogram_csv(frame)
    rows, cols = data.shape

    # get statistical data from a thermogram
    tmin = np.min(data)
    tmax = np.max(data)
    tmean = np.mean(data)
    tmedian = np.median(data)
    tsdev = np.std(data)

    # Split data into low and high parts by median temperature
    highs_xys = np.array(find_indices_over_threshold(data, tmedian))
    lows_xys = np.array(find_indices_under_threshold(data, tmedian))
    highs = data[highs_xys[0], highs_xys[1]]
    lows = data[lows_xys[0], lows_xys[1]]

    # Statistical info for upper and lower part of the data
    thmin = np.min(highs)
    thmax = np.max(highs)
    thmean = np.mean(highs)
    thmedian = np.median(highs)

    tlmin = np.min(lows)
    tlmax = np.max(lows)
    tlmean = np.mean(lows)
    tlmedian = np.median(lows)

    # Lower median
    # ------------
    th_lmin = tlmin
    th_mean_lm_lmin = (tlmean+tlmin)/2
    th_lmedian = tlmedian
    th_mean_lmd_lm = (tlmedian+tlmean)/2
    th_lmean = tlmean
    th_mean_lmd_md = (tmedian+tlmedian)/2

    # Globals
    # -------
    th_mean_min_max = (tmin+tmax)/2
    th_median = tmedian
    th_mean = tmean
    th_mean_lmd_hmd = (tlmedian+thmedian)/2

    # Upper median
    # ------------
    th_mean_md_hmd = (tmedian+thmedian)/2
    th_hmean = thmean
    th_mean_hmd_hm = (thmean+thmedian)/2
    th_hmedian = thmedian
    th_mean_hm_hmax = (thmedian+thmax)/2
    th_hmax = thmax

    # Other
    # ----
    th_temp = threshold

    elements=rows*cols
    data_sorted=np.sort(np.ravel(data))
    points05=round(elements*0.05)
    th_pct05=data_sorted[points05-1]
    th_pct95=data_sorted[-points05]

    if isYmin:
        vmin=ymin
    else:
        vmin=tmin
    if isYmax:
        vmax=ymax
    else:
        vmax=tmax

    if isAuto_temp:
        # Determine background and object section
        # Scores are given for background
        # Compare low and high median coordinates

        low_score = 0
        high_score = 0
        low_pos = 0  # -t under normal, 0 in normal range, +t over normal
        high_pos = 0  # -t under normal, 0 in normal range, +t over normal

        # Test 1 - Distance from normal temperatures
        if tlmedian >= normalTemps[0] and tlmedian <= normalTemps[1]:
            low_score += 1
        elif tlmedian < normalTemps[0]:
            low_pos = tlmedian-normalTemps[0]
        else:
            low_pos = tlmedian-normalTemps[1]

        if thmedian >= normalTemps[0] and thmedian <= normalTemps[1]:
            high_score += 1
        elif thmedian < normalTemps[0]:
            high_pos = thmedian-normalTemps[0]
        else:
            high_pos = thmedian-normalTemps[1]

        if low_score == high_score:
            if abs(low_pos) <= abs(high_pos):
                low_score += 1
            else:
                high_score += 1

        # Test 2 - Distance from center
        # Higher value -> background
        lval = get_mean_distance_from_center(lows_xys, rows, cols)
        hval = get_mean_distance_from_center(highs_xys, rows, cols)
        if lval > hval:
            low_score += 1
        elif hval > lval:
            high_score += 1

        # Test 3 - Mean distance of coordinates
        # Higher value -> background
        # Limit this test (slow for larg lists)
        if (len(lows_xys.T)<1000) and (len(highs_xys.T)<1000):
            lval = get_mean_distance_of_coordinates(lows_xys)
            hval = get_mean_distance_of_coordinates(highs_xys)
            if lval > hval:
                low_score += 1
            elif hval > lval:
                high_score += 1

        if low_score == high_score:
            low_score += int(preferHot_object)
            high_score += int(True-preferHot_object)

        # Decision
        if low_score > high_score:
            isHot_object = True
        else:
            isHot_object = False

    # Create masks section
    if (isMasks or isDeciles) and nums_int[index] in nums_graph:
        thresholds=[]
        if not isDeciles:
            thresholds = [threshold,tmin,th_pct05,th_mean_lm_lmin,tlmedian,th_mean_lmd_lm,th_lmean,
                          th_mean_lmd_md,th_mean_min_max,tmedian,tmean,
                          th_mean_lmd_hmd,th_mean_md_hmd,th_hmean,th_mean_hmd_hm,
                          th_hmedian,th_mean_hm_hmax,th_pct95,tmax]
        else:
           th_deciles=[]
           for i in range(0,10):
               thresholds.append(data_sorted[int(i/10*elements)])
        
        # Generate  masks for current thermogram
        #
        # Mask name templates (cth = cold threshold, hth = hot threshold):
        # 0001-04_mean_lmd_lm-cth.png
        # 0001-05_lmean-cth.png
        # or
        # 04_mean_lmd_lm-cth-0001.png
        # 05_lmean-cth-0001.png
        #
        # Deciles templates:
        # 0001-1_decile-hth.png
        # 0001-2_decile-hth.png
        # or
        # 0_decile-hth-0001.png
        # 1_decile-hth-0001.png
        
        j=0
        for stem in mask_names:
            tg_stem=stem+'-'
            if isHot_object:
                tg_stem+='hth'
            else:
                tg_stem+='cth'
            if isNumSort:
                tg_stem=nums[index]+'-'+tg_stem
            else:
                tg_stem=tg_stem+'-'+nums[index]
            tgname=tg_stem+'.png'
            
            th=thresholds[j]
            print(th,tgname)
            
            if isHot_object:
                mxys=find_indices_over_threshold(data, th)
                masked_data=np.where(data>=th,data,vmin)
            else:
                mxys=find_indices_under_threshold(data, th)
                masked_data=np.where(data<=th,data,vmax)
                
            # Save imagemap plots                
            fig=plt.figure()
            plt.ylim(rows-1,0)
            plt.xlim(0,cols-1)
            plt.xlabel(tg_xlabel)
            plt.ylabel(tg_ylabel)
            plt.title(tg_stem)
            plt.imshow(masked_data,vmin=vmin,vmax=vmax)
            cb=plt.colorbar()
            cb.ax.set_ylabel('Temperature (°C)')
            plt.savefig(dt_part+'-'+dirs[0]+'/im-'+tgname,dpi=300)
            plt.close()
            
            # Save scatter plots                
            fig=plt.figure()
            plt.ylim(rows-1,0)
            plt.xlim(0,cols-1)
            plt.xlabel(tg_xlabel)
            plt.ylabel(tg_ylabel)
            plt.title(tg_stem)
            plt.scatter(mxys[1],mxys[0])
            plt.savefig(dt_part+'-'+dirs[0]+'/sc-'+tgname,dpi=300)
            plt.close()

            j+=1
    
    # Analyze thermograms section
    if (not isMasks) and (not isDeciles):
        
        # Determine the threshold
        if method=='mask':
            if selection==0:    th=threshold
            elif selection==1:  th=tlmin
            elif selection==2:  th=th_pct05
            elif selection==3:  th=th_mean_lm_lmin
            elif selection==4:  th=tlmedian
            elif selection==5:  th=th_mean_lmd_lm
            elif selection==6:  th=tlmean
            elif selection==7:  th=th_mean_lmd_md
            elif selection==8:  th=th_mean_min_max
            elif selection==9:  th=tmedian
            elif selection==10:  th=tmean
            elif selection==11:  th=th_mean_lmd_hmd
            elif selection==12:  th=th_mean_md_hmd
            elif selection==13:  th=thmean
            elif selection==14:  th=th_mean_hmd_hm
            elif selection==15:  th=thmedian
            elif selection==16:  th=th_mean_hm_hmax
            elif selection==17:  th=th_pct95
            elif selection==18:  th=thmax
        else:
            th=data_sorted[int(selection/10*elements)]

        if isHot_object:
            mxys=find_indices_over_threshold(data, th)
            masked_data=np.where(data>=th,data,vmin)
        else:
            mxys=find_indices_under_threshold(data, th)
            masked_data=np.where(data<=th,data,vmax)    
                
        
        # Create thermograms of the selected frames
        # Template: im-0700.png
        # Template 0700-im.png
        if isNumSort:
            tg_stem=nums[index]+'-'+'-im'
        else:
            tg_stem='im-'+nums[index]
        if nums_int[index] in nums_graph:
            tgname=tg_stem+'.png'
           
            print('+ figures')

            # Save imagemap plots                
            fig=plt.figure()
            plt.ylim(rows-1,0)
            plt.xlim(0,cols-1)
            plt.xlabel(tg_xlabel)
            plt.ylabel(tg_ylabel)
            plt.imshow(masked_data,vmin=vmin,vmax=vmax)
            cb=plt.colorbar()
            cb.ax.set_ylabel('Temperature (°C)')
            plt.savefig(dt_part+'-'+dirs[1]+'/im-'+tgname,dpi=300)
            plt.close()
            
            
             # Plot x and y mean heat profiles
            xmeans=masked_data.mean(axis=0)
            ymeans=masked_data.mean(axis=1)
            
            fig=plt.figure()
            if isNumSort:
                tg_stem=nums[index]+'-'+'-tempx'
            else:
                tg_stem='tempx-'+nums[index]
            tgname=tg_stem+'.png'
            xs=np.arange(0,len(xmeans))
            plt.xlim(0,len(xs)-1)
            plt.ylim(xmeans.min(),xmeans.max())
            plt.plot(xs,xmeans)
            plt.xlabel('X coordinate')
            plt.ylabel('Temperature (°C)')
            if isGrid:
                plt.grid()
            plt.savefig(dt_part+'-'+dirs[1]+'/'+tgname,dpi=300)
            plt.close()
            
            fig=plt.figure()
            if isNumSort:
                tg_stem=nums[index]+'-'+'-tempy'
            else:
                tg_stem='tempy-'+nums[index]
            tgname=tg_stem+'.png'
            xs=np.arange(0,len(ymeans))
            plt.xlim(0,len(xs)-1)
            plt.ylim(ymeans.min(),ymeans.max())
            plt.plot(xs,ymeans)
            plt.xlabel('Y coordinate')
            plt.ylabel('Temperature (°C)')
            if isGrid:
                plt.grid()
            plt.savefig(dt_part+'-'+dirs[1]+'/'+tgname,dpi=300)
            plt.close()
            
            # Create a heat distribution graph
            if isNumSort:
                tg_stem=nums[index]+'-'+'-hist'
            else:
                tg_stem='hist-'+nums[index]
            tgname=tg_stem+'.png'
            if isHot_object:
                aflat=data[data>=th]
            else:
                aflat=data[data<=th]
            fig=plt.figure()
            cm = plt.cm.get_cmap('RdYlBu_r')
            num, bins, patches = plt.hist(aflat,bins=20,color='blue')
            bin_centers = 0.5 * (bins[:-1] + bins[1:])
            
            # scale values to interval [0,1]
            col = bin_centers - min(bin_centers)
            col /= max(col)
            
            for c, p in zip(col, patches):
                plt.setp(p, 'facecolor', cm(c))
        
            plt.xlabel('Temperature (°C)')
            plt.ylabel('Frequency')
            plt.savefig(dt_part+'-'+dirs[1]+'/'+tgname,dpi=300)
            plt.close()
    
        # Save the masked data
        np.savetxt(dt_part+'-'+dirs[2]+'/'+tg_stem+'.csv', masked_data, delimiter=',', fmt='%s')
    
        # Calculate and collect statistical data for the frame - section START
    
        # Calculate time for current frame
        if isPTS:
            tframe=tstart+pts[i]
        else:
            tframe=tstart+index*interval
        # Time unit: tunit
        
        # Frame statistics
        # tmin = np.min(data)
        # tmax = np.max(data)
        # tmean = np.mean(data)
        # tmedian = np.median(data)
    
        # Threshold
        if isHot_object:
            fmask_hot=1
        else:
            fmask_hot=0
        fmask_method=method
        if method=='mask':
            fmask_name=masks[selection][3:]
        else:
            fmask_name=masks[selection][2:]
        # Threshold temperature
        # th
        
        # Frame dimensions
        # rows
        # cols
        
        # Pixels (over or under thersholds)
        mxys=np.array(mxys)
        fmask_count=len(mxys.T)
        
        # Masked frame coordinates
        fmask_mean_x=mxys[1].mean()
        fmask_mean_y=mxys[0].mean()
        fmask_median_x=np.median(mxys[0].T)
        fmask_median_y=np.median(mxys[0].T)
        fmask_min_x=mxys[1].min()
        fmask_max_x=mxys[1].max()
        fmask_min_y=mxys[0].min()
        fmask_max_y=mxys[0].max()
        
        # Masked frame statistics
        mxys_temperatures=data[mxys[0],mxys[1]]
        fmask_mean_t=np.mean(mxys_temperatures)
        fmask_median_t=np.median(mxys_temperatures)
        fmask_sdev_t=np.var(mxys_temperatures)
        fmask_min_t=np.min(mxys_temperatures)
        fmask_max_t=np.max(mxys_temperatures)
        fmask_pixel_proportion=fmask_count/(rows*cols)
        
        # Calculate and collect statistical data for the frame - section END

        results.append([frame,nums_int[index],tframe,int(isHot_object),method,mask_names[selection],
                        int(isAuto_temp),th,
                        tmin,tmax,
                        tmean,tlmean,thmean,
                        tmedian,tlmedian,thmedian,tsdev,
                        fmask_count,fmask_min_t,fmask_max_t,
                        fmask_mean_t,fmask_median_t,fmask_sdev_t,
                        fmask_mean_x,fmask_mean_y,fmask_median_x,fmask_median_y,
                        fmask_min_x,fmask_max_x,fmask_min_y,fmask_max_y,
                        fmask_pixel_proportion
                        ])
        
    index+=1
    
# Create and save a log file
log=[]
base=dt_part+'-'+dirs[3]+'/'
adict=vars(args)
for key in adict.keys():
    log.append([key,adict[key]])
if (not isMasks) and (not isDeciles):
    with open(base+'arguments.log', 'w') as f:
        writer = csv.writer(f)   
        writer.writerows(log)
else:
    with open('arguments.log', 'w') as f:
        writer = csv.writer(f)   
        writer.writerows(log)


if (not isMasks) and (not isDeciles):
    print('Processing time series data.')
    # Write a summary CSV file
    fname=base+'data.csv'
    header=['Name','N','Time ('+tunit+')','Hot object','Method','Method name','Auto T',
            'Threshold',
            'min (°C)','max (°C)','mean (°C)','low mean (°C)','high mean (°C)',
            'median (°C)','low median (°C)','high median (°C)','sdev (°C)',
            'mask points','mask min (°C)','mask max (°C)',
            'mask mean (°C)','mask median (°C)','mask sdev (°C)',
            'mask mean (X)','mask mean (Y)','mask median (X)','mask median (Y)',
            'mask min (X)','mask max (X)','mask min(Y)','mask max (Y)',
            'proportion'
            ]
    
    with open(fname,'w',newline='\n') as csvfile:
        writer=csv.writer(csvfile,delimiter=',',quotechar='"')
        writer.writerow(header)
        for row in results:
            writer.writerow(row)

    # Create time series graphs
    ts=np.array(results)[:,2].astype(float)
    tlabel='Time ('+tunit+')'
    tdata=np.array(results)[:,7:].astype(float)
    
    # Plot global min,mean,median,max=f(t)
    ylabel='Temperature (°C)'
    ymaxs=tdata[:,2]
    ymedians=tdata[:,6]
    ymeans=tdata[:,3]
    ymins=tdata[:,1]
    curves=[['r',1,'-','Max'],
            ['k',1,'-','Median'],
            ['0.5',1,'-','Mean'],
            ['b',1,'-','Min']]
    multiplot(ts, tlabel, np.vstack([ymaxs,ymedians,ymeans,ymins]), ylabel, curves, 'temperatures_global','',0)
    
    # Plot object min,mean,median,max=f(t)
    ylabel='Temperature (°C)'
    if isHot_object:
        y_maxs=tdata[:,2]
        yo_hmedians=tdata[:,8]
        yo_hmeans=tdata[:,5]
        y_medians=tdata[:,6]
        curves=[['r',1,'-','Max'],
                ['k',1,'-','High median'],
                ['0.5',1,'-','High mean'],
                ['b',1,'-','Median']]
        multiplot(ts, tlabel, np.vstack([y_maxs,yo_hmedians,yo_hmeans,y_medians]), ylabel, curves, 'temperatures_high','',0)
    else:
        y_medians=tdata[:,6]
        yo_lmeans=tdata[:,4]
        yo_lmedians=tdata[:,7]
        y_mins=tdata[:,1]
        curves=[['r',1,'-','Median'],
                ['0.5',1,'-','Low mean'],
                ['k',1,'-','Low median'],
                ['b',1,'-','Min']]
        multiplot(ts, tlabel, np.vstack([y_medians,yo_lmeans,yo_lmedians,y_mins]), ylabel, curves, 'temperatures_low','',0)
    
    # Plot mask min,mean,median,max=f(t)
    ylabel='Temperature (°C)'
    if isHot_object:
        y_maxs=tdata[:,2]
        ymask_medians=tdata[:,14]
        ymask_means=tdata[:,13]
        ymask_min=tdata[:,11]
        curves=[['r',1,'-','Max'],
                ['k',1,'-','Mask median'],
                ['0.5',1,'-','Mask mean'],
                ['b',1,'-','Mask low']]
        multiplot(ts, tlabel, np.vstack([y_maxs,ymask_medians,ymask_means,ymask_min]), ylabel, curves, 'temperatures_mask_high','',0)
    else:
        ymask_max=tdata[:,12]
        ymask_means=tdata[:,13]
        ymask_medians=tdata[:,14]
        y_mins=tdata[:,1]
        curves=[['r',1,'-','Mask high'],
                ['0.5',1,'-','Mask mean'],
                ['k',1,'-','Mask median'],
                ['b',1,'-','Min']]
        multiplot(ts, tlabel, np.vstack([ymask_max,ymask_means,ymask_medians,y_mins]), ylabel, curves, 'temperatures_mask_low','',0)
    
    # Plot mask mean=f(t)
    ylabel='Temperature (°C)'
    ymask_means=tdata[:,13]
    curves=[['b',1,'-','Mask mean']]
    if isHot_object:
        tmp='High threshold: '
    else:
        tmp='Low threshold: '
    tmp+=masks[selection]
    multiplot(ts, tlabel, ymask_means, ylabel, curves, 'temperatures_mask_mean',tmp,0)
    
    # Plot mask median=f(t)
    ylabel='Temperature (°C)'
    ymask_medians=tdata[:,14]
    curves=[['b',1,'-','Mask median']]
    if isHot_object:
        tmp='High threshold: '
    else:
        tmp='Low threshold: '
    tmp+=masks[selection]
    multiplot(ts, tlabel, ymask_medians, ylabel, curves, 'temperatures_mask_median',tmp,0)
    
    # Over or under threshold proportion = f(t)
    ylabel='Proportion'
    ymask_medians=tdata[:,24]
    if isHot_object:
        tmp='High threshold: '
        curves=[['r',1,'-','Over threshold']]
    else:
        tmp='Low threshold: '
        curves=[['b',1,'-','Under threshold']]
    tmp+=masks[selection]
    multiplot(ts, tlabel, ymask_medians, ylabel, curves, 'threshold_pixels_proportion',tmp,0)
    
    
t2=datetime.now()
print("")
print("Time elapsed: "+str(t2-t1))

