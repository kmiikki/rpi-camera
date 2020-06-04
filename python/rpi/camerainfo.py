#!/usr/bin/python3
# (C) Kim Miikki 2020

import subprocess
from picamera import PiCamera

sensor_megapixels_dict= {
	#sensor: [megapixels,max_exposure]
	"imx219": [8,10e6],
	"imx477": [12.3,200e6]
}

camera_detected=0
camera_revision=""
camera_exif=""
camera_model=""
camera_make=""
camera_megapixels=-1
camera_maxres=""
camera_maxx=0
camera_maxy=0
camera_max_exposure=int(6e6) # Default maximum shutter speed, OV5647
videomodes=[]

# Detect if a camera module is present
tmp=subprocess.check_output("vcgencmd get_camera",shell=True)
tmp=tmp[:-1]
# Result format: b'supported=1 detected=0\n'
tmp=str(tmp).split("detected=")
camera_detected=int(tmp[1][0])

if camera_detected==1:
	camera=PiCamera()
	camera_revision=camera.revision
	camera_exif=camera.exif_tags
	camera.close()

	camera_model=camera_exif["IFD0.Model"]
	camera_make=camera_exif["IFD0.Make"]
	camera_maxres=str(camera.MAX_RESOLUTION)
	resolution=camera_maxres.split("x")
else:
	camera_revision="N/A"
	camera_model="N/A"
	camera_make="N/A"
	camera_maxres="-1x-1"
	resolution=camera_maxres.split("x")
camera_maxx=int(resolution[0])
camera_maxy=int(resolution[1])

try:
	camera_megapixels=sensor_megapixels_dict[camera_revision][0]
	camera_max_exposure=int(sensor_megapixels_dict[camera_revision][1])
except:
	camera_megapixels=-1
	
if camera_revision=="imx219":
	# MD, Description, A/R,  FOV (0 = Partial and 1 = Full)
	# x0, y0, ROI w, ROI h, fps_min, fps_max
	videomodes=[
		[1," 1920x1080","16:9",0,680,692,1920,1080,0.1,30],
		[2," 1920x1080","16:9",1,0,310,3280,1845,0.1,15],
		[3," 1920x1080","16:9",1,0,310,3280,1845,0.1,15],
		[4," 1640x1232"," 4:3",1,0,0,3280,2464,0.1,40],
		[5,"  1640x922","16:9",1,0,310,3280,1845,0.1,40],
		[6,"  1280x720","16:9",0,360,512,2560,1440,40,90],
		[7,"   640x480"," 4:3",0,1000,752,1280,960,40,200]
	]
elif camera_revision=="imx477":
	# MD, Description, A/R, FOV (0 = Partial and 1 = Full)
	# video x, video y, FOV w, FOW h, FPS min, FPS max
	# ROI values are manually calibrated with rulers
	# Video modes 2 (2028x1520) and 3 (4056x3040) have been
	# tested on 1.6.2020: failure
	# => Mode 2 resolution decreased to 2028x1080
	# => Mode 3 resolution decreased to 1600x1200
	videomodes=[
		[1," 2028x1080","169:90",0,108,442,3845,2162,0.1,50],
		[2," 2028x1080","169:90",1,0,380,4056,2274,0.1,50],
		[3," 1600x1200","   4:3",1,0,0,4056,3040,0.005,10],
		[4,"  1012x760","   4:3",1,0,0,4056,3040,50.1,120],
	]

