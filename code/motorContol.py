# main_drv8833.py
import pyb
import time

# --- Pin Configuration (Pyboard) ---
# We use two PWM-capable pins on the Pyboard to control the DRV8833's AIN1 and AIN2.
# Pin X1 (Timer 2, Channel 1) and Pin X2 (Timer 2, Channel 2) are good choices as they
# can share the same timer, ensuring the PWM signals are synchronized.

# 1. Setup Shared Timer and PWM Channels
# Set a suitable frequency (e.g., 20 kHz is often recommended for the DRV8833)
PWM_FREQ = 20000
tim = pyb.Timer(2, freq=PWM_FREQ)

# AIN1 (e.g., Pyboard Pin X1)
in1_pin = pyb.Pin("X1")
pwm_in1 = tim.channel(1, pyb.Timer.PWM, pin=in1_pin)
pwm_in1.pulse_percent(0)

# AIN2 (e.g., Pyboard Pin X2)
in2_pin = pyb.Pin("X2")
pwm_in2 = tim.channel(2, pyb.Timer.PWM, pin=in2_pin)
pwm_in2.pulse_percent(0)


def motorControl(speed, direction):
    """
    Controls a single DC motor connected to the DRV8833 (HW-626) module.

    Args:
        speed (int): Speed percentage (0 to 100).
        direction (int):
             1: Forward
            -1: Reverse
             0: Stop (Brake/Stop)
    """

    # Clamp the speed value to be between 0 and 100
    if speed < 0:
        speed = 0
    if speed > 100:
        speed = 100

    if direction == 1:
        # FORWARD: AIN1 = PWM (Speed), AIN2 = LOW (0%)
        # The PWM pin controls the speed, the other pin determines direction.
        pwm_in1.pulse_percent(speed)
        pwm_in2.pulse_percent(0)
    elif direction == -1:
        # REVERSE: AIN1 = LOW (0%), AIN2 = PWM (Speed)
        pwm_in1.pulse_percent(0)
        pwm_in2.pulse_percent(speed)
    else:  # direction == 0
        # STOP (Brake): AIN1 = LOW, AIN2 = LOW
        # This shorts the motor terminals, providing a quick stop (Brake).
        pwm_in1.pulse_percent(0)
        pwm_in2.pulse_percent(0)

        # Alternative: STOP (Coast - Freewheel) - Requires setting both to HIGH
        # Setting both HIGH is the other way to brake. Setting both LOW or HIGH
        # results in braking/coasting depending on the chip configuration.
        # pwm_in1.pulse_percent(100)
        # pwm_in2.pulse_percent(100)


# --- Example Usage (Same as before, but using DRV8833 logic) ---
print("Starting DRV8833 motor control test...")

try:
    while True:
        # Forward at 60% speed
        print("Running Forward (60%)")
        motorControl(60, 1)
        time.sleep(2)

        # Quick Stop (Brake)
        print("Stopping (Brake)")
        motorControl(0, 0)
        time.sleep(1)

        # Reverse at 90% speed
        print("Running Reverse (90%)")
        motorControl(90, -1)
        time.sleep(2)

        # Stop
        print("Stopping (Brake)")
        motorControl(0, 0)
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping motor.")
    motorControl(0, 0)
    print("Done.")
