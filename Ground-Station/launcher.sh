#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

 export DISPLAY=:0
 export XAUTHORITY=/home/brcason/.Xauthority

cd /home/brcason/UCI-CanSat-25-26/Ground-Station
sudo python controls.py
cd /home/brcason/
