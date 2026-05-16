import sys
import os
import time
import serial
import threading
from PyQt5 import QtCore, QtGui, QtWidgets, uic
import pyqtgraph as pg
from csv import writer, reader
from datetime import datetime
import pytz
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import random

import RPi.GPIO as GPIO
import time
import subprocess
import signal, sys

# top figure
reset_button_pin = 8
cal_alt_button_pin = 10
set_coords_button_pin = 12
set_time_button_pin = 16
set_time_switch_pin = 18
# usb: keypad

# middle figure
state_servo_pin = 33
received_led_pin = 3
sending_led_pin = 7
container_release_switch_pin = 22
container_released_led_pin = 19
eject_paraglider_switch_pin = 24
eject_paraglider_led_pin = 21
paraglider_active_switch_pin = 26
paraglider_active_led_pin = 23
payload_release_switch_pin = 28
payload_release_led_pin = 27

# bottom figure
sim_enable_switch_pin = 11
sim_activate_button_pin = 13
telemetry_toggle_switch_pin = 15

GPIO.setmode(GPIO.BCM)
BUTTON_PINS = [reset_button_pin, cal_alt_button_pin, set_coords_button_pin, set_time_button_pin, sim_activate_button_pin]
SWITCH_PINS = [set_time_switch_pin, container_release_switch_pin, eject_paraglider_switch_pin, paraglider_active_switch_pin,
              payload_release_switch_pin, sim_enable_switch_pin, telemetry_toggle_switch_pin]
# Set input pins to internal pull ups
for p in BUTTON_PINS + SWITCH_PINS:
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
LED_PINS = [received_led_pin, sending_led_pin, container_released_led_pin, eject_paraglider_led_pin,
            paraglider_active_led_pin, payload_release_led_pin]
# Initialize LEDS
for p in LED_PINS:
    GPIO.setup(p, GPIO.OUT)
    GPIO.output(received_led_pin, GPIO.LOW)
# Initialize servo pin
GPIO.setup(state_servo_pin, GPIO.out)
pwm=GPIO.PWM(state_servo_pin, 50)
pwm.start(0)

# --------------------------------------------------

# Worker thread: poll GPIO and emit Qt signals on falling edge
class ControlsThread(QtCore.QThread):
    telemetry_toggle = QtCore.pyqtSignal()
    sim_enable = QtCore.pyqtSignal()
    sim_activate = QtCore.pyqtSignal()
    sim_disable = QtCore.pyqtSignal()
    set_coords = QtCore.pyqtSignal()
    set_time_utc = QtCore.pyqtSignal()
    set_time_gps = QtCore.pyqtSignal()
    calibrate_alt = QtCore.pyqtSignal()
    release_payload = QtCore.pyqtSignal()
    release_paraglider = QtCore.pyqtSignal()
    reset_state = QtCore.pyqtSignal()
    release_container = QtCore.pyqtSignal()
    show_graphs = QtCore.pyqtSignal()

    def __init__(self, control_window, poll_interval=0.05, parent=None):
        super().__init__(parent)
        self.control_window = control_window
        self._running = True
        self.poll_interval = poll_interval
        # track previous states to detect edges (buttons are pull-up; pressed -> LOW)
        self.prev_switch_state = {p: GPIO.input(p) for p in SWITCH_PINS}
        self.graph_proc = None  # Track graph process for toggle functionality
        self.time_mode = 0  # 0 -> GPS, 1 -> UTC

    def activate_sim(self):
        global sim, sim_enable, csv_indexer
        if sim_enable == True:
            write_xbee("CMD," + TEAM_ID + ",SIM,ACTIVATE")
            sim_enable = False
            sim = True
            csv_indexer = 0

    def enable_sim(self):
        global sim, sim_enable, csv_indexer
        if sim_enable == False:
            write_xbee("CMD," + TEAM_ID + ",SIM,ENABLE")
            sim_enable = True

    def disable_sim(self):
        global sim, sim_enable, csv_indexer
        if sim_enable == True:
            write_xbee("CMD," + TEAM_ID + ",SIM,DISABLE")
            sim_enable = False

    def set_coords(self):
        # TODO: implement set coords function
        pass

        # Old code:
        # dialog = CoordinatesDiaglog()
        # result = dialog.exec_()

        # if result == QtWidgets.QDialog.Accepted:
        #     num1, num2 = dialog.get_values()
        #     write_xbee("CMD," + TEAM_ID + ",SC,{:.6f},{:.6f}".format(num1, num2))
        # else:
        #     QtWidgets.QMessageBox.information(self, "Cancelled", "You pressed Cancel!")

    def update(self):
        self.update_leds()
        self.update_state_servo()

    def update_leds(self):
        global container_released
        if container_released:
            GPIO.output(container_released_led_pin, GPIO.HIGH)
        else:
            GPIO.output(container_released_led_pin, GPIO.LOW)

        global paraglider_active
        if paraglider_active:
            GPIO.output(paraglider_active_led_pin, GPIO.HIGH)
        else:
            GPIO.output(paraglider_active_led_pin, GPIO.LOW)

        global paraglider_ejected
        if paraglider_ejected:
            GPIO.output(eject_paraglider_led_pin, GPIO.HIGH)
        else:
            GPIO.output(eject_paraglider_led_pin, GPIO.LOW)

        global payload_released
        if payload_released:
            GPIO.output(payload_release_led_pin, GPIO.HIGH)
        else:
            GPIO.output(payload_release_led_pin, GPIO.LOW)

    def set_state_servo_angle(angle):
        """
        Set servo angle from 0 to 180 degrees
        """
        duty = 2.5 + (angle / 180.0) * 10.0
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.3)

        # Stop sending signal to reduce jitter
        pwm.ChangeDutyCycle(0)

    def update_state_servo(self):
        global state
        if state == "LAUNCH_PAD":
            self.set_state_servo_angle(0)
        elif state == "ASCENT":
            self.set_state_servo_angle(30)
        elif state == "APOGEE":
            self.set_state_servo_angle(60)
        elif state == "DESCENT":
            self.set_state_servo_angle(90)
        elif state == "PROBE_RELEASE":
            self.set_state_servo_angle(120)
        elif state == "PAYLOAD_RELEASE":
            self.set_state_servo_angle(150)
        elif state == "LANDED":
            self.set_state_servo_angle(180)

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            # Handle button presses
            for p in BUTTON_PINS:
                if GPIO.input(p) == GPIO.LOW:
                    # Button pressed
                    time.sleep(0.05) # debounce
                    
                    # Wait until button is released
                    while GPIO.input(p) == GPIO.LOW:
                        pass

                    # Perform Action
                    if p == sim_activate_button_pin:
                        self.activate_sim()
                    else:
                        # disable simulation whenever another button is pressed
                        self.disable_sim()

                    if p == reset_button_pin:
                        global packet_count
                        packet_count = 0
                        self.control_window.reset_graphs()
                        write_xbee("CMD," + TEAM_ID + ",RST")
                    elif p == cal_alt_button_pin:
                        write_xbee("CMD," + TEAM_ID + ",CAL")
                    elif p == set_coords_button_pin:
                        # Enter set coords function
                        self.set_coords()
                    elif p == set_time_button_pin:
                        if self.time_mode == 0:
                            write_xbee("CMD," + TEAM_ID + ",ST,GPS")
                        else :
                            write_xbee("CMD," + TEAM_ID + ",ST," + datetime.now(pytz.timezone("UTC")).strftime("%H:%M:%S"))

            # Handle necessary switches
            for p in SWITCH_PINS:
                cur = GPIO.input(p)
                if cur != self.prev_switch_state[p]:
                    # switch was changed
                    self.prev_switch_state[p] = cur

                    time.sleep(0.05) # debounce

                    # Handle simulation mode
                    if p == sim_enable_switch_pin and cur == GPIO.HIGH:
                        self.enable_sim()
                    else:
                        self.disable_sim()
                    

                    # Perform Action
                    if p == container_release_switch_pin:
                        if cur == GPIO.HIGH:
                            write_xbee("CMD," + TEAM_ID + ",MEC,CONTAINER,ON")
                        else:
                            write_xbee("CMD," + TEAM_ID + ",MEC,CONTAINER,OFF")
                    elif p == eject_paraglider_switch_pin:
                        if cur == GPIO.HIGH:
                            write_xbee("CMD," + TEAM_ID + ",MEC,EJECT")
                    elif p == paraglider_active_switch_pin:
                        if cur == GPIO.HIGH:
                            write_xbee("CMD," + TEAM_ID + ",MEC,GLIDER,ON")
                        else:
                            write_xbee("CMD," + TEAM_ID + ",MEC,GLIDER,OFF")
                    elif p == payload_release_switch_pin:
                        if cur == GPIO.HIGH:
                            write_xbee("CMD," + TEAM_ID + ",MEC,PAYLOAD,ON")
                        else:
                            write_xbee("CMD," + TEAM_ID + ",MEC,PAYLOAD,OFF")
                    elif p == set_time_switch_pin:
                        if cur == GPIO.HIGH:
                            self.time_mode = 1
                        else:
                            self.time_mode = 0
                    elif p == telemetry_toggle_switch_pin:
                        global telemetry_on
                        if cur == GPIO.HIGH:
                            telemetry_on = True
                            write_xbee("CMD,"+ TEAM_ID + ",CX,ON")
                        else:
                            telemetry_on = False
                            write_xbee("CMD,"+ TEAM_ID + ",CX,OFF")
                                   
            time.sleep(self.poll_interval)

# Old code. Jonny, do we need this?
# Toggle graph process: close if running, open if not
# if self.graph_proc and self.graph_proc.poll() is None:
#     self.graph_proc.terminate()
#     self.graph_proc = None
# else:
#     self.graph_proc = subprocess.Popen(['python3','/home/jonathan/UCI-CanSat-25-26/Ground-Station/mini_map_test.py'])

# Helper function to flash the XBee LED without blocking the polling thread
def flash_led(LED_pin, flashes=3, on_time=0.2, off_time=0.2):
    """
    Flash the given LED pin `flashes` times on a daemon thread so the
    ControlsThread isn't blocked by sleep calls.
    """
    def _worker():
        try:
            for _ in range(flashes):
                GPIO.output(LED_pin, GPIO.HIGH)
                time.sleep(on_time)
                GPIO.output(LED_pin, GPIO.LOW)
                time.sleep(off_time)
        except Exception:
            pass    
    threading.Thread(target=_worker, daemon=True).start()


TEAM_ID = "1083"

TELEMETRY_FIELDS = ["TEAM_ID", "MISSION_TIME", "PACKET_COUNT", "MODE", "STATE", "ALTITUDE",
                    "TEMPERATURE", "PRESSURE", "VOLTAGE", "CURRENT", "GYRO_R", "GYRO_P", "GYRO_Y", "ACCEL_R",
                    "ACCEL_P", "ACCEL_Y", "HEADING", "GPS_TIME", "GPS_ALTITUDE",
                    "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_SATS","CMD_ECHO", "MAX_ALTITUDE",
                    "CONTAINER_RELEASED", "PAYLOAD_RELEASED", "PARAGLIDER_EJECTED", "PARAGLIDER_ACTIVE", "TARGET_LATITUDE",
                    "TARGET_LONGITUDE"]

current_time = time.time()
local_time = time.localtime(current_time)
readable_time = time.strftime("telemetry_%Y-%m-%d_%H-%M-%S", local_time)

sim = False
sim_enable = False
telemetry_on = True
csv_indexer = 0

packet_count = 0
packets_sent = 0

# xbee communication parameters
BAUDRATE = 115200
COM_PORT = "/dev/ttyUSB0"    # USB0 on raspberry pi

# MAKE_CSV_FILE = False
MAKE_CSV_FILE = True # Set to True to create a CSV log file of telemetry data, must be set before running the program to work
SER_DEBUG = False       # Set as True whenever testing without XBee connected

START_DELIMITER = "~"

ser = None
serialConnected = False

""" The following serial function is used when raspberry pi or linux machine is used for GS and is set to COM_PORT = "/dev/ttyUSB0" """ 
def connect_Serial():
    global ser
    global serialConnected
    if (not SER_DEBUG):
        try:
            ser = serial.Serial(COM_PORT, BAUDRATE, timeout=0.05)
            serialConnected = True
            print("Connected to Xbee")
        except serial.serialutil.SerialException as e:
            if (serialConnected):
                print(f"Could not connect to Xbee: {e}")
            serialConnected = False

def disconnect_Serial():
    global ser
    global serialConnected
    if (not SER_DEBUG):
        try:
            if serialConnected and ser.is_open:
                ser.close()
                print("Disconnected from Xbee")
            serialConnected = False
        except Exception as e:
            print(f"Error while disconnecting Xbee: {e}")
            serialConnected = False

# telemetry
# strings as keys and values as values, only last stored
# need to write all commands to csv files by last filled values
telemetry = {}
payload_released = False
paraglider_active = False
container_released = False
paraglider_ejected = False
state = "LAUNCH_PAD"

class GroundStationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        '''
        Initialize the Ground Station Window, and start timer loop for updating UI
        '''
        super().__init__()

        # Load the UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui", "ground_station.ui") # previous GS ui_path 
        # ui_path = os.path.join(os.path.dirname(__file__), "new-gui", "testing.ui") # new GS ui_path
        uic.loadUi(ui_path, self)

        # Apply 90 degree rotation to the entire UI
        # self.rotate_ui(90)

        self.showFullScreen()           

        self.setup_UI()
        self.connect_buttons()

        self.init_graphs()

    def rotate_ui(self, degrees):
        '''
        Rotate the entire UI by the specified degrees (90, 180, 270)
        using graphics scene approach from rotated_ui.py
        '''
        # Create graphics view and scene
        graphics_view = QtWidgets.QGraphicsView()
        graphics_view.setStyleSheet("border: none; background-color: white;")
        graphics_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        
        scene = QtWidgets.QGraphicsScene()
        graphics_view.setScene(scene)
        
        # Get the actual central widget that was set by uic.loadUi()
        actual_central = self.centralWidget()
        
        # Temporarily remove the central widget from main window
        self.takeCentralWidget()
        
        # Add it to the graphics scene
        proxy = scene.addWidget(actual_central)
        
        # Apply rotation to the proxy
        transform = QtGui.QTransform().rotate(degrees)
        proxy.setTransform(transform)
        
        # Adjust scene rect to fit the content
        scene.setSceneRect(scene.itemsBoundingRect())
        
        # Make graphics view expand to fill available space
        graphics_view.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        graphics_view.setMinimumSize(1, 1)
        
        # Set graphics view as the new central widget
        self.setCentralWidget(graphics_view)

    def setup_UI(self):
        '''
        Set UI to initial State
        '''
        logo_pixmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "gui", "logo.png")).scaled(self.logo.size(), aspectRatioMode=True)
        self.logo.setPixmap(logo_pixmap)
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "gui", "logo.png")))
        self.title.setText("CanSat Ground Station - TEAM " + TEAM_ID)

        # Get telemetry labels
        self.telemetry_labels = {}
        for field in TELEMETRY_FIELDS:
            label = self.telemetry_container_1.findChild(QtWidgets.QLabel, field)
            if (not label):
                label = self.telemetry_container_2.findChild(QtWidgets.QLabel, field)
                if (not label):
                    label = self.telemetry_container_3.findChild(QtWidgets.QLabel, field)
            self.telemetry_labels[field] = label

    def update(self):
        '''
        Set telemetry fields to most recent data
        '''
        global telemetry
        global telemetry_on

        for field in TELEMETRY_FIELDS:
            if field != "TEAM_ID":
                self.telemetry_labels[field].setText(telemetry[field])

        self.update_graphs()

    def init_graphs(self):
        self.x_data = []
        self.counter = 0

        self.altitude_figure = Figure()
        self.altitude_canvas = FigureCanvas(self.altitude_figure)
        self.altitude_graph.layout().addWidget(self.altitude_canvas)
        self.alt_subplot = self.altitude_figure.add_subplot(111)
        self.altitude_y_data = []

        self.accel_figure = Figure()
        self.accel_canvas = FigureCanvas(self.accel_figure)
        self.acceleration_graph.layout().addWidget(self.accel_canvas)
        self.accel_subplot = self.accel_figure.add_subplot(111)
        self.accel_r_y_data = []
        self.accel_p_y_data = []
        self.accel_y_y_data = []

        self.rotation_figure = Figure()
        self.rotation_canvas = FigureCanvas(self.rotation_figure)
        self.rotation_graph.layout().addWidget(self.rotation_canvas)
        self.rotation_subplot = self.rotation_figure.add_subplot(111)
        self.rotation_r_y_data = []
        self.rotation_p_y_data = []
        self.rotation_y_y_data = []

        self.current_figure = Figure()
        self.current_canvas = FigureCanvas(self.current_figure)
        self.current_graph.layout().addWidget(self.current_canvas)
        self.current_subplot = self.current_figure.add_subplot(111)
        self.current_y_data = []

        self.voltage_figure = Figure()
        self.voltage_canvas = FigureCanvas(self.voltage_figure)
        self.voltage_graph.layout().addWidget(self.voltage_canvas)
        self.voltage_subplot = self.voltage_figure.add_subplot(111)
        self.voltage_y_data = []

        self.timer = QtCore.QTimer()
        self.timer.setInterval(150)  # 150 ms update    # Could increase interval for less Pi resource usage, but would make graphs less smooth
        self.timer.timeout.connect(self.update_graphs)
        self.timer.start()

        self.alt_line, = self.alt_subplot.plot([], [], color="blue")
        self.alt_subplot.set_title("Altitude (m)")

        self.accel_r_line, = self.accel_subplot.plot([], [], label="R", color="blue")
        self.accel_p_line, = self.accel_subplot.plot([], [], label="P", color="orange")
        self.accel_y_line, = self.accel_subplot.plot([], [], label="Y", color="green")
        self.accel_subplot.set_title("Acceleration (°/s^2)")
        self.accel_subplot.legend()

        self.rotation_r_line, = self.rotation_subplot.plot([], [], label="R", color="blue")
        self.rotation_p_line, = self.rotation_subplot.plot([], [], label="P", color="orange")
        self.rotation_y_line, = self.rotation_subplot.plot([], [], label="Y", color="green")
        self.rotation_subplot.set_title("Rotation Rate (°/s)")
        self.rotation_subplot.legend()

        self.current_line, = self.current_subplot.plot([], [], label="Current", color="blue")
        self.current_subplot.set_title("Current (A)")
        self.current_subplot.legend()

        self.voltage_line, = self.voltage_subplot.plot([], [], label="Voltage", color="blue")
        self.voltage_subplot.set_title("Voltage (V)")
        self.voltage_subplot.legend()

    def update_graphs(self):
        # Skip update if no telemetry data yet
        if not telemetry or "PACKET_COUNT" not in telemetry:
            return

        # Helper function to safely convert to float, return 0 if empty
        def safe_float(value):
            try:
                if value == "" or value is None:
                    return 0.0
                return float(value)
            except (ValueError, TypeError):
                print(f"Warning: Could not convert '{value}' to float, using 0.0")
                return 0.0

        # Update data with error handling
        try:
            self.x_data.append(int(telemetry["PACKET_COUNT"]))
            self.altitude_y_data.append(safe_float(telemetry["ALTITUDE"]))
            self.accel_r_y_data.append(safe_float(telemetry["ACCEL_R"]))
            self.accel_p_y_data.append(safe_float(telemetry["ACCEL_P"]))
            self.accel_y_y_data.append(safe_float(telemetry["ACCEL_Y"]))
            self.rotation_r_y_data.append(safe_float(telemetry["GYRO_R"]))
            self.rotation_p_y_data.append(safe_float(telemetry["GYRO_P"]))
            self.rotation_y_y_data.append(safe_float(telemetry["GYRO_Y"]))
            self.current_y_data.append(safe_float(telemetry["CURRENT"]))
            self.voltage_y_data.append(safe_float(telemetry["VOLTAGE"]))
        except (KeyError, ValueError, TypeError) as e:
            print(f"Warning: Skipping update_graphs due to: {e}")
            return

        # self.x_data.append(self.counter)
        # self.altitude_y_data.append(random.randint(0,10))
        # self.accel_r_y_data.append(random.randint(0,10))
        # self.accel_p_y_data.append(random.randint(0,10))
        # self.accel_y_y_data.append(random.randint(0,10))
        # self.rotation_r_y_data.append(random.randint(0,10))
        # self.rotation_p_y_data.append(random.randint(0,10))
        # self.rotation_y_y_data.append(random.randint(0,10))
        # self.current_y_data.append(random.randint(0,10))
        # self.voltage_y_data.append(random.randint(0,10))
        # self.counter += 1

        # Only plot last 25 points
        if len(self.x_data) > 25:
            self.x_data.pop(0)
            self.altitude_y_data.pop(0)
            self.accel_r_y_data.pop(0)
            self.accel_p_y_data.pop(0)
            self.accel_y_y_data.pop(0)
            self.rotation_r_y_data.pop(0)
            self.rotation_p_y_data.pop(0)
            self.rotation_y_y_data.pop(0)
            self.current_y_data.pop(0)
            self.voltage_y_data.pop(0)

        # Use set_data for faster plotting instead of clear() and plot() 
        self.alt_line.set_data(self.x_data, self.altitude_y_data)
        self.alt_subplot.relim()
        self.alt_subplot.autoscale_view()
        self.altitude_canvas.draw_idle() # Use draw_idle() for better performance over draw()

        self.accel_r_line.set_data(self.x_data, self.accel_r_y_data)
        self.accel_p_line.set_data(self.x_data, self.accel_p_y_data)
        self.accel_y_line.set_data(self.x_data, self.accel_y_y_data)
        self.accel_subplot.relim()
        self.accel_subplot.autoscale_view()
        self.accel_canvas.draw_idle()

        self.rotation_r_line.set_data(self.x_data, self.rotation_r_y_data)
        self.rotation_p_line.set_data(self.x_data, self.rotation_p_y_data)
        self.rotation_y_line.set_data(self.x_data, self.rotation_y_y_data)
        self.rotation_subplot.relim()
        self.rotation_subplot.autoscale_view()
        self.rotation_canvas.draw_idle()

        self.current_line.set_data(self.x_data, self.current_y_data)
        self.current_subplot.relim()
        self.current_subplot.autoscale_view()
        self.current_canvas.draw_idle()

        self.voltage_line.set_data(self.x_data, self.voltage_y_data)
        self.voltage_subplot.relim()
        self.voltage_subplot.autoscale_view()
        self.voltage_canvas.draw_idle()

    def reset_graphs(self):
        self.x_data = []
        self.altitude_y_data = []
        self.accel_r_y_data = []
        self.accel_p_y_data = []
        self.accel_y_y_data = []
        self.rotation_r_y_data = []
        self.rotation_p_y_data = []
        self.rotation_y_y_data = []
        self.current_y_data = []
        self.voltage_y_data = []


class CoordinatesDiaglog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Two Numbers")

        layout = QtWidgets.QFormLayout()

        # First number
        self.num1 = QtWidgets.QDoubleSpinBox()
        self.num1.setDecimals(6)       # allow up to 6 decimal places
        self.num1.setRange(-1e6, 1e6)  # set a large range
        self.num1.setSingleStep(0.0001) # step size
        self.num1.clear()
        layout.addRow("Target Latitude:", self.num1)

        # Second number
        self.num2 = QtWidgets.QDoubleSpinBox()
        self.num2.setDecimals(6)
        self.num2.setRange(-1e6, 1e6)
        self.num2.setSingleStep(0.0001)
        self.num2.clear()
        layout.addRow("Target Longitude:", self.num2)

        # OK / Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self):
        return self.num1.value(), self.num2.value()

def calc_checksum(data):
    '''
    Calculate Checksum based off of packet data
    '''
    return sum(data.encode()) % 256

def verify_checksum(data, checksum):
    '''
    Return a boolean of if the checksum is correct
    '''
    return checksum == calc_checksum(data)

def parse_xbee(data):
    '''
    Parse the data from an incoming Xbee packet
    '''
    global sim, telemetry, packet_count, w, controls #, last_recieved_packet

    # Validate frame has correct number of fields (only check field count, allow empty values)
    if len(data) != len(TELEMETRY_FIELDS):
        print(f"Incomplete frame: expected {len(TELEMETRY_FIELDS)} fields, got {len(data)}")
        return

    # Ensure only recieving each packet once
    # sent_packet_count = int(data[TELEMETRY_FIELDS.index("PACKET_COUNT")])
    # if sent_packet_count == last_recieved_packet:
    #     return
    # last_recieved_packet = sent_packet_count

    packet_count += 1
    telemetry["PACKET_COUNT"] = str(packet_count)

    for i in range(len(data)):
        if TELEMETRY_FIELDS[i] != "PACKET_COUNT":
            telemetry[TELEMETRY_FIELDS[i]] = data[i]

    global payload_released
    if telemetry["PAYLOAD_RELEASED"] == "TRUE":
        payload_released = True
    else:
        payload_released = False

    global paraglider_active
    if telemetry["PARAGLIDER_ACTIVE"] == "TRUE":
        paraglider_active = True
    else:
        paraglider_active = False

    global container_released
    if telemetry["CONTAINER_RELEASED"] == "TRUE":
        container_released = True
    else:
        container_released = False

    global paraglider_ejected
    if telemetry["PARAGLIDER_EJECTED"] == "TRUE":
        paraglider_ejected = True
    else:
        paraglider_ejected = False

    global state
    state = telemetry["STATE"]

    # if data[3] == "S":
    #     sim = True
    # else:
    #     sim = False

    # Add data to csv file
    if MAKE_CSV_FILE:
        file = os.path.join(os.path.dirname(__file__), "Flight_" + TEAM_ID + "_" + readable_time +'.csv')
        with open(file, 'a', newline='') as f_object:
            writer_object = writer(f_object)
            writer_object.writerow(list(telemetry.values()) + [data[-1]])

    w.update()
    controls.update()


def read_xbee():
    '''
    Read packets from the Xbee module
    '''
    buffer = ""
    global serialConnected
    while True:     # Keep running as long as the serial connection is open
        if not serialConnected:
            connect_Serial()
            time.sleep(0.1)
            continue

        try:
            if ser.inWaiting() > 0:
                buffer += ser.read(ser.inWaiting()).decode(errors='replace')

                start_idx = buffer.find(START_DELIMITER)
                end_idx = buffer.find("\n", start_idx)
                next_start = buffer.find(START_DELIMITER, start_idx + 1)

                if next_start != -1 and (end_idx == -1 or next_start < end_idx):
                    frame_end = next_start
                elif end_idx != -1:
                    frame_end = end_idx
                else:
                    # Wait for a full packet
                    continue

                frame = buffer[start_idx + 1:frame_end].strip()
                buffer = buffer[frame_end + 1:]

                try:
                    data, checksum = frame.rsplit(",", 1)
                    if verify_checksum(data, float(checksum)):

                        split_data = data.split(",")
                        if len(split_data) == len(TELEMETRY_FIELDS):
                            flash_led(received_led_pin)
                            parse_xbee(split_data)
                        else:
                            print("Incorrect number of fields in frame: ", frame)
                    else:
                        print("Failed to read frame:", frame)
                except Exception as e:
                    print(e)
                    print("Error reading frame: ", frame)

                # start_byte = ser.read(1)
                # if start_byte != START_DELIMITER:
                #     print(start_byte.decode())

                # if start_byte == START_DELIMITER:
                #     time.sleep(0.1)
                #     frame = ser.read_until(b"\n").decode().strip()
                #     try:
                #         data, checksum = frame.rsplit(",", 1)
                #         if verify_checksum(data, float(checksum)):
                #             parse_xbee(data.split(","))
                #         else:
                #             print("Failed to read frame:", frame)
                #     except:
                #         print("Failed to read frame:", frame)

            serialConnected = True
        except serial.serialutil.SerialException as e:
            if serialConnected:
                print(f"Connection Lost: {e}")
            serialConnected = False
        except OSError as e:
            if (serialConnected):
                print(f"Connection Lost: {e}")
            serialConnected = False

        time.sleep(0.1)
            

def write_xbee(cmd):
    '''
    Write commands to the Xbee
    '''
    # Frame Format: ~<data>,<checksum>

    flash_led(sending_led_pin)

    # Create Packet
    global packets_sent
    packets_sent += 1
    checksum = calc_checksum(f"{cmd}")
    frame = f"{START_DELIMITER}{cmd},{checksum:02X}"

    # Send to XBee
    if (not SER_DEBUG):
        try:
            if (ser):
                ser.write(frame.encode())
                print(f"Packet Sent: {cmd}")
        except serial.serialutil.SerialException as e:
            print(f"Packet Not Sent: {e}")

def send_simp_data():
    '''
    Send simulated pressure data from the csv file at 1 Hz
    '''
    global sim
    global csv_indexer
    csv_file = open(os.path.join(os.path.dirname(__file__), "pres.csv"), 'r')
    csv_lines = csv_file.readlines()
    csv_indexer = 0
    while True:
        if sim and csv_indexer < len(csv_lines):
            csv_num = str(csv_lines[csv_indexer].strip())
            write_xbee('CMD,' + TEAM_ID + ',SIMP,' + str(csv_num))
            csv_indexer += 1
            
        time.sleep(1)


def main():
    connect_Serial()

    # Create new csv file with header
    if MAKE_CSV_FILE:
        file = os.path.join(os.path.dirname(__file__), "Flight_" + TEAM_ID + "_" + readable_time + '.csv')
        with open(file, 'w', newline='') as f_object:
            writer_object = writer(f_object)
            writer_object.writerow(TELEMETRY_FIELDS + ["CAM_DIRECTION"])

    # Run the app
    app = QtWidgets.QApplication(sys.argv)
    global w
    w = GroundStationWindow()
    
    if (not SER_DEBUG):
        threading.Thread(target=read_xbee, daemon=True).start()
    threading.Thread(target=send_simp_data, daemon=True).start()

    # Start GPIO controls thread and connect signals to safe GUI actions
    global controls
    controls = ControlsThread(w)
    controls.telemetry_toggle.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.telemetry_toggle_button.click()))
    controls.sim_enable.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.sim_enable_button.click()))
    controls.sim_activate.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.sim_activate_button.click()))
    controls.sim_disable.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.sim_disable_button.click()))
    controls.set_coords.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.set_coordinates_button.click()))
    controls.set_time_utc.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.set_time_utc_button.click()))
    controls.set_time_gps.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.set_time_gps_button.click()))
    controls.calibrate_alt.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.calibrate_alt_button.click()))
    controls.release_payload.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.release_payload_button.click()))
    controls.release_paraglider.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.activate_paraglider_button.click()))
    controls.release_container.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.release_container_button.click()))
    controls.reset_state.connect(lambda: QtCore.QTimer.singleShot(0, lambda: w.reset_state_button.click()))
    controls.start()

    # ensure clean shutdown: stop thread and cleanup GPIO
    def on_quit():
        controls.stop()
        controls.wait()
        GPIO.cleanup()
    app.aboutToQuit.connect(on_quit)


    w.show()
    sys.exit(app.exec_())


# # Button Click Functions to Call when Physical Control is pressed
# ###############################################################################################################################################

# def click_calibrate_alt_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.calibrate_alt_button.click())  # calls calibrate alt button click   # run immediately

# def click_set_coordinates_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.set_coordinates_button.click())  # calls set coordinates button click   # run immediately

# def click_sim_enable_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.sim_enable_button.click())  # calls sim enable button click   # run immediately

# def click_sim_activate_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.sim_activate_button.click())  # calls sim activate button click   # run immediately

# def click_sim_disable_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.sim_disable_button.click())  # calls sim disable button click   # run immediately

# def click_telemetry_toggle(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.telemetry_toggle_button.click())  # calls telemetry toggle button click   # run immediately

# def click_reset_state_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.reset_state_button.click())  # calls reset state button click   # run immediately

# def click_release_container_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.release_container_button.click())  # calls release container button click   # run immediately

# def click_release_payload_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.release_payload_button.click())  # calls release payload button click   # run immediately

# def click_activate_paraglider_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.activate_paraglider_button.click())  # calls activate paraglider button click   # run immediately

# def click_set_time_utc_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.set_time_utc_button.click())  # calls set time utc button click   # run immediately

# def click_set_time_gps_button(delay=0):
#     QtCore.QTimer.singleShot(delay, lambda: w.set_time_gps_button.click())  # calls set time gps button click   # run immediately

# ################################################################################################################################################

if __name__ == "__main__":
    main()