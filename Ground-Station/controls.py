import RPi.GPIO as GPIO
import time
import subprocess
import signal, sys

pin_14 = 14 # activate simulation input toggle (to CanSat)
pin_23 = 23 # LED indicator for simulation activate toggle

pin_15 = 15 # deactivate simulation input toggle (to CanSat)
pin_1 = 1 # LED indicator for simulation deactivate toggle

pin_9 = 9 # simulation enable button
pin_10 = 10 # LED indicator for simulation enable button

pin_11 = 11 # set coordinates button

pin_5 = 5 # release egg button
# pin_0 = 0 # LED indicator for release egg button

pin_13 = 13 # Set time UTC button
# pin_6 = 6   # LED indicator for set time UTC button

pin_26 = 26 # set time GPS
# pin_19 = 19 # LED indicator for set time GPS button
pin_19 = 19 # global LED indicator for XBEE packet sending indication

pin_27 = 27 # release paraglider
# pin_22 = 22 # LED indicator for paraglider release button

pin_4 = 4 # Release payload
# pin_17 = 17 # LED indicator for payload release button

pin_18 = 18 # show graphs

pin_21 = 21 # press to reset state
# pin_20 = 20 # flash led to indicate reseting state packet sending

pin_16 = 16 # example: calibrate altitude button
# pin_12 = 12 # example: LED indicator for calibrate altitue button

# example toggle switch application:
pin_7 = 7 # example: telemetry toggle on
pin_8 = 8 # example: telemetry toggle off
pin_25 = 25 # example: green led on while telemetry toggled on 
pin_24 = 24 # example: red led on while telemetry toggled off

###########################################################################

GPIO.setmode(GPIO.BCM)

GPIO.setup(pin_14, GPIO.IN, pull_up_down=GPIO.PUD_UP) # activate simulation toggle (to CanSat)
GPIO.setup(pin_15, GPIO.IN, pull_up_down=GPIO.PUD_UP) # deactivate simulation toggle (to CanSat)

GPIO.setup(pin_23, GPIO.OUT)
GPIO.output(pin_23, GPIO.LOW)

GPIO.setup(pin_1, GPIO.OUT)
GPIO.output(pin_1, GPIO.LOW)

GPIO.setup(pin_9, GPIO.IN, pull_up_down=GPIO.PUD_UP) # simulation enable button
GPIO.setup(pin_10, GPIO.OUT)
GPIO.output(pin_10, GPIO.HIGH)

GPIO.setup(pin_11, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set coordinates button

GPIO.setup(pin_5, GPIO.IN, pull_up_down=GPIO.PUD_UP) # release egg button
# GPIO.setup(pin_0, GPIO.OUT)
# GPIO.output(pin_0, GPIO.LOW)

GPIO.setup(pin_13, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set time UTC button
# GPIO.setup(pin_6, GPIO.OUT)
# GPIO.output(pin_6, GPIO.LOW)

GPIO.setup(pin_26, GPIO.IN, pull_up_down=GPIO.PUD_UP) # set time GPS button
GPIO.setup(pin_19, GPIO.OUT)
GPIO.output(pin_19, GPIO.LOW)

GPIO.setup(pin_27, GPIO.IN, pull_up_down=GPIO.PUD_UP) # paraglider release button
# GPIO.setup(pin_22, GPIO.OUT)
# GPIO.output(pin_22, GPIO.LOW)

GPIO.setup(pin_4, GPIO.IN, pull_up_down=GPIO.PUD_UP) # payload release button
# GPIO.setup(pin_17, GPIO.OUT)
# GPIO.output(pin_17, GPIO.LOW)

GPIO.setup(pin_18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(pin_21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(pin_20, GPIO.OUT)
# GPIO.output(pin_20, GPIO.LOW)

GPIO.setup(pin_16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(pin_12, GPIO.OUT)
# GPIO.output(pin_12, GPIO.LOW)

GPIO.setup(pin_7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_8, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(pin_25, GPIO.OUT)
GPIO.output(pin_25, GPIO.LOW)

GPIO.setup(pin_24, GPIO.OUT)
GPIO.output(pin_24, GPIO.LOW)


###########################################################################

# Helper function to flash an LED given its current state
def flash_led(pin_number):
    for i in range(3):
        GPIO.output(pin_number, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(pin_number, GPIO.LOW)
        time.sleep(0.3)

# Helper variable to ensure not infinitely calling the function when we switch to enable it
telemetry_func_called = False

# Simulation enable handling variable
simulation_enabled = False

# Simulation active handling variable
sim_activated = False

# Simulation disable handling variable
sim_disabled = False

graph_proc = None
prev_state_18 = GPIO.HIGH

def _cleanup_and_exit(signum, frame):
    GPIO.cleanup()
    sys.exit(0)

signal.signal(signal.SIGTERM, _cleanup_and_exit)
signal.signal(signal.SIGINT, _cleanup_and_exit)

###########################################################################


try:

    while True:

        

        state_14 = GPIO.input(pin_14) # activate simulation toggle (to CanSat)
        state_15 = GPIO.input(pin_15) # deactivate simulation toggle (to CanSat)

        state_9 = GPIO.input(pin_9) # simulation enable button

        state_11 = GPIO.input(pin_11) # set coordinates button

        state_5 = GPIO.input(pin_5) # Release egg button

        state_13 = GPIO.input(pin_13) # set time UTC button

        state_26 = GPIO.input(pin_26) # set time GPS button

        state_27 = GPIO.input(pin_27) # paraglider release button

        state_4 = GPIO.input(pin_4)   # payload release button

        state_18 = GPIO.input(pin_18) # show graphs
        prev = prev_state_18

        state_21 = GPIO.input(pin_21) # reset state
        
        state_16 = GPIO.input(pin_16) # calibrate altitude
        state_7 = GPIO.input(pin_7)    # toggle to telemetry Enable
        state_8 = GPIO.input(pin_8)    # toggle to telemetry Disable


        if state_9 == GPIO.LOW and simulation_enabled == False:
            print("Simulation Enabled")
            simulation_enabled = True
            GPIO.output(pin_10, GPIO.LOW)
            print("Pin 10 LED ON to indicate simulation enabled")
            GPIO.output(pin_23, GPIO.HIGH) 

        if state_14 == GPIO.LOW and sim_activated == False and sim_disabled == False:
            print("Simulation Activated")
            print("Send activation signal to CanSat...")
            GPIO.output(pin_23, GPIO.LOW)
            GPIO.output(pin_1, GPIO.HIGH)
            sim_disabled = True
            simulation_enabled = False
        
        if state_15 == GPIO.LOW and simulation_enabled == False and sim_disabled == True:
            print("Simulation Deactivated")
            print("Send deactivation xbee signal to CanSat...")
            GPIO.output(pin_1, GPIO.LOW)
            GPIO.output(pin_10, GPIO.HIGH)
            sim_disabled = False
            sim_activated = False
            simulation_enabled = False


        if state_11 == GPIO.LOW : 
            print("Set coordinates button pressed")
            print("Pin 11 button pressed, do work...")
        

        if state_5 == GPIO.LOW :
            print("Release egg button pressed")
            print("Pin 5 button pressed, do work...")
            flash_led(pin_19)
            print("Pin 19 flashes status LED to show sending xbee packet")

        if state_13 == GPIO.LOW :
            print("Set UTC time button pressed")
            print("Pin 13 button pressed, do work...")
            flash_led(pin_19)
            print("Pin 19 flashes status LED to show sending xbee packet")

        if state_26 == GPIO.LOW :
            print("Set GPS time button pressed")
            print("Pin 26 button pressed, do work...")
            flash_led(pin_19)
            print("Pin 19 flashes status LED to show sending xbee packet")

        if state_27 == GPIO.LOW :
            print("Paraglider release button pressed")
            print("Pin 27 button pressed, do work...")
            flash_led(pin_19)
            print("Pin 19 flashes status LED to show sending xbee packet")

        if state_4 == GPIO.LOW :
            print("Payload release button pressed")
            print("Pin 4 button pressed, do work...")
            flash_led(pin_19)
            print("Pin 19 flashes status LED to show sending xbee packet")


        if state_16 == GPIO.LOW :
            print("Button pressed")
            print("Pin 16 active, do work:") 
            print("For example: calibrate altitude")
            # call some other functions  that do the work
            flash_led(pin_19)
            print("Pin 19 flashes status LED to show sending xbee packet")

        if state_7 == GPIO.LOW and telemetry_func_called == False:
            print("Telemetry enabled")
            print("Call telemetry enabling function to do work...")
            telemetry_func_called = True
            GPIO.output(pin_24, GPIO.LOW)
            GPIO.output(pin_25, GPIO.HIGH)
        
        if state_8 == GPIO.LOW and telemetry_func_called == True:

            print("Telemetry Disabled")
            print("Disable or interrupt or stop the execution of the telemetry handling function...")
            telemetry_func_called = False
            GPIO.output(pin_25, GPIO.LOW)
            GPIO.output(pin_24, GPIO.HIGH)

        if state_21 == GPIO.LOW :
            print("Pin 21 button pressed, call reset state function")
            flash_led(pin_19)
            print("Pin 19 flashes to show sending xbee packet ")


        if state_18 == GPIO.LOW and prev == GPIO.HIGH:
            print("Pin 18 button pressed, show graphs")
            if graph_proc is None or graph_proc.poll() is not None:
                graph_proc = subprocess.Popen(['python3','/home/jonathan/UCI-CanSat-25-26/Ground-Station/mini_map_test.py'])
                time.sleep(0.2)
        prev_state_18 = state_18

        time.sleep(0.1) # global delay and debouncing adjustment
    
except KeyboardInterrupt:
    print("Exiting program")

finally:
    GPIO.cleanup()