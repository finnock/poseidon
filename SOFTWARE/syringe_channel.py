FORWARD = 'F'
BACKWARD = 'B'


class SyringeChannel:

    def __init__(self, main, channel_number, config):
        self.main = main
        self.channel_number = channel_number
        self.config = config


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

    def get_run_parameters(self):
        speed_in_ml_per_h = float(self.config[f"syringe-channel-{self.channel_number}"]['speed'])
        volume_in_ml = float(self.config[f"syringe-channel-{self.channel_number}"]['volume'])

        speed_in_ml_per_s = speed_in_ml_per_h / 3600
        ml_per_mm = self.syringe_area / 1000
        speed_in_mm_per_s = speed_in_ml_per_s / ml_per_mm

        distance_in_mm = volume_in_ml / ml_per_mm

        return distance_in_mm, speed_in_mm_per_s
