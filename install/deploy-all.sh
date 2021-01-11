#!/usr/bin/env bash

# Deployment:
# Change directory to rpi-camera-master/install
# $ bash deploy-all.sh

# Update system
sudo apt update -y
sudo apt dist-upgrade -y
sudo apt autoremove -y

# Create target directories
sudo mkdir -p /opt/scripts
sudo mkdir -p /opt/tools
sudo mkdir -p /opt/tools/rpi
sudo mkdir -p /opt/tools/documentation

# Copy all files to their targets
sudo rsync -av --exclude=deploy-tools.sh ../python/ /opt/tools
sudo rsync -av ../documentation/*.pdf /opt/tools/documentation
sudo rsync -av paths/*.sh /etc/profile.d
sudo rsync -av scripts/*.sh /opt/scripts

# Enable executing of *.py files
sudo chmod ugo+rx /opt/tools/*.py
sudo chmod ugo+rx /opt/tools/rpi/*.py
sudo chmod ugo+rx /opt/scripts/*.sh

# Restart the system
reboot
