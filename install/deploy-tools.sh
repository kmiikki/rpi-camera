#!/usr/bin/env bash

# Deployment:
# Change directory to rpi-camera-master/install
# $ bash deploy-tools.sh

# Create target directories
sudo mkdir -p /opt/tools
sudo mkdir -p /opt/tools/rpi
sudo mkdir -p /opt/tools/documentation

# Copy all files to their targets
sudo rsync -av --exclude=deploy-tools.sh ../python/ /opt/tools
sudo rsync -av ../documentation/*.pdf /opt/tools/documentation

# Enable executing of *.py files
sudo chmod ugo+rx /opt/tools/*.py
sudo chmod ugo+rx /opt/tools/rpi/*.py
