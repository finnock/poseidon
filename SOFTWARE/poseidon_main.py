#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import os
import serial

# This gets the Qt stuff
from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
import pyautogui
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
    def __init__(self):
        super(MainWindow, self).__init__()

        # creating Arduino connection object
        self.arduino = Arduino()

        # Setting the UI to a class variable and connecting all GUI Components
        self.ui = poseidon_controller_gui.Ui_MainWindow()
        self.ui.setupUi(self)

        # initialize config parser module and start config load routine
        self.config = self.ui_setup_load_settings_button_clicked()

        # Put comments here
        # Populate drop-down UI Objects
        self.populate_microstepping()
        self.populate_syringe_sizes()
        self.populate_pump_units()

        # Set up Syringe Channels
        self.syringe_channel_1 = SyringeChannel(self, 1)
        self.syringe_channel_2 = SyringeChannel(self, 2)
        self.syringe_channel_3 = SyringeChannel(self, 3)

        sc = self.syringe_channel_1
        sc_config = self.config['syringe_channel_1']
        sc.syringe_size = sc_config['size']
        sc.syringe_area = self.syringe_options[sc.syringe_size]['area']
        sc.syringe_total_volume = self.syringe_options[sc.syringe_size]['volume']

        sc = self.syringe_channel_2
        sc_config = self.config['syringe_channel_2']
        sc.syringe_size = sc_config['size']
        sc.syringe_area = self.syringe_options[sc.syringe_size]['area']
        sc.syringe_total_volume = self.syringe_options[sc.syringe_size]['volume']

        sc = self.syringe_channel_3
        sc_config = self.config['syringe_channel_3']
        sc.syringe_size = sc_config['size']
        sc.syringe_area = self.syringe_options[sc.syringe_size]['area']
        sc.syringe_total_volume = self.syringe_options[sc.syringe_size]['volume']

        # Connect all UI Objects to the necessary functions
        self.connect_all_gui_components()

        # Disable all UI Elements which cant be used as long as the Arduino is not connected
        self.grey_out_components()

        # Initializing multithreading to allow parallel operations
        self.threadpool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

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

        self.arduino.motors_changed = self.motor_state_change
        self.ui.motor_state_button.clicked.connect(self.toggle_motor_state)

        self.ui.numpad_1_BTN.clicked.connect(lambda: self.keystroke('1'))
        self.ui.numpad_2_BTN.clicked.connect(lambda: self.keystroke('2'))
        self.ui.numpad_3_BTN.clicked.connect(lambda: self.keystroke('3'))
        self.ui.numpad_4_BTN.clicked.connect(lambda: self.keystroke('4'))
        self.ui.numpad_5_BTN.clicked.connect(lambda: self.keystroke('5'))
        self.ui.numpad_6_BTN.clicked.connect(lambda: self.keystroke('6'))
        self.ui.numpad_7_BTN.clicked.connect(lambda: self.keystroke('7'))
        self.ui.numpad_8_BTN.clicked.connect(lambda: self.keystroke('8'))
        self.ui.numpad_9_BTN.clicked.connect(lambda: self.keystroke('9'))
        self.ui.numpad_delete_BTN.clicked.connect(lambda: self.keystroke('backspace'))
        self.ui.numpad_komma_BTN.clicked.connect(lambda: self.keystroke('.'))

        # ~~~~~~~~~~~~~~~~
        # TAB : Controller
        # ~~~~~~~~~~~~~~~~

        # ~~~~~~~~~~~
        # TAB : Setup
        # ~~~~~~~~~~~

        # Port, first populate it then connect it (population done earlier)
        self.ui.setup_refresh_ports_button.clicked.connect(self.refresh_ports)
        self.ui.setup_port_input.currentIndexChanged.connect(self.ui_setup_port_input_changed)
        self.refresh_ports()
        self.ui.setup_refresh_ports_button.clicked.connect(self.ui_setup_port_refresh_button_clicked)
        self.ui.setup_port_input.currentIndexChanged.connect(self.ui_update_config)

        # Set the microstepping value, default is 1
        self.ui.setup_microstepping_input.currentIndexChanged.connect(self.ui_setup_microsteps_input_changed)
        self.populate_microstepping()

        # Load and Save Settings
        self.ui.setup_load_settings_button.clicked.connect(self.ui_setup_load_settings_button_clicked)
        self.ui.setup_save_settings_button.clicked.connect(self.ui_setup_save_settings_button_clicked)

        # Toggle Fullscreen Mode
        self.ui.toggle_fullscreen_BTN.clicked.connect(self.toggle_fullscreen)

        # Px syringe size, populate then connect (population done earlier)
        self.ui.p1_syringe_DROPDOWN.currentIndexChanged.connect(self.set_p1_syringe)
        self.ui.p2_syringe_DROPDOWN.currentIndexChanged.connect(self.set_p2_syringe)
        self.ui.p3_syringe_DROPDOWN.currentIndexChanged.connect(self.set_p3_syringe)

        # warning to send the info to the controller
        self.ui.p1_syringe_DROPDOWN.currentIndexChanged.connect(self.send_p1_warning)
        self.ui.p2_syringe_DROPDOWN.currentIndexChanged.connect(self.send_p2_warning)
        self.ui.p3_syringe_DROPDOWN.currentIndexChanged.connect(self.send_p3_warning)

        # Px units
        self.ui.p1_units_DROPDOWN.currentIndexChanged.connect(self.set_p1_units)
        self.ui.p2_units_DROPDOWN.currentIndexChanged.connect(self.set_p2_units)
        self.ui.p3_units_DROPDOWN.currentIndexChanged.connect(self.set_p3_units)

        # warning to send the info to the controller
        self.ui.p1_units_DROPDOWN.currentIndexChanged.connect(self.send_p1_warning)
        self.ui.p2_units_DROPDOWN.currentIndexChanged.connect(self.send_p2_warning)
        self.ui.p3_units_DROPDOWN.currentIndexChanged.connect(self.send_p3_warning)

        # Px speed
        self.ui.p1_speed_INPUT.valueChanged.connect(self.set_p1_speed)
        self.ui.p2_speed_INPUT.valueChanged.connect(self.set_p2_speed)
        self.ui.p3_speed_INPUT.valueChanged.connect(self.set_p3_speed)

        # warning to send the info to the controller
        self.ui.p1_speed_INPUT.valueChanged.connect(self.send_p1_warning)
        self.ui.p2_speed_INPUT.valueChanged.connect(self.send_p2_warning)
        self.ui.p3_speed_INPUT.valueChanged.connect(self.send_p3_warning)

        # Px accel
        self.ui.p1_accel_INPUT.valueChanged.connect(self.set_p1_accel)
        self.ui.p2_accel_INPUT.valueChanged.connect(self.set_p2_accel)
        self.ui.p3_accel_INPUT.valueChanged.connect(self.set_p3_accel)

        # warning to send the info to the controller
        self.ui.p1_accel_INPUT.valueChanged.connect(self.send_p1_warning)
        self.ui.p2_accel_INPUT.valueChanged.connect(self.send_p2_warning)
        self.ui.p3_accel_INPUT.valueChanged.connect(self.send_p3_warning)

        # Px jog delta (setup)
        self.ui.p1_setup_jog_delta_INPUT.currentIndexChanged.connect(self.set_p1_setup_jog_delta)
        self.ui.p2_setup_jog_delta_INPUT.currentIndexChanged.connect(self.set_p2_setup_jog_delta)
        self.ui.p3_setup_jog_delta_INPUT.currentIndexChanged.connect(self.set_p3_setup_jog_delta)

        # warning to send the info to the contorller
        self.ui.p1_setup_jog_delta_INPUT.currentIndexChanged.connect(self.send_p1_warning)
        self.ui.p2_setup_jog_delta_INPUT.currentIndexChanged.connect(self.send_p2_warning)
        self.ui.p3_setup_jog_delta_INPUT.currentIndexChanged.connect(self.send_p3_warning)

        # Px send settings
        self.ui.p1_setup_send_BTN.clicked.connect(self.send_p1_settings)
        self.ui.p2_setup_send_BTN.clicked.connect(self.send_p2_settings)
        self.ui.p3_setup_send_BTN.clicked.connect(self.send_p3_settings)

        # remove warning to send settings
        self.ui.p1_setup_send_BTN.clicked.connect(self.send_p1_success)
        self.ui.p2_setup_send_BTN.clicked.connect(self.send_p2_success)
        self.ui.p3_setup_send_BTN.clicked.connect(self.send_p3_success)

        # Connect to arduino
        self.ui.setup_connect_button.clicked.connect(self.ui_setup_connect_button_clicked)

        # Send all the settings at once
        self.ui.send_all_BTN.clicked.connect(self.send_all)

    def ui_update_motor_state(self):
        self.ui.side_motors_button.setChecked(self.arduino.motors_enabled)

    def toggle_motor_state(self):
        self.arduino.toggle_motors()

    def send_p1_warning(self):
        self.ui.p1_setup_send_BTN.setStyleSheet("background-color: green; color: black")

    def send_p2_warning(self):
        self.ui.p2_setup_send_BTN.setStyleSheet("background-color: green; color: black")

    def send_p3_warning(self):
        self.ui.p3_setup_send_BTN.setStyleSheet("background-color: green; color: black")

    def send_p1_success(self):
        self.ui.p1_setup_send_BTN.setStyleSheet("background-color: none")

    def send_p2_success(self):
        self.ui.p2_setup_send_BTN.setStyleSheet("background-color: none")

    def send_p3_success(self):
        self.ui.p3_setup_send_BTN.setStyleSheet("background-color: none")

    def grey_out_components(self):
        # ~~~~~~~~~~~~~~~~
        # TAB : Controller
        # ~~~~~~~~~~~~~~~~
        self.ui.run_BTN.setEnabled(False)
        self.ui.pause_BTN.setEnabled(False)
        self.ui.zero_BTN.setEnabled(False)
        self.ui.stop_BTN.setEnabled(False)
        self.ui.jog_plus_BTN.setEnabled(False)
        self.ui.jog_minus_BTN.setEnabled(False)

        # ~~~~~~~~~~~~~~~~
        # TAB : Setup
        # ~~~~~~~~~~~~~~~~
        self.ui.p1_setup_send_BTN.setEnabled(False)
        self.ui.p2_setup_send_BTN.setEnabled(False)
        self.ui.p3_setup_send_BTN.setEnabled(False)
        self.ui.send_all_BTN.setEnabled(False)

    def ungrey_out_components(self):
        # ~~~~~~~~~~~~~~~~
        # TAB : Controller
        # ~~~~~~~~~~~~~~~~
        self.ui.run_BTN.setEnabled(True)
        self.ui.pause_BTN.setEnabled(True)
        self.ui.zero_BTN.setEnabled(True)
        self.ui.stop_BTN.setEnabled(True)
        self.ui.jog_plus_BTN.setEnabled(True)
        self.ui.jog_minus_BTN.setEnabled(True)

        self.ui.run_BTN.setStyleSheet("background-color: green; color: black")
        self.ui.pause_BTN.setStyleSheet("background-color: yellow; color: black")
        self.ui.stop_BTN.setStyleSheet("background-color: red; color: black")

        # ~~~~~~~~~~~~~~~~
        # TAB : Setup
        # ~~~~~~~~~~~~~~~~
        self.ui.p1_setup_send_BTN.setEnabled(True)
        self.ui.p2_setup_send_BTN.setEnabled(True)
        self.ui.p3_setup_send_BTN.setEnabled(True)
        self.ui.send_all_BTN.setEnabled(True)
    # ======================
    # FUNCTIONS : Controller
    # ======================

    def toggle_p1_activation(self):
        if self.ui.p1_activate_CHECKBOX.isChecked():
            self.is_p1_active = True
        else:
            self.is_p1_active = False

    def toggle_p2_activation(self):
        if self.ui.p2_activate_CHECKBOX.isChecked():
            self.is_p2_active = True
        else:
            self.is_p2_active = False

    def toggle_p3_activation(self):
        if self.ui.p3_activate_CHECKBOX.isChecked():
            self.is_p3_active = True
        else:
            self.is_p3_active = False

    # Get a list of active pumps (IDK if this is the best way to do this)
    def get_active_pumps(self):
        pumps_list = [self.is_p1_active, self.is_p2_active, self.is_p3_active]
        active_pumps = [i+1 for i in range(len(pumps_list)) if pumps_list[i]]
        return active_pumps

    def display_p1_syringe(self):
        self.ui.p1_syringe_LABEL.setText(self.ui.p1_syringe_DROPDOWN.currentText())

    def display_p2_syringe(self):
        self.ui.p2_syringe_LABEL.setText(self.ui.p2_syringe_DROPDOWN.currentText())

    def display_p3_syringe(self):
        self.ui.p3_syringe_LABEL.setText(self.ui.p3_syringe_DROPDOWN.currentText())

    def display_p1_speed(self):
        self.ui.p1_units_LABEL.setText(str(self.p1_speed) + " " + self.ui.p1_units_DROPDOWN.currentText())

    def display_p2_speed(self):
        self.ui.p2_units_LABEL.setText(str(self.p2_speed) + " " + self.ui.p2_units_DROPDOWN.currentText())

    def display_p3_speed(self):
        self.ui.p3_units_LABEL.setText(str(self.p3_speed) + " " + self.ui.p3_units_DROPDOWN.currentText())

    # Set Px distance to move
    def set_p1_amount(self):
        self.p1_amount = self.ui.p1_amount_INPUT.value()

    def set_p2_amount(self):
        self.p2_amount = self.ui.p2_amount_INPUT.value()

    def set_p3_amount(self):
        self.p3_amount = self.ui.p3_amount_INPUT.value()

    # Set Px jog delta
    #def set_p1_jog_delta(self):
    #	self.p1_jog_delta = self.ui.p1_jog_delta_INPUT.value()
    #def set_p2_jog_delta(self):
    #	self.p2_jog_delta = self.ui.p2_jog_delta_INPUT.value()
    #def set_p3_jog_delta(self):
    #	self.p3_jog_delta = self.ui.p3_jog_delta_INPUT.value()

    # Set the coordinate system for the pump
    def set_coordinate(self, radio):
        if radio.text() == "Abs.":
            if radio.isChecked():
                self.coordinate = "absolute"
        if radio.text() == "Incr.":
            if radio.isChecked():
                self.coordinate = "incremental"

    def run(self):
        self.statusBar().showMessage("You clicked RUN")
        testData = []

        active_pumps = self.get_active_pumps()
        if len(active_pumps) > 0:

            p1_input_displacement = str(self.convert_displacement(self.p1_amount, self.p1_units, self.p1_syringe_area, self.microstepping))
            p2_input_displacement = str(self.convert_displacement(self.p2_amount, self.p2_units, self.p2_syringe_area, self.microstepping))
            p3_input_displacement = str(self.convert_displacement(self.p3_amount, self.p3_units, self.p3_syringe_area, self.microstepping))

            pumps_2_run = ''.join(map(str,active_pumps))

            cmd = "<RUN,DIST,"+pumps_2_run+",0.0,F," + p1_input_displacement + "," + p2_input_displacement + "," + p3_input_displacement + ">"

            testData.append(cmd)

            print("Sending RUN command..")
            thread = Thread(self.runTest, testData)
            thread.finished.connect(lambda:self.thread_finished(thread))
            thread.start()
            print("RUN command sent.")
        else:
            self.statusBar().showMessage("No pumps enabled.")


    # fix
    def zero(self):
        self.statusBar().showMessage("You clicked ZERO")
        testData = []

        cmd = "<ZERO,BLAH,BLAH,BLAH,F,0.0,0.0,0.0>"

        print("Sending ZERO command..")
        thread = Thread(self.runTest, testData)
        thread.finished.connect(lambda:self.thread_finished(thread))
        thread.start()
        print("ZERO command sent.")


    def ui_side_stop_button_clicked(self):
        self.statusBar().showMessage("All motors halted")
        self.arduino.stop_movement()

    def jog(self, btn):
        print(f"Main> Jog Command. Forward To Arduino Object")
        self.arduino.jog(1, "F", 1)

    # ======================
    # FUNCTIONS : Setup
    # ======================

    def ui_setup_connect_button_clicked(self):

        try:
            self.arduino.connect()
        except AttributeError:
            self.statusBar().showMessage("Please plug in the board and select a proper port, then press connect.")
        except CannotConnectException:
            self.statusBar().showMessage("Cannot connect to board. Try again..")

        self.statusBar().showMessage("Successfully connected to board.")

        self.ui.setup_connect_button.setText('Disconnect')

        # Change UI Button states accordingly
        self.ui.disconnect_BTN.setEnabled(True)
        self.ui.p1_setup_send_BTN.setEnabled(True)
        self.ui.p2_setup_send_BTN.setEnabled(True)
        self.ui.p3_setup_send_BTN.setEnabled(True)
        self.ui.send_all_BTN.setEnabled(True)
        self.ui.connect_BTN.setEnabled(False)

    def click_disconnect_button(self):
        self.statusBar().showMessage("You clicked DISCONNECT FROM BOARD")

        self.arduino.disconnect()

        self.grey_out_components()
        self.ui.setup_connect_button.setText('Connect')


    # Refresh the list of ports
    def ui_setup_port_refresh_button_clicked(self):
        # Get a list of possible ports from the arduino object
        ports = self.arduino.discover_ports()

        # Update the UI Object and trigger its changed function
        # TODO: findout if the manual trigger is necessary
        self.ui.setup_port_input.clear()
        self.ui.setup_port_input.addItems(ports)
        # TODO: check if port from config is found in port list
        # otherwise set to first port from list
        self.ui.setup_port_input.setCurrentText(self.config['setup']['port'])

    def ui_setup_port_input_changed(self):
        # get the port from UI and forward it to the config and arduino objects.
        self.config['connect']['port'] = self.ui.setup_port_input.currentText()

    # Set the microstepping amount from the dropdown menu
    # TODO: There is definitely a better way of updating different variables
    # after there is a change of some input from the user. need to figure out.
    def ui_setup_microsteps_input_changed(self):
        # get the microsteps setting from UI and forward it to the config and arduino objects.
        self.config['connect']['microsteps'] = int(self.ui.setup_port_input.currentText())

    def ui_setup_load_settings_button_clicked(self):
        return poseidon_config.PoseidonConfig.load_config()
        # populate UI with loaded settings


    def ui_setup_save_settings_button_clicked(self):
        poseidon_config.PoseidonConfig.save_config(self.config)

    def ui_setup_toggle_fullscreen_button_clicked(self):
        if self.isFullScreen():
            self.showNormal()
            self.config['misc']['fullscreen'] = False
        else:
            self.showFullScreen()
            self.config['misc']['fullscreen'] = True


    # Populate the microstepping amounts for the dropdown menu
    def populate_microstepping(self):
        microstepping_values = ['1', '2', '4', '8', '16', '32']
        self.ui.setup_microstepping_input.addItems(microstepping_values)
        self.ui.setup_microstepping_input.setCurrentText('32')
        self.config['config']['microsteps'] = int(self.ui.setup_microstepping_input.currentText())

    # Populate the list of possible syringes to the dropdown menus
    def populate_syringe_sizes(self):
        # Volume given in mL
        # Area given in mm^2
        # TODO: allow these to be setup in the software and loaded/saved to an .ini file
        self.syringe_options = {
            '500 mL': {
                'volume': '500',
                'area': 3631.681168,
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
        self.statusBar().showMessage("You clicked SEND ALL SETTINGS")

        self.settings = []
        self.settings.append("<SETTING,SPEED,1,"+str(self.p1_speed_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,ACCEL,1,"+str(self.p1_accel_to_send)+",F,0.0,0.0,0.0>")

        self.settings.append("<SETTING,SPEED,2,"+str(self.p2_speed_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,ACCEL,2,"+str(self.p2_accel_to_send)+",F,0.0,0.0,0.0>")

        self.settings.append("<SETTING,SPEED,3,"+str(self.p3_speed_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,ACCEL,3,"+str(self.p3_accel_to_send)+",F,0.0,0.0,0.0>")

        print("Sending all settings..")
        self.arduino.send_commands(self.settings)

        self.ui.p1_setup_send_BTN.setStyleSheet("background-color: none")
        self.ui.p2_setup_send_BTN.setStyleSheet("background-color: none")
        self.ui.p3_setup_send_BTN.setStyleSheet("background-color: none")

        self.ungrey_out_components()



    # =======================
    # MISC : Functions I need
    # =======================

    def steps2mm(self, steps, microsteps):
    # 200 steps per rev
    # one rev is 0.8mm dist
        #mm = steps/200/32*0.8
        mm = steps/200/microsteps*0.8
        return mm

    def steps2mL(self, steps, syringe_area):
        mL = self.mm32mL(self.steps2mm(steps)*syringe_area)
        return mL

    def steps2uL(self, steps, syringe_area):
        uL = self.mm32uL(self.steps2mm(steps)*syringe_area)
        return uL


    def mm2steps(self, mm, microsteps):
        steps = mm/0.8*200*microsteps
        #steps = mm*200/0.8
        return steps

    def mL2steps(self, mL, syringe_area, microsteps):
        # note syringe_area is in mm^2
        steps = self.mm2steps(self.mL2mm3(mL)/syringe_area, microsteps)
        return steps

    def uL2steps(self, uL, syringe_area, microsteps):
        steps = self.mm2steps(self.uL2mm3(uL)/syringe_area, microsteps)
        return steps


    def mL2uL(self, mL):
        return mL*1000.0

    def mL2mm3(self, mL):
        return mL*1000.0


    def uL2mL(self, uL):
        return uL/1000.0

    def uL2mm3(self, uL):
        return uL


    def mm32mL(self, mm3):
        return mm3/1000.0

    def mm32uL(self, mm3):
        return mm3

    def persec2permin(self, value_per_sec):
        value_per_min = value_per_sec*60.0
        return value_per_min

    def persec2perhour(self, value_per_sec):
        value_per_hour = value_per_sec*60.0*60.0
        return value_per_hour


    def permin2perhour(self, value_per_min):
        value_per_hour = value_per_min*60.0
        return value_per_hour

    def permin2persec(self, value_per_min):
        value_per_sec = value_per_min/60.0
        return value_per_sec


    def perhour2permin(self, value_per_hour):
        value_per_min = value_per_hour/60.0
        return value_per_min

    def perhour2persec(self, value_per_hour):
        value_per_sec = value_per_hour/60.0/60.0
        return value_per_sec

    def convert_displacement(self, displacement, units, syringe_area, microsteps):
        length = units.split("/")[0]
        time = units.split("/")[1]
        inp_displacement = displacement
        # convert length first
        if length == "mm":
            displacement = self.mm2steps(displacement, microsteps)
        elif length == "mL":
            displacement = self.mL2steps(displacement, syringe_area, microsteps)
        elif length == "µL":
            displacement = self.uL2steps(displacement, syringe_area, microsteps)

        print('______________________________')
        print("INPUT  DISPLACEMENT: " + str(inp_displacement) + ' ' + length)
        print("OUTPUT DISPLACEMENT: " + str(displacement) + ' steps')
        print('\n############################################################\n')
        return displacement

    def convert_speed(self, inp_speed, units, syringe_area, microsteps):
        length = units.split("/")[0]
        time = units.split("/")[1]


        # convert length first
        if length == "mm":
            speed = self.mm2steps(inp_speed, microsteps)
        elif length == "mL":
            speed = self.mL2steps(inp_speed, syringe_area, microsteps)
        elif length == "µL":
            speed = self.uL2steps(inp_speed, syringe_area, microsteps)


        # convert time next
        if time == "s":
            pass
        elif time == "min":
            speed = self.permin2persec(speed)
        elif time == "hr":
            speed = self.perhour2persec(speed)



        print("INPUT  SPEED: " + str(inp_speed) + ' ' + units)
        print("OUTPUT SPEED: " + str(speed) + ' steps/s')
        return speed

    def convert_accel(self, accel, units, syringe_area, microsteps):
        length = units.split("/")[0]
        time = units.split("/")[1]
        inp_accel = accel
        accel = accel

        # convert length first
        if length == "mm":
            accel = self.mm2steps(accel, microsteps)
        elif length == "mL":
            accel = self.mL2steps(accel, syringe_area, microsteps)
        elif length == "µL":
            accel = self.uL2steps(accel, syringe_area, microsteps)

        # convert time next
        if time == "s":
            pass
        elif time == "min":
            accel = self.permin2persec(self.permin2persec(accel))
        elif time == "hr":
            accel = self.perhour2persec(self.perhour2persec(accel))

        print('______________________________')
        print("INPUT  ACCEL: " + str(inp_accel) + ' ' + units + '/' + time)
        print("OUTPUT ACCEL: " + str(accel) + ' steps/s/s')
        return accel


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
            self.global_listener_thread.ui_side_stop_button_clicked()
            self.serial.close()
            #self.threadpool.end()

        except AttributeError:
            pass
        sys.exit()

# I feel better having one of these
def main():
    # a new app instance
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Poseidon Pumps Controller - Fischer Lab Fork 2023")
    window.show()
    # without this, the script exits immediately.
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
