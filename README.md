# UCI-CanSat-25-26
Ground Station and Flight Software for 2025-26 CanSat Competition


## Raspberry Pi Custom Configuration
The Raspberry Pi 4B is the computer for the Ground Station.
The CanSat competition requires that the Ground Station must be fully functional without any further user configuration once the system is powered on and the program is running. 
This mean that we must automatically run our program upon the RPi's boot. 
This is done with a "systemd service job file" with the following contents:
```
insert
```

Configuration for Raspberry Pi external power button:
In the boot/firmware/config.txt file, add the following lines:
```
dtoverlay=gpio.shutdown ... insert
```

### To find the port that the XBee is connected on  
Run the following command  
```
ls /dev/tty*
```
Disconnect device  
Run the command  
Reconnect the device  

### To open pyqt designer from the terminal
```
pyqt5-tools designer
```
