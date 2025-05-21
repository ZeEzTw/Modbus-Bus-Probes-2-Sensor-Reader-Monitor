#!/usr/bin/env python3
"""
Modbus RTU Temperature and Humidity Sensor Monitor

This script continuously polls Modbus RTU devices for temperature and humidity data
via a serial connection. The script displays both the raw commands being sent and
the received data, then writes the data to an InfluxDB database.
"""

# import serial # Not used in simulation
import time
import os
from influxdb import InfluxDBClient
from datetime import datetime
import random # Added for simulation

######################
# CONFIGURATION SECTION
######################

# InfluxDB Configuration
# Local InfluxDB Configuration.
host = "172.18.4.104"  # Local InfluxDB server address (no protocol needed for v1.x)
port = 8086            # Default InfluxDB port
username = ""          # Leave empty if no authentication
password = ""          # Leave empty if no authentication
database = "temperatura_humidity_test"  # Name of the database to write to

# Initialize InfluxDB client for version 1.6.4
client = InfluxDBClient(host=host, port=port, username=username, password=password, database=database)

# Device Configuration
# Number of devices simulated on each floor/wall
# These define the structure for 3 floors * 4 walls * 4 sensors/wall = 48 sensors
floor1_east = 4
floor1_west = 4
floor1_north = 4
floor1_south = 4
floor2_east = 4
floor2_west = 4
floor2_north = 4
floor2_south = 4
floor3_east = 4
floor3_west = 4
floor3_north = 4
floor3_south = 4
# DEVICE_IDS = [106, 124, 125, 129]  # Not used in simulation

# Modbus Configuration (Not used in simulation)
# FUNCTION_CODE = 0x04     # Function code 4 = Read Input Registers
# START_ADDR = 0x0190      # Starting address for temperature data and humidity(0x0190 = 400 decimal)
# NUM_REGISTERS = 0x0002   # Number of registers to read (2 registers: temperature and humidity)

# Alternative address options (commented out, uncomment to use):
# START_ADDR = 0x0191  # TEMP_RAW: Raw temperature data (unsigned 16-bit)
# START_ADDR = 0x0194  # HUM_PROC: Processed humidity data (unsigned 16-bit)
# START_ADDR = 0x0195  # HUM_RAW: Raw humidity data (unsigned 16-bit)

# Serial Port Configuration (Not used in simulation)
# SERIAL_PORT = '/dev/ttyUSB0'  # Change to match your system's serial port, run this command to find the port: sudo dmesg -w
#plug the sensors and then unplug them to see the port
# BAUDRATE = 38400              # Modbus baud rate (commonly 9600 or 38400)
# TIMEOUT = 1                   # Serial read timeout in seconds

# Polling Configuration
POLLING_INTERVAL = 5         # Time between polling cycles in seconds
# DEVICE_PAUSE = 0.2           # Not used in simulation logic as it simulates all at once
# COMMAND_PAUSE = 0.1          # Not used in simulation

# Display Configuration
# SHOW_HEX_COMMANDS = True     # Not used in simulation

######################
# UTILITY FUNCTIONS
######################

def read_modbus_data():
    """
    Simulates reading data from 48 sensors.
    3 floors, 4 walls per floor, 4 sensors per wall.
    Returns a list of tuples: (id, device_id, temperature, humidity, wall, floor, device_code)
    """
    simulated_sensor_data = []
    current_sensor_id = 0
    
    floor_counts = {
        "floor1": {"east": floor1_east, "west": floor1_west, "north": floor1_north, "south": floor1_south},
        "floor2": {"east": floor2_east, "west": floor2_west, "north": floor2_north, "south": floor2_south},
        "floor3": {"east": floor3_east, "west": floor3_west, "north": floor3_north, "south": floor3_south}
    }
    
    wall_to_code = {"east": 0, "west": 1, "north": 2, "south": 3}

    for floor_idx, (floor_name, walls) in enumerate(floor_counts.items()):
        floor_code = floor_idx # 0 for floor1, 1 for floor2, etc.
        floor_number_display = int(floor_name.replace("floor", "")) # For device_id_str

        for wall_name, num_sensors_on_wall in walls.items():
            wall_code = wall_to_code.get(wall_name, 9) # 9 if wall_name is unexpected

            for sensor_idx_on_wall in range(num_sensors_on_wall): # sensor_idx_on_wall is 0-indexed
                current_sensor_id += 1
                # Create a descriptive device ID
                device_id_str = f"sim_f{floor_number_display}_w{wall_name}_s{sensor_idx_on_wall+1}"
                
                temperature = random.uniform(20.0, 30.0)  # Simulated temperature in Celsius
                humidity = random.uniform(30.0, 70.0)     # Simulated humidity in %
                
                # Generate device_code: FWS (Floor, Wall, Sensor index on wall)
                # Example: floor1 (0), west (1), sensor index 1 (1) -> "011"
                device_code_str = f"{floor_code}{wall_code}{sensor_idx_on_wall}"
                
                simulated_sensor_data.append(
                    (current_sensor_id, device_id_str, temperature, humidity, wall_name, floor_name, device_code_str)
                )
                
    print(f"Simulated data for {len(simulated_sensor_data)} sensors.")
    return simulated_sensor_data


def write_batch_to_influxdb(sensor_data_list):
    """
    Write multiple sensors' data to InfluxDB in a single batch
    
    Args:
        sensor_data_list: List of tuples (unique_id, device_id_str, temperature, humidity, wall_name, floor_name, device_code_str)
    """
    if not sensor_data_list:
        print("No sensor data to write to InfluxDB")
        return
        
    try:
        # Create a timestamp for all measurements in this batch
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Create points for all measurements in InfluxDB 1.x format
        points = []
        for unique_id, device_id_str, temperature, humidity, wall, floor, device_code in sensor_data_list:
            # Temperature point
            temp_point = {
                "measurement": "temperature",
                "tags": {
                    "id": str(unique_id), # Using the unique integer ID as a tag
                    "device_id": device_id_str, # Using the descriptive simulated device ID
                    "floor": floor,
                    "wall": wall,
                    "device_code": device_code # Added device_code tag
                },
                "time": timestamp,
                "fields": {
                    "value": float(temperature)
                }
            }
            points.append(temp_point)
            
            # Humidity point
            humidity_point = {
                "measurement": "humidity",
                "tags": {
                    "id": str(unique_id), # Using the unique integer ID as a tag
                    "device_id": device_id_str, # Using the descriptive simulated device ID
                    "floor": floor,
                    "wall": wall,
                    "device_code": device_code # Added device_code tag
                },
                "time": timestamp,
                "fields": {
                    "value": float(humidity)
                }
            }
            points.append(humidity_point)
        
        # Write all points to InfluxDB in a single batch using the v1.x API
        client.write_points(points)
        print(f"Data for {len(sensor_data_list)} device readings (temp/humidity pairs) written to InfluxDB successfully")
        
    except Exception as e:
        print(f"Failed to write batch data to InfluxDB: {e}")

######################
# MAIN PROGRAM
######################

def main():
    try: # Added try block for graceful exit
        while True:
            # Print header for each polling cycle
            print("\n" + "-" * 50)
            print(f"Simulating sensor readings at {time.strftime('%H:%M:%S')}")
            print("-" * 50)
            
            # Collect data from all simulated devices
            all_simulated_data = read_modbus_data()
            
            # Write all collected data to InfluxDB at once
            if all_simulated_data:
                write_batch_to_influxdb(all_simulated_data)
                
            # Wait for next polling cycle
            print(f"\nWaiting {POLLING_INTERVAL} seconds until next polling cycle...")
            time.sleep(POLLING_INTERVAL)
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    # except serial.SerialException as e: # Removed as serial is not used
    #     print(f"\nSerial port error: {e}")
    #     print(f"Please check if port {SERIAL_PORT} exists and is available.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()