import RPi.GPIO as GPIO
import time

pin_21 = 21
pin_20 = 20

GPIO.setmode(GPIO.BCM)

GPIO.setup(pin_21, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(pin_20, GPIO.OUT)
GPIO.output(pin_20, GPIO.LOW)

# Helper function to flash an LED given its current state
def flash_led(pin_number):
    for i in range(3):
        GPIO.output(pin_number, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(pin_number, GPIO.LOW)
        time.sleep(0.3)

try:


    while True:
        state_21 = GPIO.input(pin_21)

        if state_21 == GPIO.LOW :
            print("Button pressed")
            print("Pin 21 active, call reset state function")
            flash_led(pin_20)

        
        time.sleep(0.2)
    
except KeyboardInterrupt:
    print("Exiting program")

finally:
    GPIO.cleanup()