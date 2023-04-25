import serial
import time
import glob
import sys
import traceback
from thread import Thread


class CannotConnectException(Exception):
    pass


class Arduino:
    def __init__(self, config):
        # Declaring start, mid, and end marker for sending code to Arduino
        self.START_MARKER = 60  # <
        self.MID_MARKER = 44 	# ,
        self.END_MARKER = 62    # >

        self.config = config
        self.serial = None
        self.connected = False

        # total number of steps per revolution
        self.steps_per_revolution = 200
        self.mm_per_revolution = 2
        self.motors_enabled = False
        self.motors_changed_callback = None

    # Connect to the Arduino Board
    def connect(self):
        try:
            self.serial = serial.Serial()
            self.serial.port = self.config['connection']['com-port']
            self.serial.baudrate = self.config['connection']['baudrate']
            self.serial.parity = serial.PARITY_NONE
            self.serial.stopbits = serial.STOPBITS_ONE
            self.serial.bytesize = serial.EIGHTBITS
            self.serial.timeout = 1
            self.serial.open()

            print(f"Arduino> Connect to port: {self.config['connection']['com-port']}")

            # This is a thread that always runs and listens to commands from the Arduino
            self.global_listener_thread = Thread(self.serial_listener)
            self.global_listener_thread.finished.connect(lambda: self.thread_finished_helper(self.global_listener_thread))
            self.global_listener_thread.start()


            # TODO: figure out if 3s is necessary
            # TODO: move to thread and update UI when received success message
            time.sleep(2)
            self.enable_motors()
            time.sleep(1)

            self.connected = True
        except Exception as exc:
            self.connected = False
            traceback.print_exc(exc)
            raise CannotConnectException

    # Disconnect from the Arduino board
    # TODO: figure out how to handle error.. (which error?)
    def disconnect(self):
        print("Arduino> Disconnecting from board..")
        self.disable_motors()
        time.sleep(2)
        self.global_listener_thread.stop()
        self.serial.close()
        self.connected = False
        print("Arduino> Board has been disconnected")

    @staticmethod
    def discover_ports():
        """
            raises EnvironmentError
                On unsupported or unknown platforms
            returns
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            # For speed reason capped to range(50). Increase to 256 if needed.
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

        if len(result) > 0:
            return result
        else:
            raise EnvironmentError('No suitable ports found')

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

        print("Arduino> Send complete\n\n")

    def thread_finished_helper(self, thread):
        thread.stop()
        print(f"Arduino> Thread finished")

    def send_manual_arduino_command(self, operation, operation_type, motors, value, direction, steps):
        command = f"<{operation},{operation_type},{motors},{value},{direction},{steps[0]},{steps[1]},{steps[2]}>"
        print(f"Arduino> Executing: {command}")
        self.send_commands([command])

    def return_manual_arduino_command(self, operation, operation_type, motors, value, direction, steps):
        command = f"<{operation},{operation_type},{motors},{value},{direction},{steps[0]},{steps[1]},{steps[2]}>"
        return command

    def serial_listener(self):
        while self.global_listener_thread.runs:
            line = self.serial.readline()
            if len(line) > 0:
                line = line.decode('ascii').replace('\r\n', '')
                print(f"Serial> {line}")


    # #########################################################
    # Hardware Abstraction Functions
    #
    # Expose motor functionality to software on API level
    # #########################################################

    def jog(self, motor_channel, direction, distance_in_mm, speed_in_mm_per_s):
        """ Jogs the given channel in a given direction and distance

        Parameters
        ----------
        motor_channel : int
            The channel which should be manipulated (1..3)
        direction : string
            The direction in which the motor should be moved. 1 for FORWARD, 0 for BACKWARD.
        distance_in_mm : float
            The distance by which the motor should be moved, given in mm.
        """

        distances = [0.0, 0.0, 0.0]
        mm_per_rotation = float(self.config['misc']['mm-per-rotation'])
        steps_per_rotation = float(self.config['misc']['steps-per-rotation'])
        microsteps_per_step = float(self.config['misc']['microsteps'])
        distances[motor_channel - 1] = distance_in_mm / mm_per_rotation * steps_per_rotation * microsteps_per_step
        speed = speed_in_mm_per_s / mm_per_rotation * steps_per_rotation * microsteps_per_step

        # TODO: Add speed setting change and waiter? thread?
        speed_command = self.return_manual_arduino_command('SETTING', 'SPEED', motor_channel, speed, 'F', [0,0,0])
        jog_command = self.return_manual_arduino_command('RUN', 'DIST', motor_channel, 1, direction, distances)
        self.send_commands([speed_command, jog_command])

    def enable_motors(self):
        """ Enables all motors """
        self.send_manual_arduino_command('SETTING', 'ENABLE', 1, 1, "F", [0.0, 0.0, 0.0])
        self.motors_enabled = True
        self.motors_changed_callback()

    def disable_motors(self):
        """ Disables all motors """
        self.send_manual_arduino_command('SETTING', 'ENABLE', 1, 0, "F", [0.0, 0.0, 0.0])
        self.motors_enabled = False
        self.motors_changed_callback()

    def toggle_motors(self):
        """ Toggles all motors """
        if self.motors_enabled:
            self.disable_motors()
        else:
            self.enable_motors()
        self.motors_changed_callback()

    def stop_movement(self):
        self.send_manual_arduino_command("STOP", "0", "0", "0", "F", [0, 0, 0])

    def pause_movement(self):
        self.send_manual_arduino_command("PAUSE", "0", "0", "0", "F", [0, 0, 0])

    def resume_movement(self):
        self.send_manual_arduino_command("RESUME", "0", "0", "0", "F", [0, 0, 0])

    def zero(self):
        # TODO: add possibility zero only single channel
        self.send_manual_arduino_command("ZERO", "0", "0", "0", "F", [0, 0, 0])