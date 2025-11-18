import pyb
import time

# --- 1. Initialize the Internal Accelerometer ---

try:
    # Create an accelerometer object
    accel = pyb.Accel()

    # Check if this board supports the 'filtered_xyz()' method
    # This method is specific to Pyboard D-series and returns scaled g-force
    has_filtered_method = hasattr(accel, "filtered_xyz")

    print("Internal accelerometer initialized successfully.")
    if has_filtered_method:
        print("Board type: Pyboard D-series (supports g-force output)")
    else:
        print("Board type: Pyboard v1.x (supports raw integer output)")

except OSError:
    print("ERROR: Internal accelerometer not detected.")
    accel = None
    has_filtered_method = False

# --- 2. The Requested Function ---


def getInternalAccelerometerData():
    """
    Fetches all usable variables from the Pyboard's internal accelerometer.

    Returns a dictionary containing:
    - 'accel_x', 'accel_y', 'accel_z': Acceleration data
    - 'tilt': A 3-bit tilt register value (0-6)
    - 'units': A string ('g-force' or 'raw') indicating the unit
    """
    if not accel:
        print("Error: Internal accelerometer is not initialized.")
        return None

    data = {}

    # Check which method to use for data retrieval
    if has_filtered_method:
        # --- Pyboard D-series ---
        # filtered_xyz() returns scaled, floating-point g-force values
        x, y, z = accel.filtered_xyz()
        data["units"] = "g-force"

    else:
        # --- Pyboard v1.x ---
        # xyz() returns raw 8-bit signed integer values
        # (e.g., Z will be ~16 when flat)
        x, y, z = accel.xyz()
        data["units"] = "raw"

    # Pack all data into the dictionary
    data["accel_x"] = x
    data["accel_y"] = y
    data["accel_z"] = z

    # The tilt register is available on all models
    data["tilt"] = accel.tilt()

    return data


# --- 3. Main Execution (Example Usage) ---

if accel:
    print("\nReading data... Press Ctrl+C to stop.")
    print("-" * 40)

    while True:
        try:
            # Call your function to get the data
            sensor_data = getInternalAccelerometerData()

            if sensor_data:
                units = sensor_data["units"]

                # Format the output based on the data type
                if units == "g-force":
                    # Print nicely formatted floats for g-force
                    print(
                        f"Accel ({units}): X={sensor_data['accel_x']:.2f}, "
                        f"Y={sensor_data['accel_y']:.2f}, "
                        f"Z={sensor_data['accel_z']:.2f}"
                    )
                else:
                    # Print left-aligned integers for raw values
                    print(
                        f"Accel ({units}): X={sensor_data['accel_x']:<4}, "
                        f"Y={sensor_data['accel_y']:<4}, "
                        f"Z={sensor_data['accel_z']:<4}"
                    )

                # Print the tilt register
                print(f"Tilt Register: {sensor_data['tilt']}")
                print("-" * 40)

            time.sleep_ms(500)  # Poll twice per second

        except KeyboardInterrupt:
            print("\nProgram stopped.")
            break
