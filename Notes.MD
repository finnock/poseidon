## Notes

### Motors

Motor speed is limited by clockspeed of the compiler. The current Firmware checks EVERY step in the while loop for new commands from the PC.
Since a single rep of the loop results in only up to ONE SINGLE step this limits the speed drastically. especially when multiple motors move in parallel this can be seen.
Here could be some optimisations done.

## Values

A complete revolution of the motor seems to have 100 steps. With 32 microsteps enabled this should result in 3200 steps for a whole revolution

```
WHOLE_STEPS per Revolution = 100
STEPS per Revolution = WHOLE_STEPS * MICRO_STEPS = 3200
```

Using a T8 threaded rod with 2mm steepness results in 2mm per revolution

```
MM_PER_REVOLUTION = 2
MM_PER_MICROSTEP = 2/3200 = 0.000625 or 0.625 micrometers
```