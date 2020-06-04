#!/usr/bin/python3
# (C) Kim Miikki 2020

from rpi.camerainfo import *

if camera_detected==1:
	print("Raspberry Pi camera module")
	print("  revision:".ljust(14),camera_revision)
	print("  model:".ljust(14),camera_model)
	print("  make:".ljust(14),camera_make)
	print("  megapixels:".ljust(14),camera_megapixels)
	print("  max x:".ljust(14),camera_maxx)
	print("  max y:".ljust(14),camera_maxy)
else:
	print("Raspberry Pi camera module not found!")
