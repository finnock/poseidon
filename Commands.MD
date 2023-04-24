## New Commands to Arduino

### Overview

No settings are stored to the arduino (unless we find a way to save permanently).
All infos needed for the operation are transported directly with the command.

 - `MOVE`: Move
 - `ENABLE`: Enable Motors
 - `DISABLE`: Disable Motors
 - `STOP`: Stop all motor movement
 - `PAUSE`: Pause all motor movement
 - `RESUME`: Resume all motor movement
 - `POSITION`: Set or Receive positional information

### MOVE

```
MOVE c<CHANNEL#> d<STEPS> s<SPEED> a<ACCEL>

# Example:
MOVE c2 d284 s183.5 a5.0
```

 - `CHANNEL#`: Channel number, either `1`, `2` or `3`
 - `STEPS`: Number of steps the motor should move. 
            Has to be `int` and can be negative or positive
 - `SPEED`: Speed with which the motor should move, given as steps/second as floating point.
            Has to be positive and nonzero.
 - `ACCEL`: Acceleration given in steps/second² as floating point. Has to be positive and nonzero.

### ENABLE

```
ENABLE
```

No further arguments. Enables all motors.

### DISABLE

```
DISABLE
```

No further arguments. Disables all motors.

### STOP

```
STOP [c<CHANNEL#>]
```

 - optional `CHANNEL#`: The channel number which should be stopped.

If no channel is provided, all channels will be stopped. This will delete all "pause" information.

### PAUSE

```
PAUSE
```

No further arguments. Pauses all movement.

### RESUME

```
RESUME
```

No further arguments. Disables all motors.

## Poseidon Commands to Arduino

### Run Motors with given steps

```
<RUN,DIST,_MOTORS_,_VALUE_,_DIRECTION_,_STEPS-M1_,_STEPS-M2_,_STEPS-M3_>
```
 - `_MOTORS_`: String list with `123` corresponding to the motors (e.g. `13` is only Motor 1 & 3)
 - `_VALUE_`: `0`?
 - `_DIRECTION_`: `F` for forward, `B` for backward
 - `_STEPS-M#_`: Steps to move for Motor # as decimal string

### Pause & Resume Motors

```
<$OPERATION,BLAH,$MOTORS,BLAH,F,0.0,0.0,0.0>
```
 - `$OPERATION`: `PAUSE` or `RESUME` respectively.
 - `$MOTORS`: String list with `123` corresponding to the motors (e.g. `13` is only Motor 1 & 3)

### Zero and Stop

```
<$OPERATION,BLAH,BLAH,BLAH,F,0.0,0.0,0.0>
```
 - `$OPERATION`: `ZERO` or `STOP` respectively.

### Save settings to the Arduino

```
<SETTING,$VAR,$MOTOR,$VALUE,F,0.0,0.0,0.0>
```
 - `$VAR`: `SPEED`, `ACCEL` or `DELTA`
 - `$MOTOR`: The motor number which should be affected
 - `$VALUE`: The value which should be stored for the given variable, formatted as a string.

### Send command contained in String `command`

```
thread = Thread(self.runTest, command)
thread.finished.connect(lambda:self.thread_finished(thread))
thread.start()
```