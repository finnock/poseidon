#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import sys
from datetime import datetime
import os

# This gets the Qt stuff
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
import pyautogui

import numpy as np
from decimal import Decimal

# This is our window from QtCreator
import poseidon_controller_gui

import traceback, sys
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
        # creating Arduino connection object
        self.arduino = Arduino()

        # Setting the UI to a class variable and connecting all GUI Components
        super(MainWindow, self).__init__()
        self.ui = poseidon_controller_gui.Ui_MainWindow()
        self.ui.setupUi(self)

        # Put comments here
        self.populate_microstepping()
        self.populate_syringe_sizes()
        self.populate_pump_jog_delta()
        self.populate_pump_units()
        self.setting_variables()
        self.populate_ports()
        self.set_port()

        # Set up Syringe Channels
        self.syringe_channel_1 = SyringeChannel(self, 1)

        self.connect_all_gui_components()
        self.grey_out_components()


        # Initializing multithreading to allow parallel operations
        self.threadpool = QtCore.QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())




    # =============================
    # SETTING : important variables
    # =============================
    def setting_variables(self):

        self.set_p1_syringe()
        self.set_p2_syringe()
        self.set_p3_syringe()

        self.is_p1_active = False
        self.is_p2_active = False
        self.is_p3_active = False

        self.experiment_notes = ""

    def thread_finished(self, th):
        print("Your thread has completed. Now terminating..")
        th.stop()
        print("Thread has been terminated.")
        print("=============================\n\n")
        # here is where you need to end the thread

    def keystroke(self, key):
        pyautogui.press(key)

    # ===================================
    # CONNECTING : all the GUI Components
    # ===================================
    def connect_all_gui_components(self):

        # ~~~~~~~~~~~~~~~
        # SIDE : NUMPAD
        # ~~~~~~~~~~~~~~~

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

        # Px active checkboxes
        self.ui.p1_activate_CHECKBOX.stateChanged.connect(self.toggle_p1_activation)
        self.ui.p2_activate_CHECKBOX.stateChanged.connect(self.toggle_p2_activation)
        self.ui.p3_activate_CHECKBOX.stateChanged.connect(self.toggle_p3_activation)

        # Px display (TODO)

        # Px syringe display
        self.ui.p1_syringe_DROPDOWN.currentIndexChanged.connect(self.display_p1_syringe)
        self.ui.p2_syringe_DROPDOWN.currentIndexChanged.connect(self.display_p2_syringe)
        self.ui.p3_syringe_DROPDOWN.currentIndexChanged.connect(self.display_p3_syringe)


        # Px speed display
        self.ui.p1_units_DROPDOWN.currentIndexChanged.connect(self.display_p1_speed)
        self.ui.p2_units_DROPDOWN.currentIndexChanged.connect(self.display_p2_speed)
        self.ui.p3_units_DROPDOWN.currentIndexChanged.connect(self.display_p3_speed)



        #self.populate_pump_units()

        # Px amount
        self.ui.p1_amount_INPUT.valueChanged.connect(self.set_p1_amount)
        self.ui.p2_amount_INPUT.valueChanged.connect(self.set_p2_amount)
        self.ui.p3_amount_INPUT.valueChanged.connect(self.set_p3_amount)

        # Px jog delta
        #self.ui.p1_jog_delta_INPUT.valueChanged.connect(self.set_p1_jog_delta)
        #self.ui.p2_jog_delta_INPUT.valueChanged.connect(self.set_p2_jog_delta)
        #self.ui.p3_jog_delta_INPUT.valueChanged.connect(self.set_p3_jog_delta)

        # Action buttons
        self.ui.run_BTN.clicked.connect(self.run)
        self.ui.pause_BTN.clicked.connect(self.pause)
        self.ui.zero_BTN.clicked.connect(self.zero)
        self.ui.stop_BTN.clicked.connect(self.stop)

        # Jog Buttons
        self.ui.jog_plus_BTN.clicked.connect(lambda:self.jog(self.ui.jog_plus_BTN))
        self.ui.jog_minus_BTN.clicked.connect(lambda:self.jog(self.ui.jog_minus_BTN))

        # Set coordinate system
        self.ui.absolute_RADIO.toggled.connect(lambda:self.set_coordinate(self.ui.absolute_RADIO))
        self.ui.incremental_RADIO.toggled.connect(lambda:self.set_coordinate(self.ui.incremental_RADIO))

        # ~~~~~~~~~~~
        # TAB : Setup
        # ~~~~~~~~~~~

        # Port, first populate it then connect it (population done earlier)
        self.ui.refresh_ports_BTN.clicked.connect(self.refresh_ports)
        self.ui.port_DROPDOWN.currentIndexChanged.connect(self.set_port)

        self.ui.experiment_notes.editingFinished.connect(self.set_experiment_notes)

        # Set the microstepping value, default is 1
        self.ui.microstepping_DROPDOWN.currentIndexChanged.connect(self.set_microstepping)

        # Set the log file name
        self.date_string =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.date_string = self.date_string.replace(":","_") # Replace semicolons with underscores

        # Load and Save Settings
        self.ui.load_settings_BTN_2.clicked.connect(self.load_settings)
        self.ui.save_settings_BTN_2.clicked.connect(self.save_settings)

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
        self.ui.connect_BTN.clicked.connect(self.click_connect_button)
        self.ui.disconnect_BTN.clicked.connect(self.click_disconnect_button)

        # Send all the settings at once
        self.ui.send_all_BTN.clicked.connect(self.send_all)

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

    # Clean up this text
    def pause(self):
        active_pumps = self.get_active_pumps()
        pumps_2_run = ''.join(map(str,active_pumps))

        if self.ui.pause_BTN.text() == "Pause":
            self.statusBar().showMessage("You clicked PAUSE")
            testData = []
            cmd = "<PAUSE,BLAH," + pumps_2_run + ",BLAH,F,0.0,0.0,0.0>"
            testData.append(cmd)

            print("Sending PAUSE command..")
            thread = Thread(self.runTest, testData)
            thread.finished.connect(lambda:self.thread_finished(thread))
            thread.start()
            print("PAUSE command sent.")

            self.ui.pause_BTN.setText("Resume")

        elif self.ui.pause_BTN.text() == "Resume":
            self.statusBar().showMessage("You clicked RESUME")
            testData = []
            cmd = "<RESUME,BLAH," + pumps_2_run + ",BLAH,F,0.0,0.0,0.0>"
            testData.append(cmd)

            print("Sending RESUME command..")
            thread = Thread(self.runTest, testData)
            thread.finished.connect(lambda:self.thread_finished(thread))
            thread.start()
            print("RESUME command sent.")

            self.ui.pause_BTN.setText("Pause")

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


    def stop(self):
        self.statusBar().showMessage("You clicked STOP")
        cmd = "<STOP,BLAH,BLAH,BLAH,F,0.0,0.0,0.0>"

        print("Sending STOP command..")
        thread = Thread(self.send_single_command, cmd)
        thread.finished.connect(lambda:self.thread_finished(thread))
        thread.start()
        print("STOP command sent.")

    def jog(self, btn):
        print(f"Main> Jog Command. Forward To Syringe Channel Object")
        self.syringe_channel_1.jog(FORWARD)
        # self.statusBar().showMessage("You clicked JOG")
        # #self.serial.flushInput()
        # testData = []
        # active_pumps = self.get_active_pumps()
        # if len(active_pumps) > 0:
        #     pumps_2_run = ''.join(map(str,active_pumps))
        #
        #     one_jog = str(self.p1_setup_jog_delta_to_send)
        #     two_jog = str(self.p2_setup_jog_delta_to_send)
        #     three_jog = str(self.p3_setup_jog_delta_to_send)
        #
        #     if btn.text() == "Jog +":
        #         self.statusBar().showMessage("You clicked JOG +")
        #         f_cmd = "<RUN,DIST," + pumps_2_run +",0,F," + one_jog + "," + two_jog + "," + three_jog + ">"
        #         testData.append(f_cmd)
        #
        #         print("Sending JOG command..")
        #
        #         thread = Thread(self.runTest, testData)
        #         thread.finished.connect(lambda:self.thread_finished(thread))
        #         thread.start()
        #         print("JOG command sent.")
        #
        #     elif btn.text() == "Jog -":
        #         self.statusBar().showMessage("You clicked JOG -")
        #         b_cmd = "<RUN,DIST," + pumps_2_run +",0,B," + one_jog + "," + two_jog + "," + three_jog + ">"
        #         testData.append(b_cmd)
        #
        #         print("Sending JOG command..")
        #         thread = Thread(self.runTest, testData)
        #         thread.finished.connect(lambda:self.thread_finished(thread))
        #         thread.start()
        #         print("JOG command sent.")
        # else:
        #     self.statusBar().showMessage("No pumps enabled.")

    # ======================
    # FUNCTIONS : Setup
    # ======================

    def click_connect_button(self):
        self.statusBar().showMessage("You clicked CONNECT TO CONTROLLER")

        try:
            self.arduino.connect()
        except AttributeError:
            self.statusBar().showMessage("Please plug in the board and select a proper port, then press connect.")
        except CannotConnectException:
            self.statusBar().showMessage("Cannot connect to board. Try again..")

        self.statusBar().showMessage("Successfully connected to board.")

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
        self.ui.connect_BTN.setEnabled(True)
        self.ui.disconnect_BTN.setEnabled(False)


    # Populate the available ports
    # TODO: can this be moved to arduino file?
    def populate_ports(self):
        """
            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        print("Populating ports..")
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        self.ui.port_DROPDOWN.addItems(result)
        print("Ports have been populated.")

    # Refresh the list of ports
    # TODO: can this be moved to arduino file?
    def refresh_ports(self):
        self.statusBar().showMessage("You clicked REFRESH PORTS")
        self.ui.port_DROPDOWN.clear()
        self.populate_ports()
        self.set_port()

    # Set the port that is selected from the dropdown menu
    # TODO: find usage, move to arduino file
    def set_port(self):
        self.arduino.port = self.ui.port_DROPDOWN.currentText()

    # Set the microstepping amount from the dropdown menu
    # TODO: There is definitely a better way of updating different variables
    # after there is a change of some input from the user. need to figure out.
    def set_microstepping(self):
        self.microstepping = int(self.ui.microstepping_DROPDOWN.currentText())
        self.set_p1_units()
        self.set_p1_speed()
        self.set_p1_accel()
        self.set_p1_setup_jog_delta()
        self.set_p1_amount()

        self.set_p2_units()
        self.set_p2_speed()
        self.set_p2_accel()
        self.set_p2_setup_jog_delta()
        self.set_p2_amount()

        self.set_p3_units()
        self.set_p3_speed()
        self.set_p3_accel()
        self.set_p3_setup_jog_delta()
        self.set_p3_amount()

        print(self.microstepping)

    def set_experiment_notes(self):
        self.experiment_notes = self.ui.experiment_notes.text()

    # Set the name of the log file
    # Can probably delete
    def set_log_file_name(self):
        """
        Sets the file name for the current test run, enables us to log data to the file.

        Callback setter method from the 'self.ui.logFileNameInput' to set the
        name of the log file. The log file name is of the form
        label_Year-Month-Date hour_min_sec.txt
        """
        # Create a date string
        self.date_string =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Replace semicolons with underscores
        self.date_string = self.date_string.replace(":","_")
        self.log_file_name = self.ui.log_file_name_INPUT.text() + "_" + self.date_string + ".png"

    def save_settings(self):
        # TODO: if you cancel then it gives error, fix this
        # TODO: add comment
        name, _ = QFileDialog.getSaveFileName(self,'Save File', options=QFileDialog.DontUseNativeDialog)

        # Create a date string
        self.date_string =  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Replace semicolons with underscores
        self.date_string = self.date_string.replace(":","_")

        date_string = self.date_string

        # write all of the settings here
        ## Settings for pump 1
        p1_syringe 			= str(self.p1_syringe)
        p1_units 			= str(self.p1_units)
        p1_speed 			= str(self.p1_speed)
        p1_accel 			= str(self.p1_accel)
        p1_setup_jog_delta 	= str(self.p1_setup_jog_delta)

        ## Settings for pump 2
        p2_syringe 			= str(self.p2_syringe)
        p2_units 			= str(self.p2_units)
        p2_speed 			= str(self.p2_speed)
        p2_accel 			= str(self.p2_accel)
        p2_setup_jog_delta 	= str(self.p2_setup_jog_delta)

        ## Settings for pump 3
        p3_syringe 			= str(self.p3_syringe)
        p3_units 			= str(self.p3_units)
        p3_speed 			= str(self.p3_speed)
        p3_accel 			= str(self.p3_accel)
        p3_setup_jog_delta 	= str(self.p3_setup_jog_delta)

        ## Experiment Notes
        experiment_notes = self.experiment_notes

        text = []
        text.append("File name: " + name + ".txt" + "\n") 		# line 0
        text.append("Date time: " + date_string + "\n") 		# line 1

        text.append(":================================ \n") 	# line 2
        text.append("P1 Syrin: " + p1_syringe + "\n") 			# line 3
        text.append("P1 Units: " + p1_units + "\n") 			# line 4
        text.append("P1 Speed: " + p1_speed + "\n") 			# line 5
        text.append("P1 Accel: " + p1_accel + "\n") 			# line 6
        text.append("P1 Jog D: " + p1_setup_jog_delta + "\n") 	# line 7
        text.append(":================================ \n")		# line 8
        text.append("P2 Syrin: " + p2_syringe + "\n") 			# line 9
        text.append("P2 Units: " + p2_units + "\n") 			# line 10
        text.append("P2 Speed: " + p2_speed + "\n") 			# line 11
        text.append("P2 Accel: " + p2_accel + "\n") 			# line 12
        text.append("P2 Jog D: " + p2_setup_jog_delta + "\n") 	# line 13
        text.append(":================================ \n") 	# line 14
        text.append("P3 Syrin: " + p3_syringe + "\n") 			# line 15
        text.append("P3 Units: " + p3_units + "\n") 			# line 16
        text.append("P3 Speed: " + p3_speed + "\n") 			# line 17
        text.append("P3 Accel: " + p3_accel + "\n") 			# line 18
        text.append("P3 Jog D: " + p3_setup_jog_delta + "\n") 	# line 19
        text.append("Exp Note: " + experiment_notes)			# line 20

        if name:
            with open(name + ".txt", 'w') as f:
                f.writelines(text)
                self.statusBar().showMessage("Settings saved in " + name + ".txt")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def load_settings(self):
        # need to make name an tuple otherwise i had an error and app crashed
        name, _ = QFileDialog.getOpenFileName(self, 'Open File', options=QFileDialog.DontUseNativeDialog, filter = "Text (*.txt)")

        if name:
            with open(name, 'r') as f:
                text = f.readlines()
                # here is where you load all of your variables
                # reformatting the text
                text = [line.split(':')[-1].strip('\n')[1:] for line in text]
                fname = text[0]
                date_string = text[1]

                p1_syringe 			= text[3]
                p1_units 			= text[4]
                p1_speed 			= text[5]
                p1_accel 			= text[6]
                p1_setup_jog_delta 	= text[7]

                p2_syringe 			= text[9]
                p2_units 			= text[10]
                p2_speed 			= text[11]
                p2_accel 			= text[12]
                p2_setup_jog_delta 	= text[13]

                p3_syringe 			= text[15]
                p3_units 			= text[16]
                p3_speed 			= text[17]
                p3_accel 			= text[18]
                p3_setup_jog_delta 	= text[19]

                experiment_notes 	= text[20]

                #print(fname, date_string, p1_syringe, p1_units, p1_speed, p1_accel, p1_setup_jog_delta)

            # Here we are setting all of the values as given by the settings file
            p1_syringe_index = self.ui.p1_syringe_DROPDOWN.findText(p1_syringe, QtCore.Qt.MatchFixedString)
            self.ui.p1_syringe_DROPDOWN.setCurrentIndex(p1_syringe_index)
            p1_units_index = self.ui.p1_units_DROPDOWN.findText(p1_units, QtCore.Qt.MatchFixedString)
            self.ui.p1_units_DROPDOWN.setCurrentIndex(p1_units_index)
            self.ui.p1_speed_INPUT.setValue(float(p1_speed))
            self.ui.p1_accel_INPUT.setValue(float(p1_accel))

            AllItems = [self.ui.p1_setup_jog_delta_INPUT.itemText(i) for i in range(self.ui.p1_setup_jog_delta_INPUT.count())]

            p1_setup_jog_delta_index = self.ui.p1_setup_jog_delta_INPUT.findText(p1_setup_jog_delta, QtCore.Qt.MatchFixedString)
            self.ui.p1_setup_jog_delta_INPUT.setCurrentIndex(p1_setup_jog_delta_index)


            p2_syringe_index = self.ui.p2_syringe_DROPDOWN.findText(p2_syringe, QtCore.Qt.MatchFixedString)
            self.ui.p2_syringe_DROPDOWN.setCurrentIndex(p2_syringe_index)
            p2_units_index = self.ui.p2_units_DROPDOWN.findText(p2_units, QtCore.Qt.MatchFixedString)
            self.ui.p2_units_DROPDOWN.setCurrentIndex(p2_units_index)
            self.ui.p2_speed_INPUT.setValue(float(p2_speed))
            self.ui.p2_accel_INPUT.setValue(float(p2_accel))

            p2_setup_jog_delta_index = self.ui.p2_setup_jog_delta_INPUT.findText(p2_setup_jog_delta, QtCore.Qt.MatchFixedString)
            self.ui.p2_setup_jog_delta_INPUT.setCurrentIndex(p2_setup_jog_delta_index)

            p3_syringe_index = self.ui.p3_syringe_DROPDOWN.findText(p3_syringe, QtCore.Qt.MatchFixedString)
            self.ui.p3_syringe_DROPDOWN.setCurrentIndex(p3_syringe_index)
            p3_units_index = self.ui.p3_units_DROPDOWN.findText(p3_units, QtCore.Qt.MatchFixedString)
            self.ui.p3_units_DROPDOWN.setCurrentIndex(p3_units_index)
            self.ui.p3_speed_INPUT.setValue(float(p3_speed))
            self.ui.p3_accel_INPUT.setValue(float(p3_accel))

            p3_setup_jog_delta_index = self.ui.p3_setup_jog_delta_INPUT.findText(p3_setup_jog_delta, QtCore.Qt.MatchFixedString)
            self.ui.p3_setup_jog_delta_INPUT.setCurrentIndex(p3_setup_jog_delta_index)

            self.ui.experiment_notes.setText(experiment_notes)

            self.statusBar().showMessage("Settings loaded from: " + text[1])
        else:
            self.statusBar().showMessage("No file selected.")

    # Populate the microstepping amounts for the dropdown menu
    def populate_microstepping(self):
        self.microstepping_values = ['1', '2', '4', '8', '16', '32']
        self.ui.microstepping_DROPDOWN.addItems(self.microstepping_values)
        self.microstepping = 1

    # Populate the list of possible syringes to the dropdown menus
    def populate_syringe_sizes(self):
        # labels for each syringe
        self.syringe_options = ["BD 1 mL", "BD 3 mL", "BD 5 mL", "BD 10 mL", "BD 20 mL", "BD 30 mL", "BD 60 mL", "500 mL"]

        # volumina of the syringes in mL
        self.syringe_volumes = [1, 3, 5, 10, 20, 30, 60, 500]

        # circle areas of the syringes in mm^2
        self.syringe_areas = [17.34206347, 57.88559215, 112.9089185, 163.539454, 285.022957, 366.0961536, 554.0462538, 3631.681168]

        self.ui.p1_syringe_DROPDOWN.addItems(self.syringe_options)
        self.ui.p2_syringe_DROPDOWN.addItems(self.syringe_options)
        self.ui.p3_syringe_DROPDOWN.addItems(self.syringe_options)

    # Set Px syringe
    def set_p1_syringe(self):
        self.p1_syringe = self.ui.p1_syringe_DROPDOWN.currentText()
        self.p1_syringe_area = self.syringe_areas[self.syringe_options.index(self.p1_syringe)]
        self.display_p1_syringe()

        self.set_p1_units()
        self.set_p1_speed()
        self.set_p1_accel()
        self.set_p1_setup_jog_delta()
        self.set_p1_amount()

    def set_p2_syringe(self):
        self.p2_syringe = self.ui.p2_syringe_DROPDOWN.currentText()
        self.p2_syringe_area = self.syringe_areas[self.syringe_options.index(self.p2_syringe)]
        self.display_p2_syringe()

        self.set_p2_units()
        self.set_p2_speed()
        self.set_p2_accel()
        self.set_p2_setup_jog_delta()
        self.set_p2_amount()

    def set_p3_syringe(self):
        self.p3_syringe = self.ui.p3_syringe_DROPDOWN.currentText()
        self.p3_syringe_area = self.syringe_areas[self.syringe_options.index(self.p3_syringe)]
        self.display_p3_syringe()

        self.set_p3_units()
        self.set_p3_speed()
        self.set_p3_accel()
        self.set_p3_setup_jog_delta()
        self.set_p3_amount()

    # Set Px units
    def set_p1_units(self):
        self.p1_units = self.ui.p1_units_DROPDOWN.currentText()

        length = self.p1_units.split("/")[0]
        self.ui.p1_units_LABEL_2.setText(length)

        self.set_p1_speed()
        self.set_p1_accel()
        self.set_p1_setup_jog_delta()
        self.set_p1_amount()

    def set_p2_units(self):
        self.p2_units = self.ui.p2_units_DROPDOWN.currentText()

        length = self.p2_units.split("/")[0]
        self.ui.p2_units_LABEL_2.setText(length)

        self.set_p2_speed()
        self.set_p2_accel()
        self.set_p2_setup_jog_delta()
        self.set_p2_amount()

    def set_p3_units(self):
        self.p3_units = self.ui.p3_units_DROPDOWN.currentText()

        length = self.p3_units.split("/")[0]
        self.ui.p3_units_LABEL_2.setText(length)

        self.set_p3_speed()
        self.set_p3_accel()
        self.set_p3_setup_jog_delta()
        self.set_p3_amount()


    def populate_pump_units(self):
        self.units = ['mm/s', 'mL/s', 'mL/hr', 'µL/hr']
        self.ui.p1_units_DROPDOWN.addItems(self.units)
        self.ui.p2_units_DROPDOWN.addItems(self.units)
        self.ui.p3_units_DROPDOWN.addItems(self.units)

    def populate_pump_jog_delta(self):
        self.jog_delta = ['0.01', '0.1', '1.0', '10.0']
        self.ui.p1_setup_jog_delta_INPUT.addItems(self.jog_delta)
        self.ui.p2_setup_jog_delta_INPUT.addItems(self.jog_delta)
        self.ui.p3_setup_jog_delta_INPUT.addItems(self.jog_delta)

    # Set Px speed
    def set_p1_speed(self):
        self.p1_speed = self.ui.p1_speed_INPUT.value()
        self.ui.p1_units_LABEL.setText(str(self.p1_speed) + " " + self.ui.p1_units_DROPDOWN.currentText())
        self.p1_speed_to_send = self.convert_speed(self.p1_speed, self.p1_units, self.p1_syringe_area, self.microstepping)

    def set_p2_speed(self):
        self.p2_speed = self.ui.p2_speed_INPUT.value()
        self.ui.p2_units_LABEL.setText(str(self.p2_speed) + " " + self.ui.p2_units_DROPDOWN.currentText())
        self.p2_speed_to_send = self.convert_speed(self.p2_speed, self.p2_units, self.p2_syringe_area, self.microstepping)

    def set_p3_speed(self):
        self.p3_speed = self.ui.p3_speed_INPUT.value()
        self.ui.p3_units_LABEL.setText(str(self.p3_speed) + " " + self.ui.p3_units_DROPDOWN.currentText())
        self.p3_speed_to_send = self.convert_speed(self.p3_speed, self.p3_units, self.p3_syringe_area, self.microstepping)

    # Set Px accel
    def set_p1_accel(self):
        self.p1_accel = self.ui.p1_accel_INPUT.value()
        self.p1_accel_to_send = self.convert_accel(self.p1_accel, self.p1_units, self.p1_syringe_area, self.microstepping)

    def set_p2_accel(self):
        self.p2_accel = self.ui.p2_accel_INPUT.value()
        self.p2_accel_to_send = self.convert_accel(self.p2_accel, self.p2_units, self.p2_syringe_area, self.microstepping)

    def set_p3_accel(self):
        self.p3_accel = self.ui.p3_accel_INPUT.value()
        self.p3_accel_to_send = self.convert_accel(self.p3_accel, self.p3_units, self.p3_syringe_area, self.microstepping)

    # Set Px jog delta (setup)
    def set_p1_setup_jog_delta(self):
        self.p1_setup_jog_delta = self.ui.p1_setup_jog_delta_INPUT.currentText()
        self.p1_setup_jog_delta = float(self.ui.p1_setup_jog_delta_INPUT.currentText())
        self.p1_setup_jog_delta_to_send = self.convert_displacement(self.p1_setup_jog_delta, self.p1_units, self.p1_syringe_area, self.microstepping)

    def set_p2_setup_jog_delta(self):
        self.p2_setup_jog_delta = float(self.ui.p2_setup_jog_delta_INPUT.currentText())
        self.p2_setup_jog_delta_to_send = self.convert_displacement(self.p2_setup_jog_delta, self.p2_units, self.p2_syringe_area, self.microstepping)

    def set_p3_setup_jog_delta(self):
        self.p3_setup_jog_delta = float(self.ui.p3_setup_jog_delta_INPUT.currentText())
        self.p3_setup_jog_delta_to_send = self.convert_displacement(self.p3_setup_jog_delta, self.p3_units, self.p3_syringe_area, self.microstepping)

    # Send Px settings
    def send_p1_settings(self):
        self.statusBar().showMessage("You clicked SEND P1 SETTINGS")
        self.p1_settings = []
        self.p1_settings.append("<SETTING,SPEED,1," + str(self.p1_speed_to_send) + ",F,0.0,0.0,0.0>")
        self.p1_settings.append("<SETTING,ACCEL,1," + str(self.p1_accel_to_send) + ",F,0.0,0.0,0.0>")
        self.p1_settings.append("<SETTING,DELTA,1," + str(self.p1_setup_jog_delta_to_send) + ",F,0.0,0.0,0.0>")

        print("Sending P1 SETTINGS..")
        thread = Thread(self.runTest, self.p1_settings)
        thread.finished.connect(lambda:self.thread_finished(thread))
        thread.start()
        print("P1 SETTINGS sent.")

    def send_p2_settings(self):
        self.statusBar().showMessage("You clicked SEND P2 SETTINGS")
        self.p2_settings = []
        self.p2_settings.append("<SETTING,SPEED,2," + str(self.p2_speed_to_send) + ",F,0.0,0.0,0.0>")
        self.p2_settings.append("<SETTING,ACCEL,2," + str(self.p2_accel_to_send) + ",F,0.0,0.0,0.0>")
        self.p2_settings.append("<SETTING,DELTA,2," + str(self.p2_setup_jog_delta_to_send) + ",F,0.0,0.0,0.0>")

        print("Sending P2 SETTINGS..")
        thread = Thread(self.runTest, self.p2_settings)
        thread.finished.connect(lambda:self.thread_finished(thread))
        thread.start()
        print("P2 SETTINGS sent.")

    def send_p3_settings(self):
        self.statusBar().showMessage("You clicked SEND P3 SETTINGS")
        self.p3_settings = []
        self.p3_settings.append("<SETTING,SPEED,3," + str(self.p3_speed_to_send) + ",F,0.0,0.0,0.0>")
        self.p3_settings.append("<SETTING,ACCEL,3," + str(self.p3_accel_to_send) + ",F,0.0,0.0,0.0>")
        self.p3_settings.append("<SETTING,DELTA,3," + str(self.p3_setup_jog_delta_to_send) + ",F,0.0,0.0,0.0>")

        print("Sending P3 SETTINGS..")
        thread = Thread(self.runTest, self.p3_settings)
        thread.finished.connect(lambda:self.thread_finished(thread))
        thread.start()
        print("P3 SETTINGS sent.")

    # Send all settings
    def send_all(self):
        self.statusBar().showMessage("You clicked SEND ALL SETTINGS")

        self.settings = []
        self.settings.append("<SETTING,SPEED,1,"+str(self.p1_speed_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,ACCEL,1,"+str(self.p1_accel_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,DELTA,1,"+str(self.p1_setup_jog_delta_to_send)+",F,0.0,0.0,0.0>")

        self.settings.append("<SETTING,SPEED,2,"+str(self.p2_speed_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,ACCEL,2,"+str(self.p2_accel_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,DELTA,2,"+str(self.p2_setup_jog_delta_to_send)+",F,0.0,0.0,0.0>")

        self.settings.append("<SETTING,SPEED,3,"+str(self.p3_speed_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,ACCEL,3,"+str(self.p3_accel_to_send)+",F,0.0,0.0,0.0>")
        self.settings.append("<SETTING,DELTA,3,"+str(self.p3_setup_jog_delta_to_send)+",F,0.0,0.0,0.0>")

        print("Sending all settings..")
        self.arduino.thread_send_commands(self.settings)

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





    #============================


    def listening(self):
        startMarker = self.startMarker
        midMarker = self.midMarker
        endMarker = self.endMarker
        posMarker = ord('?')
        i = 0

        while (True):
            self.serial.flushInput()
            x = "z"
            ck = ""
            isDisplay = "asdf"
            while self.serial.inWaiting() == 0:
                pass
            while  not x or ord(x) != startMarker:
                x = self.serial.read()
                #if ord(x) == posMarker:
                #	return self.get_position()
            while ord(x) != endMarker:
                if ord(x) == midMarker:
                    i += 1
                    print(ck)
                    #isDisplay = ck
                    #if i % 100 == 0:
                    #	self.ui.p1_absolute_DISP.display(ck)
                    ck = ""
                    x = self.serial.read()

                if ord(x) != startMarker:
                    ck = ck + x.decode()

                x = self.serial.read()
                # TODO
            #if isDisplay == "START":
            #	print("This is ck: " + ck)
                #motorID = int(ck)
                #self.is_p1_running = True
                #run thread(self.display_position, motorID)

                #toDisp = self.steps2mm(float(ck))
                #print("Pump num " + toDisp + " is now running.")i
                #self.ui.p1_absolute_DISP.display(toDisp)
                #isDisplay = ""

            #self.serial.flushInput()
            #print(self.serial.read(self.serial.inWaiting()).decode('ascii'))
            print(ck)
            print("\n")

    # TODO
    # def display_position(self, motorID):
    # 	if motorID == 1:

    # 		seconds = 0
    # 		p1_speed = self.p1_speed_to_send
    # 		p1_dist = 0
    # 		p1_time = p1_dist/p1_speed

    # 		time_start = time.start()
    # 		while self.is_p1_running:
    # 			pass



    def get_position(self):
        ck = ""
        x = self.serial.read()

        while ord(x) != self.endMarker:
            if ord(x) == self.midMarker:
                print(ck)
                ck = ""
                x = self.serial.read()
            ck = ck + x.decode()
            x = self.serial.read()
        print(ck)
        return (ck)



    def closeEvent(self, event):
        try:
            #self.global_listener_thread.stop()
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
