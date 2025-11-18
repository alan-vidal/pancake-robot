import pyb
import time
import struct
import uasyncio  # Import the asynchronous I/O library


# --- 1. MPU-6050 Driver (No changes needed) ---
class MPU6050:
    DEFAULT_ADDR = 0x68
    REG_PWR_MGMT_1 = 0x6B
    REG_ACCEL_X_H = 0x3B
    SCALE_ACCEL = 16384.0
    SCALE_GYRO = 131.0

    def __init__(self, i2c_bus, addr=DEFAULT_ADDR):
        self.i2c = i2c_bus
        self.addr = addr
        self._buffer = bytearray(14)
        try:
            self.i2c.writeto_mem(self.addr, self.REG_PWR_MGMT_1, b"\x00")
            time.sleep_ms(100)  # Sync sleep is OK in init
        except OSError as e:
            print(f"Failed to init MPU6050: {e}")
            raise

    def get_all_data_scaled(self):
        try:
            # This is still a synchronous (blocking) I2C read
            self.i2c.readfrom_mem_into(self.addr, self.REG_ACCEL_X_H, self._buffer)
            ax_r, ay_r, az_r, t_r, gx_r, gy_r, gz_r = struct.unpack(
                ">hhhhhhh", self._buffer
            )

            ax = ax_r / self.SCALE_ACCEL
            ay = ay_r / self.SCALE_ACCEL
            az = az_r / self.SCALE_ACCEL
            temp_c = (t_r / 340.0) + 36.53
            gx = gx_r / self.SCALE_GYRO
            gy = gy_r / self.SCALE_GYRO
            gz = gz_r / self.SCALE_GYRO

            return (ax, ay, az, temp_c, gx, gy, gz)
        except OSError as e:
            print(f"I2C Error: {e}")
            return (0, 0, 0, 0, 0, 0, 0)


# --- 2. Synchronous Helper Functions (No changes needed) ---
# These functions do the CPU-work of getting and packing data.


def externalAcelerometers(sensor_device):
    if not sensor_device:
        return None
    ax, ay, az, temp_c, gx, gy, gz = sensor_device.get_all_data_scaled()
    return {
        "accel_x": ax,
        "accel_y": ay,
        "accel_z": az,
        "gyro_x": gx,
        "gyro_y": gy,
        "gyro_z": gz,
        "temp_c": temp_c,
    }


def getInternalAccelerometerData(accel_obj, has_filtered_method):
    if not accel_obj:
        return None
    if has_filtered_method:
        x, y, z = accel_obj.filtered_xyz()  # Blocking read
        units = "g-force"
    else:
        x, y, z = accel_obj.xyz()  # Blocking read
        units = "raw"
    return {"accel_x": x, "accel_y": y, "accel_z": z, "units": units}


# --- 3. Asynchronous Wrapper Functions (NEW) ---
# These functions call the synchronous code and then yield control.


async def get_internal_data_async(accel_obj, has_filtered_method):
    """Async wrapper for the internal accelerometer read."""
    data = getInternalAccelerometerData(accel_obj, has_filtered_method)
    await uasyncio.sleep_ms(0)  # Yield to the scheduler
    return data


async def get_external_data_async(sensor_device):
    """Async wrapper for the external accelerometer read."""
    data = externalAcelerometers(sensor_device)
    await uasyncio.sleep_ms(0)  # Yield to the scheduler
    return data


# --- 4. Refactored Asynchronous Fusion Function (NEW) ---

NORMALIZATION_RANGE_G = 2.0
NORMALIZATION_RANGE_V1_RAW = 32.0


async def get_averaged_accel_data_async(
    internal_obj, internal_has_filter, external_obj
):
    """
    Fetches data from both sensors concurrently, normalizes,
    and returns the average.
    """

    # 1. Schedule both tasks to run concurrently
    # uasyncio.gather() runs both coroutines.
    # The 'await' pauses this function until *both* are complete.
    try:
        int_data, ext_data = await uasyncio.gather(
            get_internal_data_async(internal_obj, internal_has_filter),
            get_external_data_async(external_obj),
        )
    except OSError as e:
        print(f"Sensor read error: {e}")
        return None

    if not int_data or not ext_data:
        print("Error reading one or more sensors.")
        return None

    # 2. Normalize Internal Sensor Data (This part is fast)
    int_norm_factor = (
        NORMALIZATION_RANGE_G
        if int_data["units"] == "g-force"
        else NORMALIZATION_RANGE_V1_RAW
    )
    int_norm_x = int_data["accel_x"] / int_norm_factor
    int_norm_y = int_data["accel_y"] / int_norm_factor
    int_norm_z = int_data["accel_z"] / int_norm_factor

    # 3. Normalize External Sensor Data
    ext_norm_x = ext_data["accel_x"] / NORMALIZATION_RANGE_G
    ext_norm_y = ext_data["accel_y"] / NORMALIZATION_RANGE_G
    ext_norm_z = ext_data["accel_z"] / NORMALIZATION_RANGE_G

    # 4. Average and Clamp
    avg_x = max(-1.0, min(1.0, (int_norm_x + ext_norm_x) / 2.0))
    avg_y = max(-1.0, min(1.0, (int_norm_y + ext_norm_y) / 2.0))
    avg_z = max(-1.0, min(1.0, (int_norm_z + ext_norm_z) / 2.0))

    return {"norm_x": avg_x, "norm_y": avg_y, "norm_z": avg_z}


# --- 5. Demonstration Task (Blinker) ---


async def blink_led(led, period_ms):
    """A simple task to prove the scheduler is working."""
    while True:
        led.toggle()
        await uasyncio.sleep_ms(period_ms)


# --- 6. Main Asynchronous Execution ---


async def main():
    """Main coroutine to set up and run all tasks."""
    print("Initializing all sensors...")
    internal_accel = None
    external_mpu = None
    has_filtered_method = False

    try:
        # 1. Init Internal Sensor
        internal_accel = pyb.Accel()
        has_filtered_method = hasattr(internal_accel, "filtered_xyz")
        print("Internal accelerometer initialized.")

        # 2. Init External Sensor
        i2c = pyb.I2C(1, pyb.I2C.MASTER, baudrate=400000)
        devices = i2c.scan()
        if MPU6050.DEFAULT_ADDR not in devices:
            raise OSError("MPU-6050 not found at 0x68.")
        external_mpu = MPU6050(i2c)
        print("External MPU-6050 initialized.")

    except Exception as e:
        print(f"FATAL ERROR during initialization: {e}")
        return

    # --- Create and run tasks ---
    print("\nStarting sensor fusion loop...")
    print("The RED LED (LED 1) should be blinking.")
    print("-" * 50)

    # Create and schedule the blinker task to run "in the background"
    led = pyb.LED(1)  # LED 1 is RED on most Pyboards
    uasyncio.create_task(blink_led(led, 500))

    # Run the main fusion loop
    while True:
        # Call our new async fusion function
        fused_data = await get_averaged_accel_data_async(
            internal_accel, has_filtered_method, external_mpu
        )

        if fused_data:
            print(
                f"Fused Norm: X={fused_data['norm_x']: .3f} | "
                f"Y={fused_data['norm_y']: .3f} | "
                f"Z={fused_data['norm_z']: .3f}"
            )

        # This is the cooperative sleep.
        # While this task is sleeping, the blink_led task will run.
        await uasyncio.sleep_ms(200)


# --- Run the Event Loop ---
try:
    uasyncio.run(main())
except KeyboardInterrupt:
    print("Interrupted")
finally:
    # Optional: Clean up loop/tasks if needed
    print("Loop stopped.")
