FORWARD = 1
BACKWARD = 0

class SyringeChannel:

    def __init__(self, channel_number):
        self.channel_number = channel_number

    def jog(self, direction):
