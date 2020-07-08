#!/usr/bin/python3

import sys

def partition(lst, n):
  division = len(lst) / n
  return [lst[round(division * i):round(division * (i + 1))] for i in range(n)]

def distanceextract(lst): 
    return [item[3] for item in lst]

def distancesort(sub_li): 
  
    # reverse = None (Sorts in Ascending order) 
    # key is set to sort using second element of  
    # sublist lambda has been used 
    return(sorted(sub_li, key = lambda x: x[2]))  

arguments=len(sys.argv)
if arguments==1:
    print("Usage: optimum-gains.py RGB-file_name.txt")
    exit(0)
elif arguments>2:
    print("Too many arguments!")
    exit(1)

filename=sys.argv[1]
file = open(filename, "r") 
sampling = 1

lines = file.readlines()
count = len(lines)
# listorder = ["exp_time2", "r_gain3", "b_gain4", "r_avg6", "g_avg7", "b_avg8"]
dfs = list()
disposed=0
for x in range(1,count):
    defsets = lines[x].split(";")
    defset = [float(defsets[1]), float(defsets[2]), float(defsets[3]), \
              float(defsets[5]), float(defsets[6]), float(defsets[7])]
#    indices = [1,2,3,5,6,7]
#   defset = np.take(defsets,indices)
#     defset = [float(defset[i]) for i in len(indices)]

  # Dispose under- and overexposed images
  # R, G, B thresholds: minimum 0.5 and maximum 254.5
    if (defset[3]<0.5 or defset[3]>254.5) and \
        (defset[4]<0.5 or defset[4]>254.5) and \
        (defset[5]<0.5 or defset[5]>254.5):
        disposed+=1
    else:
        distance = abs(defset[3]-defset[4]) + abs(defset[4]-defset[5]) \
                 + abs(defset[5]-defset[3])
        defsetdistance = [defset[0],defset[1],defset[2],distance]
        dfs.append(defsetdistance)
count=len(dfs)
if disposed>0:
  print("Under- or overexposed images (which are not included in calibration): "+str(disposed))
  print("Valid images for calibration: "+str(count))
else:
  print("Calibration images: "+str(count))

if count>0:
    #count = int(count/sampling)
    #defsetdistsample =  partition(dfs,count)
    exposuretime=int(lines[1].split(";")[1])

    dfsflatten = list()

    for i in range(len(dfs)): #Traversing through the main list
      for j in range (len(dfs[i])): #Traversing through each sublist
        dfsflatten.append(dfs[i][j]) #Appending elements into our flat_list
      
    #Sampling is the number of exposures used for each r_ and b_gains
    samplinglists = dfsflatten.count(exposuretime)
    #print("Sampling = ", samplinglists)
    #sampling = int((count-1) / samplinglists)

    #Partitioning of the total list into exposure sampling sets
    #count = int((count-1)/sampling)
    defsetdistsample =  partition(dfs,samplinglists)  
    
    dft = list()
    for x in range(0,samplinglists):
        dists = distanceextract(defsetdistsample[x])
        totaldist = sum(dists)
        defsettotaldist = [defsetdistsample[x][0][1],defsetdistsample[x][0][2], \
                           totaldist]
        dft.append(defsettotaldist)

    optimal = distancesort(dft)[0]
    #print(distancesort(dft))
    print("Optimal r_gain = ", optimal[0])
    print("Optimal b_gain = ", optimal[1])
    print("Total distance = ", optimal[2])
else:
    print("No valid calibration data!\nUnable to calculate optimal calibration values.")
