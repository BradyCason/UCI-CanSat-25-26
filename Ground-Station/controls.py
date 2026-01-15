import RPi.GPIO as GPIO
import time
import subprocess
import signal, sys

# One LED to flash for Xbee transmission indication 
XbeeLED = 22 # could be any GPIO 

pin_9 = 9     # Press to enable simulation button
pin_14 = 14   # Press to activate simulation input toggle (to CanSat)
pin_15 = 15   # Press to deactivate simulation input toggle (to CanSat)
pin_11 = 11   # Press to set coordinates button
pin_13 = 13   # Press to set time UTC button
pin_26 = 26   # Press to set time GPS
pin_5 = 5     # Press to release egg 
pin_27 = 27   # Press to release paraglider
pin_4 = 4     # Press to Release payload
pin_18 = 18   # Press to show graphs
pin_21 = 21   # Press to reset state
pin_16 = 16   # Press to Calibrate altitude button

pin_7 = 7     # Telemetry toggle on
pin_8 = 8     # Telemetry toggle off
pin_25 = 25   # Green led on while telemetry toggled on 
pin_24 = 24   # Red led on while telemetry toggled off
pin_10 = 10   # LED indicator for simulation enable button
pin_23 = 23   # LED indicator for simulation activate toggle
pin_1 = 1     # LED indicator for simulation deactivate toggle


# Abstract the pin numbers with names
enableSim = pin_9
activateSim = pin_14
deactivateSim = pin_15
setCoords = pin_11
setTimeUTC = pin_13
setTimeGPS = pin_26
releaseEgg = pin_5
releaseParaglider = pin_27
releasePayload = pin_4
showGraphs = pin_18
resetState = pin_21
calibrateAltitute = pin_16
readTelemetryOn = pin_7   
readTelemetryOff = pin_8 
LEDTelemetryOn = pin_25 
LEDTelemetryOff = pin_24
LEDSimEnable = pin_10
LEDSimActivate = pin_23
LEDSimDeactivate = pin_1 


###########################################################################

GPIO.setmode(GPIO.BCM)

GPIO.setup(activateSim, GPIO.IN, pull_up_down=GPIO.PUD_UP)        # activate simulation toggle (to CanSat)
GPIO.setup(deactivateSim, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # deactivate simulation toggle (to CanSat)
GPIO.setup(enableSim, GPIO.IN, pull_up_down=GPIO.PUD_UP)          # simulation enable button
GPIO.setup(setCoords, GPIO.IN, pull_up_down=GPIO.PUD_UP)          # set coordinates button
GPIO.setup(releaseEgg, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # release egg button
GPIO.setup(setTimeUTC, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # set time UTC button
GPIO.setup(setTimeGPS, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # set time GPS button
GPIO.setup(releaseParaglider, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # paraglider release button
GPIO.setup(releasePayload, GPIO.IN, pull_up_down=GPIO.PUD_UP)     # payload release button
GPIO.setup(showGraphs, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # Show graphs
GPIO.setup(resetState, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # Reset State
GPIO.setup(calibrateAltitute, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Calibrate Altitude
GPIO.setup(readTelemetryOn, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Read telemetry on
GPIO.setup(readTelemetryOff, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Read teleemtry off

# LEDs setup
GPIO.setup(LEDTelemetryOn, GPIO.OUT)  
GPIO.output(LEDTelemetryOn, GPIO.LOW)
GPIO.setup(LEDTelemetryOff, GPIO.OUT)
GPIO.output(LEDTelemetryOff, GPIO.LOW)
GPIO.setup(XbeeLED, GPIO.OUT)
GPIO.output(XbeeLED, GPIO.LOW)
GPIO.setup(LEDSimEnable, GPIO.OUT)
GPIO.output(LEDSimEnable, GPIO.HIGH)    # Begins lit green
GPIO.setup(LEDSimActivate, GPIO.OUT)
GPIO.output(LEDSimActivate, GPIO.LOW)
GPIO.setup(LEDSimDeactivate, GPIO.OUT)
GPIO.output(LEDSimDeactivate, GPIO.LOW)

###########################################################################

# Helper function to flash an LED given its current state 
def flash_led(LED):
    for i in range(3):
        GPIO.output(LED, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(LED, GPIO.LOW)
        time.sleep(0.3)
        # Need to revise so it is not interrupting program exeuction via sleep

def _cleanup_and_exit(signum, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, _cleanup_and_exit)
signal.signal(signal.SIGINT, _cleanup_and_exit)

telemetry_func_called = False # Helper variable to ensure not infinitely calling the function when we switch to enable it
simulation_enabled = False # Simulation enable handling variable
sim_activated = False # Simulation active handling variable
sim_disabled = False # Simulation disable handling variable
graph_proc = None
prev_state_showGraphs = GPIO.HIGH

###########################################################################

try:

    while True:

        prev = prev_state_showGraphs

        state_enableSim = GPIO.input(enableSim)                 # simulation enable button
        state_activateSim = GPIO.input(activateSim)             # activate simulation toggle (to CanSat)
        state_deactivateSim = GPIO.input(deactivateSim)         # deactivate simulation toggle (to CanSat)
        state_setCoords = GPIO.input(setCoords)                 # set coordinates button
        state_releaseEgg = GPIO.input(releaseEgg)               # Release egg button
        state_setTimeUTC = GPIO.input(setTimeUTC)               # set time UTC button
        state_setTimeGPS = GPIO.input(setTimeGPS)               # set time GPS button
        state_releaseParaglider = GPIO.input(releaseParaglider) # paraglider release button
        state_releasePayload = GPIO.input(releasePayload)       # payload release button
        state_showGraphs = GPIO.input(showGraphs)               # show graphs
        state_resetState = GPIO.input(resetState)               # reset state
        state_calibrateAltitude = GPIO.input(calibrateAltitute) # calibrate altitude
        state_readTelemetryOn = GPIO.input(readTelemetryOn)     # toggle to telemetry Enable
        state_readTelemetryOff = GPIO.input(readTelemetryOff)   # toggle to telemetry Disable

        if state_enableSim == GPIO.LOW and simulation_enabled == False:
            print("Simulation Enabled")
            simulation_enabled = True
            GPIO.output(pin_10, GPIO.LOW)
            print("Pin 10 LED ON to indicate simulation enabled")
            GPIO.output(pin_23, GPIO.HIGH) 

        if state_activateSim == GPIO.LOW and sim_activated == False and sim_disabled == False:
            print("Simulation Activated")
            print("Send activation signal to CanSat...")
            GPIO.output(pin_23, GPIO.LOW)
            GPIO.output(pin_1, GPIO.HIGH)
            sim_disabled = True
            simulation_enabled = False
        
        if state_deactivateSim == GPIO.LOW and simulation_enabled == False and sim_disabled == True:
            print("Simulation Deactivated")
            print("Send deactivation xbee signal to CanSat...")
            GPIO.output(pin_1, GPIO.LOW)
            GPIO.output(pin_10, GPIO.HIGH)
            sim_disabled = False
            sim_activated = False
            simulation_enabled = False

        if state_setCoords == GPIO.LOW : 
            print("Set coordinates button pressed")
            print("Pin 11 button pressed, do work...")
        
        if state_releaseEgg == GPIO.LOW :
            print("Release egg button pressed")
            print("Pin 5 button pressed, do work...")
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_setTimeUTC == GPIO.LOW :
            print("Set UTC time button pressed")
            print("Pin 13 button pressed, do work...")
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_setTimeGPS == GPIO.LOW :
            print("Set GPS time button pressed")
            print("Pin 26 button pressed, do work...")
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_releaseParaglider == GPIO.LOW :
            print("Paraglider release button pressed")
            print("Pin 27 button pressed, do work...")
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_releasePayload == GPIO.LOW :
            print("Payload release button pressed")
            print("Pin 4 button pressed, do work...")
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_calibrateAltitude == GPIO.LOW :
            print("Button pressed")
            print("Pin 16 active, do work:") 
            print("For example: calibrate altitude")
            # call some other functions  that do the work
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_readTelemetryOn == GPIO.LOW and telemetry_func_called == False:
            print("Telemetry enabled")
            print("Call telemetry enabling function to do work...")
            telemetry_func_called = True
            GPIO.output(pin_24, GPIO.LOW)
            GPIO.output(pin_25, GPIO.HIGH)
        
        if state_readTelemetryOff == GPIO.LOW and telemetry_func_called == True:
            print("Telemetry Disabled")
            print("Disable or interrupt or stop the execution of the telemetry handling function...")
            telemetry_func_called = False
            GPIO.output(pin_25, GPIO.LOW)
            GPIO.output(pin_24, GPIO.HIGH)

        if state_resetState == GPIO.LOW :
            print("Pin 21 button pressed, call reset state function")
            flash_led(XbeeLED)
            print("Pin {XbeeLED} flashes xbee status LED to show sending xbee packet")

        if state_showGraphs == GPIO.LOW and prev == GPIO.HIGH:
            print("Pin 18 button pressed, show graphs")
            if graph_proc is None or graph_proc.poll() is not None:
                graph_proc = subprocess.Popen(['python3','/home/jonathan/UCI-CanSat-25-26/Ground-Station/mini_map_test.py'])
                time.sleep(0.2)
        prev_state_showGraphs = state_showGraphs

        time.sleep(0.1) # global delay and debouncing adjustment
    
except KeyboardInterrupt:
    print("Exiting program")

finally:
    GPIO.cleanup()