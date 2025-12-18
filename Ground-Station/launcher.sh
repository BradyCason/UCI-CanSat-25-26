#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home


export DISPLAY=:0
export XAUTHORITY=$HOME/.Xauthority
# export XDG_RUNTIME_DIR=/tmp/runtime-$USER

USER=$(whoami)

cd /home/$USER/UCI-CanSat-25-26/Ground-Station/
sudo python3 controls.py
cd /home/$USER

# cd $HOME/UCI-CanSat-25-26/Ground-Station/
# sudo python3 controls.py
# cd $HOME
