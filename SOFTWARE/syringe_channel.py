from thread import Thread
import time
import serial

FORWARD = 1
BACKWARD = 0

class SyringeChannel:

    def __init__(self, main, channel_number):
        self.main = main
        self.channel_number = channel_number

    def jog(self, direction):
        print(f"SyringeChannel> Send Test Jog Command")
        self.main.arduino.send_manual_arduino_command('RUN', 'DIST', 1, 0, direction, [8000, 8000, 8000])
