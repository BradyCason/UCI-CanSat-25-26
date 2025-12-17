import RPi.GPIO as GPIO
import time
import subprocess


pin_18 = 18 # show graphs

pin_21 = 21 # example: press to reset state
pin_20 = 20 # flash led to indicate reseting state packet sending

pin_16 = 16 # example: calibrate altitude button
pin_12 = 12 # example: LED indicator for calibrate altitue button

# example toggle switch application:
pin_7 = 7 # example: telemetry toggle on
pin_8 = 8 # example: telemetry toggle off
pin_25 = 25 # example: green led on while telemetry toggled on 
pin_24 = 24 # example: red led on while telemetry toggled off

GPIO.setmode(GPIO.BCM)

GPIO.setup(pin_18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(pin_21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_20, GPIO.OUT)
GPIO.output(pin_20, GPIO.LOW)

GPIO.setup(pin_16, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_12, GPIO.OUT)
GPIO.output(pin_12, GPIO.LOW)

GPIO.setup(pin_7, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_8, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_25, GPIO.OUT)
GPIO.setup(pin_24, GPIO.OUT)
GPIO.output(pin_25, GPIO.LOW)
GPIO.output(pin_24, GPIO.LOW)


# Helper function to flash an LED given its current state
def flash_led(pin_number):
    for i in range(3):
        GPIO.output(pin_number, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(pin_number, GPIO.LOW)
        time.sleep(0.3)

# Helper variable to ensure not infinitely calling the function when we switch to enable it
telemetry_func_called = False

try:

    while True:

        state_18 = GPIO.input(pin_18) # show graphs

        state_21 = GPIO.input(pin_21) # reset state
        
        state_16 = GPIO.input(pin_16) # calibrate altitude
        state_7 = GPIO.input(pin_7)    # toggle to telemetry Enable
        state_8 = GPIO.input(pin_8)    # toggle to telemetry Disable


        if state_16 == GPIO.LOW :
            print("Button pressed")
            print("Pin 16 active, do work:") 
            print("For example: calibrate altitude")
            # call some other functions  that do the work
            flash_led(pin_12)
            print("Pin 12 flashes status LED to show sending xbee packet")

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
            flash_led(pin_20)
            print("Pin 20 flashes to show sending xbee packet ")


        if state_18 == GPIO.LOW :
            print("Pin 18 button pressed, show graphs")
            subprocess.Popen(['python3','/home/brcason/UCI-CanSat-25-26/Ground-Station/mini_map_test.py'])
            time.sleep(0.1)

        time.sleep(0.1) # global delay and debouncing adjustment
    
except KeyboardInterrupt:
    print("Exiting program")

finally:
    GPIO.cleanup()