FORWARD = 'F'
BACKWARD = 'B'


class SyringeChannel:

    def __init__(self, main, channel_number):
        self.main = main
        self.channel_number = channel_number

    def jog(self, direction):
        self.main.arduino.jog(self.channel_number, direction, 1)
