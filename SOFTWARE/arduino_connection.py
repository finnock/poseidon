import serial
import time
from thread import Thread


class CannotConnectException(Exception):
    pass


class Arduino:
    def __init__(self):
        # Declaring start, mid, and end marker for sending code to Arduino
        self.START_MARKER = 60   # <
        self.END_MARKER = 62  	# ,F,0.0>
        self.MID_MARKER = 44 	# ,

        self.port = None
        self.serial = None
        self.connected = False

    # Connect to the Arduino Board
    def connect(self):
        try:
            port_declared = self.port in vars()
            try:
                self.serial = serial.Serial()
                self.serial.port = self.port
                self.serial.baudrate = 230400
                self.serial.parity = serial.PARITY_NONE
                self.serial.stopbits = serial.STOPBITS_ONE
                self.serial.bytesize = serial.EIGHTBITS
                self.serial.timeout = 1
                self.serial.open()

                # This is a thread that always runs and listens to commands from the Arduino
                # TODO: figure out how this is usable! Sounds good!
                #self.global_listener_thread = Thread(self.listening)
                #self.global_listener_thread.finished.connect(lambda:self.self.thread_finished(self.global_listener_thread))
                #self.global_listener_thread.start()


                # TODO: figure out if 3s is necessary
                # TODO: possible thread?
                time.sleep(3)

                self.connected = True
            except:
                self.connected = False
                raise CannotConnectException
        except AttributeError:
            self.connected = False

    # Disconnect from the Arduino board
    # TODO: figure out how to handle error.. (which error?)
    def disconnect(self):
        print("Arduino> Disconnecting from board..")
        #self.global_listener_thread.stop()
        time.sleep(3)
        self.serial.close()
        self.connected = False
        print("Arduino> Board has been disconnected")

    def send_commands(self, commands):
        thread = Thread(self.send_commands_helper, commands)
        thread.finished.connect(lambda: self.thread_finished_helper(thread))
        thread.start()

    def send_commands_helper(self, commands):
        for command in commands:
            # Send the command via the serial connection
            self.serial.write(command.encode())
            self.serial.flushInput()
            print("Arduino> Send Command: " + command)

            # Wait for reply
            while self.serial.inWaiting() == 0:
                pass

            # Receive data via serial connection
            data_received = self.receive_position_arduino()
            print("Arduino> Receive Reply: " + data_received)

            # Short sleep time for serial connection to reset
            time.sleep(0.1)

        print("Arduino> Send and receive complete\n\n")

    def thread_finished_helper(self, thread):
        thread.stop()
        print(f"Arduino> Thread finished")

    def send_manual_arduino_command(self, operation, operation_type, motors, value, direction, steps):
        command = f"<{operation},{operation_type},{motors},{value},{direction},{steps[0]},{steps[1]},{steps[2]}>"
        print(f"Arduino> Executing: {command}")
        self.send_commands([command])

    def receive_position_arduino(self):
        result = ""
        current_marker = None  # any value that is not an end- or startMarker

        # wait for the start character
        while ord(current_marker) != self.START_MARKER:
            current_marker = self.serial.read()

        # save data until the end marker is found
        while ord(current_marker) != self.END_MARKER:
            if ord(current_marker) == self.MID_MARKER:
                # print(f"Arduino> Receive Position Midmarker: {result}")
                # self.ui.p1_absolute_DISP.display(result)
                # TODO move to UI
                result = ""
                current_marker = self.serial.read()

            if ord(current_marker) != self.START_MARKER:
                # print(current_marker)
                result = result + current_marker.decode()

            current_marker = self.serial.read()
        return (result)
