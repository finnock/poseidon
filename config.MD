# Settings

All settings are saved to an ini file using the configparser module. They are grouped into sections.

## Serial `connection` Settings

| Setting         | Description                                                 |
|-----------------|-------------------------------------------------------------|
| `com-port`:     | The port to use for the serial connection                   |
| `baudrate`:     | The baudrate used for the connection. Default is 230400     |
| `microsteps`:   | The number of microsteps setup on the CNC-Shield            |
| `auto-connect`: | Weather the system should auto connect to the Arduino board |

## `misc` Settings

| Setting        | Description                                                        |
|----------------|--------------------------------------------------------------------|
| `fullscreen`   | Weather the app should automatically be started in fullscreen mode |
| `jog-distance` | The distance for each jog movement given in mm                     |
| `jog-speed`    | The speed for the jog movement, given in mm/s                      |

## `syringe-channel-#` Settings

Where `#` is the number corresponding to the syringe channel (1, 2, 3)

| Setting             | Description                                                             |
|---------------------|-------------------------------------------------------------------------|
| `size`              | The syringe size given as text. Options are hardcoded right now (todo!) |
| `speed`             | The dispensing speed, right now fixed to mL/h (todo!)                   |
| `volume`            | The overall volume to be extruded in one sequence run                   |
| `acceleration`      | The acceleration for the channel, given in steps/s²                     |
| `sequence-position` | The position in the sequence queue                                      |