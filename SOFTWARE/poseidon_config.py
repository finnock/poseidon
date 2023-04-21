import configparser
import os
CONFIG_FILENAME = 'config.ini'


class PoseidonConfig:

    @staticmethod
    def default_config():
        config = configparser.ConfigParser()

        config['connection'] = {
            'com-port': '',
            'baudrate': 230400,
            'microsteps': 32,
            'auto-connect': False
        }

        config['misc'] = {
            'fullscreen': False,
            'jog-distance': 10,
            'jog-speed': 10,
        }

        config['syringe-channel-1'] = {
            # TODO: get size from dynamically created list / file / whatever
            'size': '500 mL',
            'speed': 0,
            'volume': 0,
            'acceleration': 5,
            'sequence-position': 1
        }

        config['syringe-channel-2'] = config['syringe-channel-1']
        config['syringe-channel-2']['sequence-position'] = '2'
        config['syringe-channel-3'] = config['syringe-channel-1']
        config['syringe-channel-3']['sequence-position'] = '3'

        return config

    # Load config file
    @staticmethod
    def load_config():
        config = configparser.ConfigParser()

        # check if config_file exists
        if not os.path.isfile(CONFIG_FILENAME):
            # No config file found. Populate temporary config object with settings and create file with it
            new_config = PoseidonConfig.default_config()
            with open(CONFIG_FILENAME, 'w') as configfile:
              new_config.write(configfile)

        # TODO: check if it's valid by checking for necessary config settings (optional)

        # read config file
        config.read(CONFIG_FILENAME)

        return config

    @staticmethod
    def save_config(config):
        with open(CONFIG_FILENAME, 'w') as configfile:
            config.write(configfile)
