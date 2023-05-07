#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 24 11:08:19 2023

@author: Kim Miikki
"""
import argparse
import csv
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.colors as colors
# colors.cnames
from datetime import datetime
from pathlib import Path

outdir='csv_tl'

cols=0
rows=0
xcol=0
ycols=[]

px=1920
py=1080
pr=px/py
minpx=64
minpy=int(minpx/pr)

default_size=8

fontsize=default_size
axeslabelsize=default_size
isBoldLabels=False
linew=0.25
gridw=0.5

xmin=0
xmax=0
y1min=0
y1max=0
y2min=0
y2max=0
isXmin=False
isXmax=False
isY1min=False
isY1max=False
isY2min=False
isY2max=False

dpi=300
ycols_pri=[]
ycols_sec=[]
legends=['upper left','upper center','upper right',
           'center left','center','center right',
           'lower left','lower center','lower right']
palette=['blue','red','green','cyan','magenta','gold',
         'black','deeppink','darkblue','aquamarine','gray','maroon',
         'indigo','olive','teal','hotpink','salmon','purple','peru','orchid',
         'peru','limegreen','khaki','lightpink','plum','darkmagenta']
maxcolors=len(palette)
isPx=False
isPy=False
isPr=False
isGrid=True
isLogX=False
isLogY1=False
isLogY2=False
isLegend=False
isLabelX=False

genLast=False

legend=0
legfont=default_size
lega=1.0

xlabel='X'
y1label='Y1 data'
y2label='Y2 data'


# Set the print options to suppress scientific notation
np.set_printoptions(suppress=True)

def unique(arglist):
    x = np.array(arglist)
    return np.unique(x)

def getColumns(argstr):
    columns=[]
    s=argstr.strip()
    # Find character ','
    list1=s.split(',')
    list1=unique(list1)

    # Find ranges and add all numbers into a list
    for element in list1:
        isNumeric=element.isnumeric()
        # Test if element is a range
        error=False
        if not isNumeric:
            tmp=element.split('-')
            if len(tmp) != 2:
                error=True
            else:
                isFirst=True
                a=-1
                b=-1
                for n in tmp:
                    if not n.isnumeric():
                        error=True
                    else:
                        if isFirst:
                            a=int(n)
                            isFirst=False
                        else:
                            b=int(n)
                if not error:
                    if b<=a:
                        error=True
                if not error:
                    i=a
                    while i<=b:                                           
                        columns.append(i)
                        i+=1
        else:
            columns.append(int(element))
    return unique(columns)

def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))

print("Generate time-lapse images from a CSV file")

# Get current directory
curdir=os.getcwd()
path=Path(curdir)
foldername=os.path.basename(curdir)
print("")
print("Current directory:")
print(curdir)
print('')
if curdir!='/':
    curdir+='/'

parser=argparse.ArgumentParser()
parser.add_argument('name', type=str, help='CSV filename')
parser.add_argument('-x', help='x column position', type=int, default=0, required=False)
parser.add_argument('-y', help='y positions of columns (separation=, range number1-numer2', type=str, required=False)
parser.add_argument('-s', help='y positions for secondary axis data', type=str, required=False)
parser.add_argument('-px', help='graph width in pixels', type=int, required=False)
parser.add_argument('-py', help='graph height in pixels', type=int, required=False)
parser.add_argument('-pr', help='graph width/height ratio as float', type=float, required=False)
parser.add_argument('-xmin', help='y1 axis minimum value', type=float, required=False)
parser.add_argument('-xmax', help='y1 axis maximum value', type=float, required=False)
parser.add_argument('-y1min', help='y1 axis minimum value', type=float, required=False)
parser.add_argument('-y1max', help='y1 axis maximum value', type=float, required=False)
parser.add_argument('-y2min', help='y2 axis minimum value', type=float, required=False)
parser.add_argument('-y2max', help='y2 axis maximum value', type=float, required=False)
parser.add_argument('-logx',action='store_true',help='logarithmic x scales',required=False)
parser.add_argument('-logy1',action='store_true',help='logarithmic y1 scales',required=False)
parser.add_argument('-logy2',action='store_true',help='logarithmic y1 scales',required=False)
parser.add_argument('-legpos', help='enable legend with position (1-9)', type=int, required=False)
parser.add_argument('-legfont', help='legend font size', type=float, default=fontsize, required=False)
parser.add_argument('-lega', help='legend alpha value (0-1)', type=float, required=False)
parser.add_argument('-lx', help='x axis label', type=str, required=False)
parser.add_argument('-ly1', help='y1 axis label', type=str, required=False)
parser.add_argument('-ly2', help='y1 axis label', type=str, required=False)
parser.add_argument('-fsize', help='label font size', type=float, default=fontsize, required=False)
parser.add_argument('-asize', help='axes font size', type=float, default=axeslabelsize, required=False)
parser.add_argument('-size', help='global font size', type=float, required=False)
parser.add_argument('-b',action='store_true',help='enable bold font style for labels',required=False)
parser.add_argument('-l',action='store_true',help='generate the last graph',required=False)
# add legend
args = parser.parse_args()
isComment=False

# Check and assign arguments
if args.x != None:
    xcol=int(args.x)
if args.y != None:
    y=str(args.y)
    ycols=getColumns(y)
if args.s != None:
    s=str(args.s)
    ycols_sec=getColumns(s)

if args.px != None:
    val=int(args.px)
    if val<minpx:
        print('Graph width too small (px>='+str(minpx)+'). Using default value: '+str(minpx))
        isComment=True
    else:
        px=val
        isPx=True

if args.py != None:
    val=int(args.py)
    if val<minpy:
        print('Graph height too small (py>='+str(minpy)+'). Using default value: '+str(minpy))
        isComment=True
    else:
        py=val
        isPy=True

isDims=[isPx,isPy]
if args.pr != None:
    val=float(args.pr)
    if val<=0:
        print('Invalid graph width/ratio (pr>0). Using default value: '+str(pr))
        isComment=True
    elif False not in isDims:
        pr=px/py
        print('Graph width and hight are both defined. Overriding specified -pr value ('+str(val)+') with the calculated ratio: '+str(pr))
        isComment=True
    if not isComment:
        pr=val
        if isPx and not isPy:
            py=int(px/pr)
        else:
            px=int(pr*py)
    
if args.xmin != None:
    xmin=float(args.xmin)
    isXmin=True
if args.xmax != None:
    xmax=float(args.xmax)
    isXmax=True
    
if args.y1min != None:
    y1min=float(args.y1min)
    isY1min=True
if args.y1max != None:
    y1max=float(args.y1max)
    isY1max=True
if args.y2min != None:
    y2min=float(args.y2min)
    isY2min=True
if args.y2max != None:
    y2max=float(args.y2max)
    isY2max=True

if isXmin and isXmax:
    if xmax<=xmin:
        print('Primary axis xmax must be greater than xmin. Using default: auto')
        isXmax=False
        isComment=True

if isY1min and isY1max:
    if y1max<=y1min:
        print('Primary axis y1max must be greater than y1min. Using default: auto')
        isY1max=False
        isComment=True

if isY2min and isY2max:
    if y2max<=y2min:
        print('Primary axis y1max must be greater than y1min. Using default: auto')
        isY2max=False
        isComment=True

if xcol in ycols:
    print('Same x and y column selected! The program is terminated.')
    sys.exit(0)

if args.logx:
    isLogX=True
if args.logy1:
    isLogY1=True
if args.logy2:
    isLogY2=True
if args.legfont != None:
    legfont=float(args.legfont)
if args.fsize != None:
    fontsize=float(args.fsize)
if args.asize != None:
    axeslabelsize=float(args.asize)
if args.b:
    isBoldLabels=True

if args.legpos != None:
    val=int(args.legpos)
    if val in list(range(1,10)):
        legend=val-1
        isLegend=True
    else:
        print('Legend selection is out of range (1-9). The legend is disabled.')
        isLegend=False
        isComment=True
if args.lega != None:
    val=float(args.lega)
    if val<0 or val>1:
        print('Legend alpha is out range (0-1). The legend is disabled')
        isLegend=False
        isComment=True
    else:
        lega=val
        isLegend=True

if args.size != None:
    val=float(args.size)
    legfont=val
    fontsize=val
    axeslabelsize=val

if args.lx != None:
    xlabel=args.lx
    isLabelX=True
if args.ly1 != None:
    y1label=args.ly1
if args.ly2 != None:
    y2label=args.ly2

if args.l:
    genLast=True

if not genLast:
    try:
        if not os.path.exists(outdir):
            os.mkdir(outdir)
    except OSError:
        print("Unable to create a directory or directories under following path:\n"+curdir)
        print("Program is terminated.")
        print("")
        sys.exit(1)    

# Open the CSV data file
csvname=args.name
try:
    data = np.genfromtxt(csvname, delimiter=',', names=True)
    cols=len(data.dtype)
    rows=len(data)
    # Read header data
    with open(csvname, 'r') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
    #Convert the list of tuples to an array
    data=np.array([list(x) for x in data])
    data=data.T
    # Trim header names
    i=0
    for h in fieldnames:
       fieldnames[i]=h.strip()
       i+=1
except OSError:
    print('Missing or unable to open the CSV file')
    sys.exit(0)

if cols<1:
    print('The CSV file must have at least 2 data columns which are separted by a \' character.')
    sys.exit(0)

if args.y==None:
    # Select all columns except the x column
    ycols=list(range(0,cols))
    ycols.pop(xcol)
    
if len(ycols)==0:
    print('No y column/columns selected!')
    sys.exit(0)

# Get the intersection for ys and secondary ys
if len(ycols_sec)>0:
    #ycols_sec=intersection(ycols_sec, ycols)
    # Union
    ycols=list(set(ycols) | set (ycols_sec))

if max(ycols)>cols-1:
    print('Maximum allowed column number ('+str(cols-1)+') is exceeded!')
    sys.exit(0)

# Difference
ycols_pri=list(set(ycols)-set(ycols_sec))
ycols_pri.sort()

if isComment:
    print('')
print('Graph size')
print('----------')
print('Width:  '+str(px))
print('Height: '+str(py))
print('W/H   : '+str(round(pr,2)))

# Create a color table for graphs'Y2 data', color='b'
# Template: data column, color index, secondary y axis (Bool)
graphcol=[]
j=0
for i in ycols:
    graphcol.append([i,palette[j],i in ycols_sec])
    j+=1

isPrimary=bool(len(ycols_pri))
isSecondary=bool(len(ycols_sec))

# Set limits for x axis
if not isXmin:
    xmin=data[xcol][0]
if not isXmax:
    xmax=data[xcol][-1]
    
# Find limits for primary and secondary y-axis
if isPrimary:
    for i in ycols_pri:
        if not isY1min:
            vmin=data[i].min()
            if vmin<y1min:
                y1min=vmin
        if not isY1max:
            vmax=data[i].max()
            if vmax>y1max:
                y1max=vmax
if isSecondary:
    for i in ycols_sec:
        if not isY2min:
            vmin=data[i].min()
            if vmin<y2min:
                y2min=vmin
        if not isY2max:
            vmax=data[i].max()
            if vmax>y2max:
                y2max=vmax


# Calculate graph width and height in inches
width=px/dpi
height=py/dpi

if (not isLabelX) and (fieldnames[xcol] != ''):
    xlabel=fieldnames[xcol]

if isBoldLabels:
    fontweight='bold'
else:
    fontweight='normal'


# Generate a graph with complete data (= final image of the time-lapse graphs)
if genLast:
    outdir=''
    j=rows-1
else:
    outdir+='/'
    j=0
    digits=len(str(rows))

t1=datetime.now()
print("\nProcessing:")

while j<rows:
    fig,ax1=plt.subplots()
    fig.set_figheight(height)
    fig.set_figwidth(width)
    plt.xlabel(xlabel, fontsize=fontsize, fontweight=fontweight)
    plt.ylabel(y1label, fontsize=fontsize, fontweight=fontweight)
    ax1.tick_params(labelsize=axeslabelsize)
    
    if isLogX:
        plt.xscale('log')
    if isLogY1:
        ax1.set_yscale('log')        
    
    plt.xlim(xmin,xmax)
    plt.ylim(y1min,y1max)
    
    if isGrid:
        plt.grid()
        plt.grid(linewidth=gridw)
    
    if isSecondary:
        ax2=ax1.twinx()
        plt.ylim(y2min,y2max)        
        ax2.set_ylabel(y2label, fontsize=fontsize, fontweight=fontweight)
        if isLogY2:
            ax2.set_yscale('log')
        ax2.tick_params(labelsize=axeslabelsize)
        
    # Plot all graphs
    lines=[]
    labels=[]
    for i,color,sec in graphcol:
        #print(i,color,sec)    
        if not sec:
            line,=ax1.plot(data[xcol][:j],data[i][:j],color,linewidth=linew)
        else:
            line,=ax2.plot(data[xcol][:j],data[i][:j],color,linewidth=linew)
        if isLegend:
            lines.append(line)
            labels.append(fieldnames[i])
    
    if isLegend:
        ax1.legend(handles=lines, labels=labels, framealpha=lega, loc=legends[legend],fontsize=legfont)
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    if genLast:
        name=Path(csvname).stem
    else:
        name=str(j).zfill(digits)
        print(outdir,end='')
    print(name)
    plt.savefig(curdir+outdir+name+'.png',dpi=dpi)
    plt.close()
    j+=1

t2=datetime.now()
print("")
print("Time elapsed: "+str(t2-t1))

