FORWARD = 'F'
BACKWARD = 'B'


class SyringeChannel:

    def __init__(self, main, channel_number):
        self.main = main
        self.channel_number = channel_number
        self.syringe_size = ''
        self.syringe_area = 0
        self.syringe_total_volume = 0
        self.volume_unit = 'mL'
        self.speed_unit = 'mL/h'
        self.sequence_position = channel_number
        # Absolute position is None since it is not yet zeroed
        self.absolute_position = None
        self.remaining_volume = 0
        self.acceleration = 5
