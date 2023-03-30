## Commands to Arduino

Main Command Structure
```
<_MODE_,_SETTING_,_MOTORS_,_VALUE_,_DIRECTION_,_STEPS-M1_,_STEPS-M2_,_STEPS-M3_>
```
 - `_MODE_`: `RUN`?
 - `_SETTING_`: `DIST`?
 - `_MOTORS_`: String list with `123` corresponding to the motors (e.g. `13` is only Motor 1 & 3)
 - `_VALUE_`: `0`?
 - `_DIRECTION_`: `F` for forward
 - `_STEPS-M#_`: Steps to move for Motor # as decimal string

Send command contained in String `command`

```
thread = Thread(self.runTest, command)
thread.finished.connect(lambda:self.thread_finished(thread))
thread.start()
```