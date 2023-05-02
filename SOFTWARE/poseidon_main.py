#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
from datetime import datetime
import os
import serial

# This gets the Qt stuff
from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
import pyautogui
from qt_material import *
import configparser

import numpy as np
from decimal import Decimal

# This is our window from QtCreator
import poseidon_controller_gui

import traceback, sys

# Import custom python files
import poseidon_config
from thread import Thread
from syringe_channel import *
from arduino_connection import Arduino, CannotConnectException

# #####################################
# ERROR HANDLING : CANNOT CONNECT CLASS
# #####################################


# #######################
# GUI : MAIN WINDOW CLASS
# #######################
class MainWindow(QtWidgets.QMainWindow, poseidon_controller_gui.Ui_MainWindow):

    # =======================================================
    # INITIALIZING : The UI and setting some needed variables
    # =======================================================
    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app
        apply_stylesheet(self.app, theme="custom_dark_red.xml", extra={
            'density_scale': '0'
        })

        print("Applied Stylesheet")

        # Setting the UI to a class variable and connecting all GUI Components
        self.ui = poseidon_controller_gui.Ui_MainWindow()

        print("Main Window Created")

        self.ui.setupUi(self)

        print("Setup UI")

        # initialize config parser module and start config load routine
        self.config = self.ui_setup_load_settings_button_clicked()

        print("Config Loaded")

        # creating Arduino connection object
        self.arduino = Arduino(self.config, self)

        print("Arduino Created")
        # Put comments here
        # Populate drop-down UI Objects
        self.populate_syringe_sizes()
        self.populate_pump_units()


        print("Poulated")

        # Set up Syringe Channels
        self.syringe_channel_1 = SyringeChannel(self, 1, self.config)
        self.syringe_channel_2 = SyringeChannel(self, 2, self.config)
        self.syringe_channel_3 = SyringeChannel(self, 3, self.config)
        self.syringes = [self.syringe_channel_1, self.syringe_channel_2, self.syringe_channel_3]

        self.ui.channel_1_slider.setMaximum(int(self.syringe_channel_1.mm_to_steps(300)))
        self.ui.channel_1_slider.setValue(0)
        self.ui.channel_2_slider.setMaximum(int(self.syringe_channel_2.mm_to_steps(300)))
        self.ui.channel_2_slider.setValue(0)
        self.ui.channel_3_slider.setMaximum(int(self.syringe_channel_3.mm_to_steps(300)))
        self.ui.channel_3_slider.setValue(0)

        for channel_number in [1, 2, 3]:
            sc = self.syringes[channel_number - 1]
            sc.syringe_size = self.config[f"syringe-channel-{channel_number}"]['size']
            sc.syringe_area = self.syringe_options[sc.syringe_size]['area']
            sc.syringe_total_volume = self.syringe_options[sc.syringe_size]['volume']


        print("Syringes Created")

        # Connect all UI Objects to the necessary functions
        self.connect_all_gui_components()

        print("Connected GUI")

        # Disable all UI Elements which cant be used as long as the Arduino is not connected
        self.ui_disable_components_when_disconnected()


        print("Disabled UI")

        # Initializing multithreading to allow parallel operations
        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setMaxThreadCount(8)
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        print("Threadpool Started")

        self.ui_update_thread = Thread(self.ui_update_syringe_channel_position_displays)
        self.ui_update_thread.start()

        print("UI Update Thread Started")

        if self.config['connection']['auto-connect'] == 'True':
            print("Attempting Auto Connect")
            self.ui_setup_connect_button_clicked()

        print("Passed Auto Connect. Finished __init__")

    def keystroke(self, key):
        pyautogui.press(key)

    def ui_update_config(self):
        self.config['connection']['com-port'] = self.ui.setup_port_input.currentText()
        self.config['connection']['microsteps'] = int(self.ui.setup_microstepping_input.currentText())
        # TODO: add all config UI objects

    # ===================================
    # CONNECTING : all the GUI Components
    # ===================================
    def connect_all_gui_components(self):

        # ~~~~~~~~~~~~~~~~~~~~~~~~
        # SIDE : CONTROLS + NUMPAD
        # ~~~~~~~~~~~~~~~~~~~~~~~~

        self.arduino.motors_changed_callback = self.ui_update_motor_state
        self.arduino.position_update_callback = self.callback_position_update
        self.ui.side_motors_button.clicked.connect(self.ui_toggle_motor_state_clicked)

        self.ui.side_num_pad_0_button.clicked.connect(lambda: self.keystroke('0'))
        self.ui.side_num_pad_1_button.clicked.connect(lambda: self.keystroke('1'))
        self.ui.side_num_pad_2_button.clicked.connect(lambda: self.keystroke('2'))
        self.ui.side_num_pad_3_button.clicked.connect(lambda: self.keystroke('3'))
        self.ui.side_num_pad_4_button.clicked.connect(lambda: self.keystroke('4'))
        self.ui.side_num_pad_5_button.clicked.connect(lambda: self.keystroke('5'))
        self.ui.side_num_pad_6_button.clicked.connect(lambda: self.keystroke('6'))
        self.ui.side_num_pad_7_button.clicked.connect(lambda: self.keystroke('7'))
        self.ui.side_num_pad_8_button.clicked.connect(lambda: self.keystroke('8'))
        self.ui.side_num_pad_9_button.clicked.connect(lambda: self.keystroke('9'))
        self.ui.side_num_pad_delete_button.clicked.connect(lambda: self.keystroke('backspace'))
        self.ui.side_num_pad_comma_button.clicked.connect(lambda: self.keystroke('.'))

        # ~~~~~~~~~~~~~~~~
        # TAB : Controller
        # ~~~~~~~~~~~~~~~~

        self.ui.channel_1_jog_left_button.clicked.connect(lambda: self.jog(1, -1))
        self.ui.channel_1_jog_right_button.clicked.connect(lambda: self.jog(1, 1))
        self.ui.channel_2_jog_left_button.clicked.connect(lambda: self.jog(2, -1))
        self.ui.channel_2_jog_right_button.clicked.connect(lambda: self.jog(2, 1))
        self.ui.channel_3_jog_left_button.clicked.connect(lambda: self.jog(3, -1))
        self.ui.channel_3_jog_right_button.clicked.connect(lambda: self.jog(3, 1))

        self.ui.channel_1_end_button.clicked.connect(lambda: self.run(1))
        self.ui.channel_2_end_button.clicked.connect(lambda: self.run(2))
        self.ui.channel_3_end_button.clicked.connect(lambda: self.run(3))

        for vol_input, spd_input, sc in [
            (self.ui.channel_1_volume_input, self.ui.channel_1_speed_input, self.syringe_channel_1),
            (self.ui.channel_2_volume_input, self.ui.channel_2_speed_input, self.syringe_channel_2),
            (self.ui.channel_3_volume_input, self.ui.channel_3_speed_input, self.syringe_channel_3),
        ]:
            syringe_option = self.syringe_options[sc.syringe_size]

            vol_input.setDecimals(syringe_option['volume-decimals'])
            vol_input.setMaximum(syringe_option['volume-maximum'])
            vol_input.setSingleStep(syringe_option['volume-step'])
            vol_input.setValue(float(self.config[f"syringe-channel-{sc.channel_number}"]['volume']))

            spd_input.setDecimals(syringe_option['speed-decimals'])
            spd_input.setMaximum(syringe_option['speed-maximum'])
            spd_input.setSingleStep(syringe_option['speed-step'])
            spd_input.setValue(float(self.config[f"syringe-channel-{sc.channel_number}"]['speed']))

        self.ui.jog_delta_input.setValue(float(self.config['misc']['jog-distance']))
        self.ui.jog_delta_speed_input.setValue(float(self.config['misc']['jog-speed']))

        self.ui.side_play_pause_button.clicked.connect(self.run_sequence_thread)

        # ~~~~~~~~~~~
        # TAB : Setup
        # ~~~~~~~~~~~

        # Port, first populate it then connect it (population done earlier)
        if self.config['connection']['com-port'] == '':
            self.ui_setup_port_refresh_button_clicked()
        else:
            self.ui.setup_port_input.addItem(self.config['connection']['com-port'])

        self.ui.setup_refresh_ports_button.clicked.connect(self.ui_setup_port_refresh_button_clicked)
        self.ui.setup_port_input.currentIndexChanged.connect(self.ui_setup_port_input_changed)
        # TODO: generic update function?
        # self.ui.setup_port_input.currentIndexChanged.connect(self.ui_update_config)

        # Set the microstepping value
        self.ui.setup_microstepping_input.currentIndexChanged.connect(self.ui_setup_microsteps_input_changed)
        self.populate_microstepping()

        # Load and Save Settings
        self.ui.setup_load_settings_button.clicked.connect(self.ui_setup_load_settings_button_clicked)
        self.ui.setup_save_settings_button.clicked.connect(self.ui_setup_save_settings_button_clicked)

        # Toggle Fullscreen Mode
        self.ui.setup_toggle_fullscreen_button.clicked.connect(self.ui_setup_toggle_fullscreen_button_clicked)

        # Connect to arduino
        self.ui.setup_connect_button.clicked.connect(self.ui_setup_connect_button_clicked)

        # Send all the settings at once
        self.ui.setup_send_all_settings_button.clicked.connect(self.send_all)

    def ui_update_motor_state(self):
        self.ui.side_motors_button.setChecked(self.arduino.motors_enabled)

    def ui_toggle_motor_state_clicked(self):
        self.arduino.toggle_motors()

    def ui_disable_components_when_disconnected(self):
        # get the connection state from the arduino controller
        connected = self.arduino.connected

        for button in self.ui.side_control_buttons.buttons():
            button.setEnabled(connected)

        for button in self.ui.sequence_control_buttons.buttons():
            button.setEnabled(connected)

        self.ui.setup_send_all_settings_button.setEnabled(connected)

    # ======================
    # FUNCTIONS : Controller
    # ======================

    def callback_position_update(self, p1, r1, p2, r2, p3, r3):
        # Syringe Channel Feedback
        self.syringe_channel_1.absolute_position = p1
        self.syringe_channel_1.remaining_volume = r1
        self.syringe_channel_2.absolute_position = p2
        self.syringe_channel_2.remaining_volume = r2
        self.syringe_channel_3.absolute_position = p3
        self.syringe_channel_3.remaining_volume = r3

    def ui_update_syringe_channel_position_displays(self):
        print('Starting SC Thread')

        while True:
            p1 = self.syringe_channel_1.absolute_position
            r1 = self.syringe_channel_1.remaining_volume
            p2 = self.syringe_channel_2.absolute_position
            r2 = self.syringe_channel_2.remaining_volume
            p3 = self.syringe_channel_3.absolute_position
            r3 = self.syringe_channel_3.remaining_volume

            # UI Slider Feedback
            self.ui.channel_1_slider.setValue(p1)
            self.ui.channel_2_slider.setValue(p2)
            self.ui.channel_3_slider.setValue(p3)

            # UI LCD Feedback
            self.ui.channel_1_pos_lcd.display(self.syringe_channel_1.steps_to_mm(p1))
            self.ui.channel_2_pos_lcd.display(self.syringe_channel_2.steps_to_mm(p2))
            self.ui.channel_3_pos_lcd.display(self.syringe_channel_3.steps_to_mm(p3))

            # UI LCD Feedback
            self.ui.channel_1_rem_lcd.display(self.syringe_channel_1.steps_to_ml(r1))
            self.ui.channel_2_rem_lcd.display(self.syringe_channel_2.steps_to_ml(r2))
            self.ui.channel_3_rem_lcd.display(self.syringe_channel_3.steps_to_ml(r3))

            self.syringe_channel_1.running = (r1 > 0)
            self.syringe_channel_2.running = (r2 > 0)
            self.syringe_channel_3.running = (r3 > 0)
            # self.ui.channel_1_pos_lcd.repaint()

            time.sleep(0.2)

    def run(self, channel):

        vol_input, spd_input, syringe = [
            (self.ui.channel_1_volume_input, self.ui.channel_1_speed_input, self.syringe_channel_1),
            (self.ui.channel_2_volume_input, self.ui.channel_2_speed_input, self.syringe_channel_2),
            (self.ui.channel_3_volume_input, self.ui.channel_3_speed_input, self.syringe_channel_3),
        ][channel - 1]

        self.config[f"syringe-channel-{channel}"]['speed'] = str(spd_input.value())
        self.config[f"syringe-channel-{channel}"]['volume'] = str(vol_input.value())

        # get run distance in mm from SC Object
        absolute_position, run_speed = syringe.get_run_parameters()

        lcds = [self.ui.channel_1_speed_lcd, self.ui.channel_2_speed_lcd, self.ui.channel_3_speed_lcd]
        lcds[channel - 1].display(syringe.steps_to_mm(run_speed))

        self.arduino.jog(channel, absolute_position, run_speed)

    def jog(self, channel, direction):
        print(f"Main> Jog Command. Forward To Arduino Object")

        self.config['misc']['jog-distance'] = str(self.ui.jog_delta_input.value())
        self.config['misc']['jog-speed'] = str(self.ui.jog_delta_speed_input.value())

        lcds = [self.ui.channel_1_speed_lcd, self.ui.channel_2_speed_lcd, self.ui.channel_3_speed_lcd]
        lcds[channel - 1].display(self.config['misc']['jog-speed'])

        absolute_position, jog_speed = self.syringes[channel - 1].get_jog_parameters(direction)

        self.arduino.jog(channel, absolute_position, jog_speed)

    def run_sequence_thread(self):
        print('Woot')
        self.run_sequence_thread = Thread(self.run_sequence)
        self.run_sequence_thread.start()

    def run_sequence(self):
        # Run Channel 1
        self.run(1)
        self.syringe_channel_1.running = True
        print('Go into Wait Loop')
        while self.syringe_channel_1.running:
            time.sleep(1)
            print('Still Running')

        print('SC1 finished')

        self.run(2)
        self.syringe_channel_2.running = True
        while self.syringe_channel_2.running:
            time.sleep(1)

        self.run(3)
        self.syringe_channel_3.running = True
        while self.syringe_channel_3.running:
            time.sleep(1)


    def ui_side_stop_button_clicked(self):
        self.statusBar().showMessage("All motors halted")
        self.arduino.stop_movement()

    # ======================
    # FUNCTIONS : Setup
    # ======================

    def ui_setup_connect_button_clicked(self):
        if not self.arduino.connected:
            try:
                self.arduino.connect()
            except AttributeError:
                self.statusBar().showMessage("Please plug in the board and select a proper port, then press connect.")
            except CannotConnectException:
                self.statusBar().showMessage("Cannot connect to board. Try again..")

            self.statusBar().showMessage("Successfully connected to board.")

            self.ui.setup_connect_button.setText('Disconnect')
        else:
            self.arduino.disconnect()
            self.ui.setup_connect_button.setText('Connect')
            self.statusBar().showMessage("Successfully disconnected from board.")

        self.ui_disable_components_when_disconnected()

    def click_disconnect_button(self):
        self.statusBar().showMessage("You clicked DISCONNECT FROM BOARD")

        self.arduino.disconnect()

        self.ui_disable_components_when_disconnected()
        self.ui.setup_connect_button.setText('Connect')

    # Refresh the list of ports
    def ui_setup_port_refresh_button_clicked(self):
        # Get a list of possible ports from the arduino object
        ports = self.arduino.discover_ports()

        # Update the UI Object and trigger its changed function
        # TODO: findout if the manual trigger is necessary
        self.ui.setup_port_input.clear()
        self.ui.setup_port_input.addItems(ports)
        config_port = self.config['connection']['com-port']
        if config_port in ports:
            self.ui.setup_port_input.setCurrentText(config_port)
        else:
            self.ui.setup_port_input.setCurrentText(ports[0])


    def ui_setup_port_input_changed(self):
        # get the port from UI and forward it to the config and arduino objects.
        self.config['connection']['com-port'] = self.ui.setup_port_input.currentText()

    # Set the microstepping amount from the dropdown menu
    # TODO: There is definitely a better way of updating different variables
    # after there is a change of some input from the user. need to figure out.
    def ui_setup_microsteps_input_changed(self):
        # get the microsteps setting from UI and forward it to the config and arduino objects.
        self.config['misc']['microsteps'] = self.ui.setup_microstepping_input.currentText()

    def ui_setup_load_settings_button_clicked(self):
        return poseidon_config.PoseidonConfig.load_config()
        # populate UI with loaded settings


    def ui_setup_save_settings_button_clicked(self):
        poseidon_config.PoseidonConfig.save_config(self.config)

    def ui_setup_toggle_fullscreen_button_clicked(self):
        if self.isFullScreen():
            self.showNormal()
            self.config['misc']['fullscreen'] = str(False)
        else:
            self.showFullScreen()
            self.config['misc']['fullscreen'] = str(False)


    # Populate the microstepping amounts for the dropdown menu
    def populate_microstepping(self):
        microstepping_values = ['1', '2', '4', '8', '16', '32']
        self.ui.setup_microstepping_input.addItems(microstepping_values)
        self.ui.setup_microstepping_input.setCurrentText('32')
        self.config['misc']['microsteps'] = self.ui.setup_microstepping_input.currentText()

    # Populate the list of possible syringes to the dropdown menus
    def populate_syringe_sizes(self):
        # Volume given in mL
        # Area given in mm^2
        # TODO: allow these to be setup in the software and loaded/saved to an .ini file
        self.syringe_options = {
            '500 mL': {
                'volume': '500',
                'area': 3631.681168,
                'volume-decimals': 0,
                'volume-maximum': 550,
                'volume-step': 1,
                'speed-decimals': 0,
                'speed-maximum': 9999,
                'speed-step': 1
            }
        }

        # Update the UI Objects and set to the value stored in the config
        self.ui.setup_channel_1_syringe_input.addItems(self.syringe_options.keys())
        self.ui.setup_channel_2_syringe_input.addItems(self.syringe_options.keys())
        self.ui.setup_channel_3_syringe_input.addItems(self.syringe_options.keys())
        self.ui.setup_channel_1_syringe_input.setCurrentText(self.config['syringe-channel-1']['size'])
        self.ui.setup_channel_2_syringe_input.setCurrentText(self.config['syringe-channel-2']['size'])
        self.ui.setup_channel_3_syringe_input.setCurrentText(self.config['syringe-channel-3']['size'])

    def populate_pump_units(self):
        # TODO: Think about a better method
        # TODO: add units to config so they can be saved and loaded
        units = ['mm/s', 'mL/s', 'mL/hr', 'µL/hr']
        self.ui.setup_channel_1_unit_input.addItems(units)
        self.ui.setup_channel_2_unit_input.addItems(units)
        self.ui.setup_channel_3_unit_input.addItems(units)

    # Send all settings
    def send_all(self):
        pass
        # self.statusBar().showMessage("You clicked SEND ALL SETTINGS")
        #
        # self.settings = []
        # self.settings.append("<SETTING,SPEED,1,"+str(self.p1_speed_to_send)+",F,0.0,0.0,0.0>")
        # self.settings.append("<SETTING,ACCEL,1,"+str(self.p1_accel_to_send)+",F,0.0,0.0,0.0>")
        #
        # self.settings.append("<SETTING,SPEED,2,"+str(self.p2_speed_to_send)+",F,0.0,0.0,0.0>")
        # self.settings.append("<SETTING,ACCEL,2,"+str(self.p2_accel_to_send)+",F,0.0,0.0,0.0>")
        #
        # self.settings.append("<SETTING,SPEED,3,"+str(self.p3_speed_to_send)+",F,0.0,0.0,0.0>")
        # self.settings.append("<SETTING,ACCEL,3,"+str(self.p3_accel_to_send)+",F,0.0,0.0,0.0>")
        #
        # print("Sending all settings..")
        # self.arduino.send_commands(self.settings)
        #
        # self.ui.p1_setup_send_BTN.setStyleSheet("background-color: none")
        # self.ui.p2_setup_send_BTN.setStyleSheet("background-color: none")
        # self.ui.p3_setup_send_BTN.setStyleSheet("background-color: none")
        #
        # self.ungrey_out_components()


    '''
        Syringe Volume (mL)	|		Syringe Area (mm^2)
    -----------------------------------------------
        1				|			17.34206347
        3				|			57.88559215
        5				|			112.9089185
        10				|			163.539454
        20				|			285.022957
        30				|			366.0961536
        60				|			554.0462538

    IMPORTANT: These are for BD Plastic syringes ONLY!! Others will vary.
    '''

    def closeEvent(self, event):
        try:
            if self.arduino.connected:
                self.arduino.disconnect()
            #self.threadpool.end()

        except AttributeError:
            pass
        sys.exit()

# I feel better having one of these
def main():
    # a new app instance
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(app)
    window.setWindowTitle("Poseidon Pumps Controller - Fischer Lab Fork 2023")
    window.show()
    # without this, the script exits immediately.
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
