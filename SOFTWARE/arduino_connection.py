import serial
import time
from thread import Thread


class CannotConnectException(Exception):
    pass


class Arduino:
    def __init__(self):
        # Declaring start, mid, and end marker for sending code to Arduino
        self.START_MARKER = 60  # <
        self.MID_MARKER = 44 	# ,
        self.END_MARKER = 62    # >

        self.port = None
        self.serial = None
        self.connected = False

        self.steps = None
        self.steps_per_mm = None
        self.motors_enabled = False
        self.motors_changed = None

    # Connect to the Arduino Board
    def connect(self):
        try:
            self.port in vars()
            try:
                self.serial = serial.Serial()
                self.serial.port = self.port
                self.serial.baudrate = 230400
                self.serial.parity = serial.PARITY_NONE
                self.serial.stopbits = serial.STOPBITS_ONE
                self.serial.bytesize = serial.EIGHTBITS
                self.serial.timeout = 1
                self.serial.open()

                print(f"Arduino> Connect to port: {self.port}")

                # This is a thread that always runs and listens to commands from the Arduino
                # TODO: figure out how this is usable! Sounds good!
                self.global_listener_thread = Thread(self.serial_listener)
                self.global_listener_thread.finished.connect(lambda:self.thread_finished(self.global_listener_thread))
                self.global_listener_thread.start()


                # TODO: figure out if 3s is necessary
                # TODO: possible thread?
                time.sleep(2)
                self.enable_motors()
                time.sleep(1)

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

    def serial_listener(self):
        while True:
            line = self.serial.readline()
            if len(line) > 0:
                print(line.decode('ascii').replace('\r\n', ''))


    # #########################################################
    # Hardware Abstraction Functions
    #
    # Expose motor functionality to software on API level
    # #########################################################

    def jog(self, motor_channel, direction, distance):
        """ Jogs the given channel in a given direction and distance

        Parameters
        ----------
        motor_channel : int
            The channel which should be manipulated (1..3)
        direction : string
            The direction in which the motor should be moved. 1 for FORWARD, 0 for BACKWARD.
        distance : float
            The distance by which the motor should be moved, given in mm.
        """

        distances = [0.0, 0.0, 0.0]
        distances[motor_channel - 1] = distance * 200 * 32

        self.send_manual_arduino_command('RUN', 'DIST', "1", 1, direction, distances)

    def enable_motors(self):
        """ Enables all motors """
        self.send_manual_arduino_command('SETTING', 'ENABLE', 1, 1, "F", [0.0, 0.0, 0.0])
        self.motors_enabled = True
        self.motors_changed()

    def disable_motors(self):
        """ Disables all motors """
        self.send_manual_arduino_command('SETTING', 'ENABLE', 1, 0, "F", [0.0, 0.0, 0.0])
        self.motors_enabled = False
        self.motors_changed()

    def toggle_motors(self):
        """ Toggles all motors """
        if self.motors_enabled:
            self.disable_motors()
        else:
            self.enable_motors()
        self.motors_changed()

