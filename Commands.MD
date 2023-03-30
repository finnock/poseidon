## Commands to Arduino

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