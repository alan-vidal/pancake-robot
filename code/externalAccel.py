import pyb
import time
import struct


# --- 1. A Minimal MPU-6050 Driver Class ---
# This class handles the I2C communication and data conversion.
#
class MPU6050:
    """A minimal driver for the MPU-6050 IMU."""

    # Default I2C address
    DEFAULT_ADDR = 0x68

    # Internal register addresses
    REG_PWR_MGMT_1 = 0x6B
    REG_ACCEL_X_H = 0x3B
    REG_GYRO_X_H = 0x43
    REG_TEMP_H = 0x41

    # Scaling factors for default settings (±2g, ±250dps)
    # 16-bit signed int (65536 total values)
    # Accel: 65536 / 4g (from -2g to +2g) = 16384 LSB/g
    # Gyro:  65536 / 500dps (from -250 to +250) = 131.072 LSB/dps
    SCALE_ACCEL = 16384.0
    SCALE_GYRO = 131.0

    def __init__(self, i2c_bus, addr=DEFAULT_ADDR):
        self.i2c = i2c_bus
        self.addr = addr
        self._buffer = bytearray(14)

        # Wake the sensor up - it starts in sleep mode
        # We do this by writing 0 to the Power Management 1 register
        self.i2c.writeto_mem(self.addr, self.REG_PWR_MGMT_1, b"\x00")
        time.sleep_ms(100)  # Wait for sensor to stabilize

    def _read_signed_word(self, high_byte, low_byte):
        """Combines two bytes into a 16-bit signed integer."""
        value = (high_byte << 8) | low_byte
        # Check if the highest bit (sign bit) is set
        if value >= 0x8000:
            return value - 0x10000  # Convert to negative (two's complement)
        else:
            return value

    def get_all_data_scaled(self):
        """
        Reads all 14 bytes of data (Accel, Temp, Gyro) at once
        and returns them as scaled, physical values.
        """
        try:
            # Read 14 bytes starting from the Accel X H register (0x3B)
            # This block contains:
            # 0x3B-3C: Accel X
            # 0x3D-3E: Accel Y
            # 0x3F-40: Accel Z
            # 0x41-42: Temp
            # 0x43-44: Gyro X
            # 0x45-46: Gyro Y
            # 0x47-48: Gyro Z
            self.i2c.readfrom_mem_into(self.addr, self.REG_ACCEL_X_H, self._buffer)

            # Unpack all 7 values (14 bytes) at once.
            # '>' means big-endian, 'h' means signed 16-bit integer.
            ax_raw, ay_raw, az_raw, temp_raw, gx_raw, gy_raw, gz_raw = struct.unpack(
                ">hhhhhhh", self._buffer
            )

            # --- Apply scaling factors ---

            # Accelerometer data in g-force
            ax = ax_raw / self.SCALE_ACCEL
            ay = ay_raw / self.SCALE_ACCEL
            az = az_raw / self.SCALE_ACCEL

            # Temperature data in degrees Celsius
            # Formula from datasheet: (TEMP_OUT / 340) + 36.53
            temp_c = (temp_raw / 340.0) + 36.53

            # Gyroscope data in degrees per second (dps)
            gx = gx_raw / self.SCALE_GYRO
            gy = gy_raw / self.SCALE_GYRO
            gz = gz_raw / self.SCALE_GYRO

            return (ax, ay, az, temp_c, gx, gy, gz)

        except OSError as e:
            print(f"I2C Error reading sensor: {e}")
            return (0, 0, 0, 0, 0, 0, 0)


# --- 2. Your Requested Function ---


def externalAcelerometers(sensor_device):
    """
    Takes an initialized MPU6050 sensor object and returns a
    dictionary containing all usable variables.

    Output variables:
    - 'accel_x', 'accel_y', 'accel_z': Acceleration in g-force (g)
    - 'gyro_x', 'gyro_y', 'gyro_z': Angular velocity in degrees/sec (dps)
    - 'temp_c': Temperature in degrees Celsius (°C)
    """
    if not sensor_device:
        print("Error: Sensor device is not initialized.")
        return None

    # Get all 7 scaled values from the sensor
    ax, ay, az, temp_c, gx, gy, gz = sensor_device.get_all_data_scaled()

    # Pack the data into a clean, easy-to-use dictionary
    sensor_data = {
        "accel_x": ax,
        "accel_y": ay,
        "accel_z": az,
        "gyro_x": gx,
        "gyro_y": gy,
        "gyro_z": gz,
        "temp_c": temp_c,
    }

    return sensor_data


# --- 3. Main Execution (Example Usage) ---

print("Initializing I2C(1) on X9 (SCL) and X10 (SDA)...")
try:
    # Initialize I2C bus 1
    i2c = pyb.I2C(1, pyb.I2C.MASTER, baudrate=400000)

    # Check if the sensor is connected (should be at 0x68)
    devices = i2c.scan()
    if MPU6050.DEFAULT_ADDR not in devices:
        raise OSError("MPU-6050 not found at address 0x68.")

    print("MPU-6050 sensor found!")

    # Create the sensor object
    mpu = MPU6050(i2c)

    print("Reading data from sensor. Press Ctrl+C to stop.")
    print("-" * 40)

    while True:
        # Call your function to get the data
        all_data = externalAcelerometers(mpu)

        if all_data:
            # Print the formatted data
            print(
                f"Accel (g):  X={all_data['accel_x']:.2f}, Y={all_data['accel_y']:.2f}, Z={all_data['accel_z']:.2f}"
            )
            print(
                f"Gyro (dps): X={all_data['gyro_x']:.2f}, Y={all_data['gyro_y']:.2f}, Z={all_data['gyro_z']:.2f}"
            )
            print(f"Temp (°C):  {all_data['temp_c']:.2f}")
            print("-" * 40)

        time.sleep_ms(500)  # Poll twice per second

except OSError as e:
    print(f"Failed to initialize. Check wiring. Error: {e}")
except KeyboardInterrupt:
    print("\nProgram stopped.")
