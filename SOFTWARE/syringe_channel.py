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
        self.absolute_position = 0
        self.remaining_volume = 0
        self.running = False
        self.acceleration = 5

    def get_run_parameters(self):
        speed_in_ml_per_h = float(self.config[f"syringe-channel-{self.channel_number}"]['speed'])
        volume_in_ml = float(self.config[f"syringe-channel-{self.channel_number}"]['volume'])

        speed_in_ml_per_s = speed_in_ml_per_h / 3600
        speed_in_mm_per_s = self.ml_to_mm(speed_in_ml_per_s)
        distance_in_mm = self.ml_to_mm(volume_in_ml)

        new_position = self.absolute_position + self.mm_to_steps(distance_in_mm)

        return new_position, self.mm_to_steps(speed_in_mm_per_s)

    def get_jog_parameters(self, direction):
        speed_in_mm_per_s = float(self.config['misc']['jog-speed'])
        distance_in_mm = float(self.config['misc']['jog-distance'])

        new_position = self.absolute_position + self.mm_to_steps(distance_in_mm) * direction

        return new_position, self.mm_to_steps(speed_in_mm_per_s)

    def mm_to_steps(self, mm):
        mm_per_rotation = float(self.config['misc']['mm-per-rotation'])
        steps_per_rotation = float(self.config['misc']['steps-per-rotation'])
        microsteps_per_step = float(self.config['misc']['microsteps'])

        return mm / mm_per_rotation * steps_per_rotation * microsteps_per_step

    def steps_to_mm(self, steps):
        mm_per_rotation = float(self.config['misc']['mm-per-rotation'])
        steps_per_rotation = float(self.config['misc']['steps-per-rotation'])
        microsteps_per_step = float(self.config['misc']['microsteps'])

        return steps / microsteps_per_step / steps_per_rotation * mm_per_rotation

    def steps_to_ml(self, steps):
        mm_per_rotation = float(self.config['misc']['mm-per-rotation'])
        steps_per_rotation = float(self.config['misc']['steps-per-rotation'])
        microsteps_per_step = float(self.config['misc']['microsteps'])

        return self.mm_to_ml(steps / microsteps_per_step / steps_per_rotation * mm_per_rotation)

    def ml_to_mm(self, ml):
        return ml / (self.syringe_area / 1000)

    def mm_to_ml(self, mm):
        return mm * (self.syringe_area / 1000)


