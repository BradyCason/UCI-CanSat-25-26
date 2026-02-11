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

# --- GPIO pins (copied/kept from controls.py) ---
XbeeLED = 19
pin_9 = 9     # enable simulation
pin_14 = 14   # activate sim
pin_15 = 15   # deactivate sim
pin_11 = 11   # set coords
pin_13 = 13   # set time UTC
pin_26 = 26   # set time GPS
pin_16 = 16   # calibrate altitude
pin_4 = 4     # release payload
pin_27 = 27   # release paraglider
pin_21 = 21   # reset state
pin_7 = 7     # telemetry on toggle
pin_8 = 8     # telemetry off toggle
pin_5 = 5     # release egg pin
pin_18 = 18   # show graphs

GPIO.setmode(GPIO.BCM)
INPUT_PINS = [pin_18, pin_9, pin_14, pin_15, pin_11, pin_13, pin_26, pin_16, pin_4, pin_27, pin_21, pin_7, pin_8, pin_5]
for p in INPUT_PINS:
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(XbeeLED, GPIO.OUT)
GPIO.output(XbeeLED, GPIO.LOW)
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
    release_egg = QtCore.pyqtSignal()
    show_graphs = QtCore.pyqtSignal()

    def __init__(self, poll_interval=0.05, parent=None):
        super().__init__(parent)
        self._running = True
        self.poll_interval = poll_interval
        # track previous states to detect edges (buttons are pull-up; pressed -> LOW)
        self.prev = {p: GPIO.input(p) for p in INPUT_PINS}
        self.graph_proc = None  # Track graph process for toggle functionality

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            for p in INPUT_PINS:
                cur = GPIO.input(p)
                if self.prev[p] == GPIO.HIGH and cur == GPIO.LOW:
                    # falling edge detected -> map pin to signal
                    if p == pin_7 or p == pin_8:
                        self.telemetry_toggle.emit()
                        flash_led(XbeeLED)
                    elif p == pin_9:
                        self.sim_enable.emit()
                        flash_led(XbeeLED)
                    elif p == pin_14:
                        self.sim_activate.emit()
                        flash_led(XbeeLED)
                    elif p == pin_15:
                        self.sim_disable.emit()
                        flash_led(XbeeLED)
                    elif p == pin_11:
                        self.set_coords.emit()
                        flash_led(XbeeLED)
                    elif p == pin_13:
                        self.set_time_utc.emit()
                        flash_led(XbeeLED)
                    elif p == pin_26:
                        self.set_time_gps.emit()
                        flash_led(XbeeLED)
                    elif p == pin_16:
                        self.calibrate_alt.emit()
                        flash_led(XbeeLED)
                    elif p == pin_4:
                        self.release_payload.emit()
                        flash_led(XbeeLED)
                    elif p == pin_27:
                        self.release_paraglider.emit()
                        flash_led(XbeeLED)
                    elif p == pin_21:
                        self.reset_state.emit()
                        flash_led(XbeeLED)
                    elif p == pin_5:
                        self.release_egg.emit()
                        flash_led(XbeeLED)
                    elif p == pin_18:
                        # Toggle graph process: close if running, open if not
                        if self.graph_proc and self.graph_proc.poll() is None:
                            self.graph_proc.terminate()
                            self.graph_proc = None
                        else:
                            self.graph_proc = subprocess.Popen(['python3','/home/jonathan/UCI-CanSat-25-26/Ground-Station/mini_map_test.py'])
                                                
                self.prev[p] = cur
            time.sleep(self.poll_interval)


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
                    "ACCEL_P", "ACCEL_Y", "GPS_TIME", "GPS_ALTITUDE",
                    "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_SATS","CMD_ECHO", "MAX_ALTITUDE",
                    "CONTAINER_RELEASED", "PAYLOAD_RELEASED", "PARAGLIDER_ACTIVE", "TARGET_LATITUDE",
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
COM_PORT = 7

MAKE_CSV_FILE = False
SER_DEBUG = False       # Set as True whenever testing without XBee connected

START_DELIMITER = "~"

ser = None
serialConnected = False

def connect_Serial():
    global ser
    global serialConnected
    if (not SER_DEBUG):
        try:
            # ser = serial.Serial("/dev/tty.usbserial-AR0JQZCB", BAUDRATE, timeout=0.05)
            ser = serial.Serial("COM" + str(COM_PORT), BAUDRATE, timeout=0.05)
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

class GroundStationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        '''
        Initialize the Ground Station Window, and start timer loop for updating UI
        '''
        super().__init__()

        # Load the UI
        ui_path = os.path.join(os.path.dirname(__file__), "gui", "ground_station.ui")
        uic.loadUi(ui_path, self)

        # self.showFullScreen()

        self.setup_UI()
        self.connect_buttons()

        self.payload_released = False
        self.paraglider_active = False
        self.container_released = False

        self.init_graphs()

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

        # Set First Color of Telemetry Toggle button
        if telemetry_on:
            self.telemetry_toggle_button.setText("Telemetry Toggle: On")
            self.make_button_green(self.telemetry_toggle_button)
        else:
            self.telemetry_toggle_button.setText("Telemetry Toggle: Off")
            self.make_button_red(self.telemetry_toggle_button)

    def connect_buttons(self):
        '''
        Connect Buttons to their functions
        '''
        self.sim_enable_button.clicked.connect(lambda: self.handle_simulation("ENABLE"))
        self.sim_activate_button.clicked.connect(lambda: self.handle_simulation("ACTIVATE"))
        self.sim_disable_button.clicked.connect(lambda: self.handle_simulation("DISABLE"))
        self.reset_state_button.clicked.connect(self.reset_state)
        self.set_time_gps_button.clicked.connect(lambda: write_xbee("CMD," + TEAM_ID + ",ST,GPS"))
        self.set_time_utc_button.clicked.connect(lambda: write_xbee("CMD," + TEAM_ID + ",ST," + datetime.now(pytz.timezone("UTC")).strftime("%H:%M:%S")))
        self.calibrate_alt_button.clicked.connect(lambda: write_xbee("CMD," + TEAM_ID + ",CAL"))
        self.release_payload_button.clicked.connect(self.release_payload_clicked)
        self.activate_paraglider_button.clicked.connect(self.activate_paraglider_clicked)
        self.release_container_button.clicked.connect(self.release_container_clicked)
        self.telemetry_toggle_button.clicked.connect(self.toggle_telemetry)
        self.set_coordinates_button.clicked.connect(self.set_coordinates)

        # Connect non-sim buttons to update sim button colors
        self.reset_state_button.clicked.connect(self.non_sim_button_clicked)
        self.set_time_gps_button.clicked.connect(self.non_sim_button_clicked)
        self.set_time_utc_button.clicked.connect(self.non_sim_button_clicked)
        self.calibrate_alt_button.clicked.connect(self.non_sim_button_clicked)
        self.release_payload_button.clicked.connect(self.non_sim_button_clicked)
        self.activate_paraglider_button.clicked.connect(self.non_sim_button_clicked)
        self.release_container_button.clicked.connect(self.non_sim_button_clicked)
        self.telemetry_toggle_button.clicked.connect(self.non_sim_button_clicked)
        self.set_coordinates_button.clicked.connect(self.non_sim_button_clicked)

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
        self.update_color_buttons()

    def make_button_green(self, button):
        '''
        Takes in a button object and makes the background green
        '''
        button.setStyleSheet("QPushButton{background-color: rgba(40, 167, 69, 1);} QPushButton:hover{background-color: rgba(36, 149, 62, 1);}")

    def make_button_red(self, button):
        '''
        Takes in a button object and makes the background red
        '''
        button.setStyleSheet("QPushButton{background-color: rgba(220, 53, 69, 1);} QPushButton:hover{background-color: rgba(200, 45, 59, 1);}")

    def make_button_blue(self, button):
        '''
        Takes in a button object and makes the background blue
        '''
        button.setStyleSheet("QPushButton{background-color: rgba(33,125,182,1);} QPushButton:hover{background-color: rgba(27, 100, 150, 1);}")

    def handle_simulation(self, cmd):
        '''
        Send a simulation command: ("ACTIVATE", "ENABLE", "DISABLE")
        '''
        global sim, sim_enable, csv_indexer

        if cmd == "ACTIVATE" and sim_enable == False or cmd == "ENABLE" and sim_enable == True:
            return
        
        write_xbee("CMD," + TEAM_ID + ",SIM," + cmd)

        if cmd == "ENABLE":
            sim_enable = True
        elif cmd == "DISABLE":
            sim_enable = False
            sim = False
        elif cmd == "ACTIVATE":
            sim_enable = False
            sim = True
            csv_indexer = 0
        
        self.update_sim_button_colors()

        if cmd == "ACTIVATE":
            # Wait 1 second to let the Payload receive the command
            # before sending simp data
            time.sleep(1)

    def update_sim_button_colors(self):
        '''
        Set simulation buttons to the correct colors based off of
        if it is active, enabled, or disabled
        '''
        global sim, sim_enable

        if (sim):
            self.make_button_blue(self.sim_enable_button)
            self.make_button_blue(self.sim_activate_button)
            self.make_button_red(self.sim_disable_button)
        elif (sim_enable):
            self.make_button_blue(self.sim_enable_button)
            self.make_button_green(self.sim_activate_button)
            self.make_button_blue(self.sim_disable_button)
        else:
            self.make_button_green(self.sim_enable_button)
            self.make_button_blue(self.sim_activate_button)
            self.make_button_blue(self.sim_disable_button)

    def non_sim_button_clicked(self):
        '''
        Disable simulation when any button is pressed
        '''
        global sim_enable
        sim_enable = False
        self.update_sim_button_colors()
    
    def reset_state(self):
        global packet_count
        packet_count = 0
        self.reset_graphs()
        write_xbee("CMD," + TEAM_ID + ",RST")

    def toggle_telemetry(self):
        global telemetry_on
        telemetry_on = not telemetry_on

        if telemetry_on:
            write_xbee("CMD,"+ TEAM_ID + ",CX,ON")
            self.telemetry_toggle_button.setText("Telemetry Toggle: On")
            self.make_button_green(self.telemetry_toggle_button)
        else:
            write_xbee("CMD,"+ TEAM_ID + ",CX,OFF")
            self.telemetry_toggle_button.setText("Telemetry Toggle: Off")
            self.make_button_red(self.telemetry_toggle_button)

    def release_payload_clicked(self):
        if self.payload_released:
            write_xbee("CMD," + TEAM_ID + ",MEC,PAYLOAD,OFF")
        else:
            write_xbee("CMD," + TEAM_ID + ",MEC,PAYLOAD,ON")
    
    def activate_paraglider_clicked(self):
        if self.paraglider_active:
            write_xbee("CMD," + TEAM_ID + ",MEC,GLIDER,OFF")
        else:
            write_xbee("CMD," + TEAM_ID + ",MEC,GLIDER,ON")
    
    def release_container_clicked(self):
        if self.container_released:
            write_xbee("CMD," + TEAM_ID + ",MEC,CONTAINER,OFF")
        else:
            write_xbee("CMD," + TEAM_ID + ",MEC,CONTAINER,ON")

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()

    def update_color_buttons(self):
        if self.payload_released:
            self.release_payload_button.setText("Reset Payload Release")
            self.make_button_green(self.release_payload_button)
        else:
            self.release_payload_button.setText("Release Payload")
            self.make_button_red(self.release_payload_button)

        if self.paraglider_active:
            self.activate_paraglider_button.setText("Deactivate Paraglider")
            self.make_button_green(self.activate_paraglider_button)
        else:
            self.activate_paraglider_button.setText("Activate Paraglider")
            self.make_button_red(self.activate_paraglider_button)

        if self.container_released:
            self.release_container_button.setText("Reset Container Release")
            self.make_button_green(self.release_container_button)
        else:
            self.release_container_button.setText("Release Container")
            self.make_button_red(self.release_container_button)

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
        self.accel_r_line, = self.accel_subplot.plot([], [], label="R", color="blue")
        self.accel_p_line, = self.accel_subplot.plot([], [], label="P", color="orange")
        self.accel_y_line, = self.accel_subplot.plot([], [], label="Y", color="green")
        self.accel_figure.legend()

        self.rotation_figure = Figure()
        self.rotation_canvas = FigureCanvas(self.rotation_figure)
        self.rotation_graph.layout().addWidget(self.rotation_canvas)
        self.rotation_subplot = self.rotation_figure.add_subplot(111)
        self.rotation_r_y_data = []
        self.rotation_p_y_data = []
        self.rotation_y_y_data = []
        self.rotation_r_line, = self.rotation_subplot.plot([], [], label="R", color="blue")
        self.rotation_p_line, = self.rotation_subplot.plot([], [], label="P", color="orange")
        self.rotation_y_line, = self.rotation_subplot.plot([], [], label="Y", color="green")
        self.rotation_figure.legend()

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

        # self.timer = QtCore.QTimer()
        # self.timer.setInterval(100)  # 100 ms update
        # self.timer.timeout.connect(self.update_graphs)
        # self.timer.start()

    def update_graphs(self):

        # Update data
        self.x_data.append(telemetry["PACKET_COUNT"])
        self.altitude_y_data.append(float(telemetry["ALTITUDE"]))
        self.accel_r_y_data.append(float(telemetry["ACCEL_R"]))
        self.accel_p_y_data.append(float(telemetry["ACCEL_P"]))
        self.accel_y_y_data.append(float(telemetry["ACCEL_Y"]))
        self.rotation_r_y_data.append(float(telemetry["GYRO_R"]))
        self.rotation_p_y_data.append(float(telemetry["GYRO_P"]))
        self.rotation_y_y_data.append(float(telemetry["GYRO_Y"]))
        self.current_y_data.append(float(telemetry["CURRENT"]))
        self.voltage_y_data.append(float(telemetry["VOLTAGE"]))

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

        # Only plot last 50 points
        if len(self.x_data) > 50:
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

        # Plot
        self.alt_subplot.clear()
        self.alt_subplot.plot(self.x_data, self.altitude_y_data, color='blue')
        self.alt_subplot.set_title("Altitude (m)")
        self.altitude_canvas.draw()

        self.accel_subplot.clear()
        self.accel_subplot.plot(self.x_data, self.accel_r_y_data, color='blue')
        self.accel_subplot.plot(self.x_data, self.accel_p_y_data, color='orange')
        self.accel_subplot.plot(self.x_data, self.accel_y_y_data, color='green')
        self.accel_subplot.set_title("Acceleration (°/s^2)")
        self.accel_canvas.draw()

        self.rotation_subplot.clear()
        self.rotation_subplot.plot(self.x_data, self.rotation_r_y_data, color='blue')
        self.rotation_subplot.plot(self.x_data, self.rotation_p_y_data, color='orange')
        self.rotation_subplot.plot(self.x_data, self.rotation_y_y_data, color='green')
        self.rotation_subplot.set_title("Rotation Rate (°/s)")
        self.rotation_canvas.draw()

        self.current_subplot.clear()
        self.current_subplot.plot(self.x_data, self.current_y_data, color='blue')
        self.current_subplot.set_title("Current (A)")
        self.current_canvas.draw()

        self.voltage_subplot.clear()
        self.voltage_subplot.plot(self.x_data, self.voltage_y_data, color='blue')
        self.voltage_subplot.set_title("Voltage (V)")
        self.voltage_canvas.draw()

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

    def set_coordinates(self):
        dialog = CoordinatesDiaglog()
        result = dialog.exec_()

        if result == QtWidgets.QDialog.Accepted:
            num1, num2 = dialog.get_values()
            write_xbee("CMD," + TEAM_ID + ",SC,{:.6f},{:.6f}".format(num1, num2))
        else:
            QtWidgets.QMessageBox.information(self, "Cancelled", "You pressed Cancel!")


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
    global sim, telemetry, packet_count, w #, last_recieved_packet

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

    if telemetry["PAYLOAD_RELEASED"] == "TRUE":
        w.payload_released = True
    else:
        w.payload_released = False

    if telemetry["PARAGLIDER_ACTIVE"] == "TRUE":
        w.paraglider_active = True
    else:
        w.paraglider_active = False

    if telemetry["CONTAINER_RELEASED"] == "TRUE":
        w.container_released = True
    else:
        w.container_released = False

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
    controls = ControlsThread()
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