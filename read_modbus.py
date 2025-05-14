#!/usr/bin/env python3
"""
Modbus RTU Temperature and Humidity Sensor Monitor

This script continuously polls Modbus RTU devices for temperature and humidity data
via a serial connection. The script displays both the raw commands being sent and
the received data, then writes the data to an InfluxDB database.
"""

import serial
import time
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

######################
# CONFIGURATION SECTION
######################

# InfluxDB Configuration
# Local InfluxDB Configuration
host = "http://172.18.4.104:8086"  # Local InfluxDB server address with protocol
bucket = "temperatura_humidity_data"  # Name of the bucket to write to

# Initialize InfluxDB client
client = InfluxDBClient(url=host)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Device Configuration
DEVICE_IDS = [106, 124, 125, 129]  # List of device IDs to poll - add/remove device IDs as needed

# Modbus Configuration
FUNCTION_CODE = 0x04     # Function code 4 = Read Input Registers
START_ADDR = 0x0190      # Starting address for temperature data and humidity(0x0190 = 400 decimal)
NUM_REGISTERS = 0x0002   # Number of registers to read (2 registers: temperature and humidity)

# Alternative address options (commented out, uncomment to use):
# START_ADDR = 0x0191  # TEMP_RAW: Raw temperature data (unsigned 16-bit)
# START_ADDR = 0x0194  # HUM_PROC: Processed humidity data (unsigned 16-bit)
# START_ADDR = 0x0195  # HUM_RAW: Raw humidity data (unsigned 16-bit)

# Serial Port Configuration
SERIAL_PORT = '/dev/ttyUSB0'  # Change to match your system's serial port, run this command to find the port: sudo dmesg -w
#plug the sensors and then unplug them to see the port
BAUDRATE = 38400              # Modbus baud rate (commonly 9600 or 38400)
TIMEOUT = 1                   # Serial read timeout in seconds

# Polling Configuration
POLLING_INTERVAL = 5         # Time between polling cycles in seconds
DEVICE_PAUSE = 0.2           # Time between device polls in seconds
COMMAND_PAUSE = 0.1          # Time to wait after sending a command

# Display Configuration
SHOW_HEX_COMMANDS = True     # Set to False to hide hex command display

######################
# UTILITY FUNCTIONS
######################

def modbus_crc(data: bytes) -> bytes:
    """
    Calculate Modbus RTU CRC-16 for the given data.
    
    Args:
        data: Bytes to calculate CRC for
        
    Returns:
        2-byte CRC value in little-endian byte order
    """
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if (crc & 0x0001):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def read_modbus_data(ser, device_id):
    """
    Send a Modbus request to read temperature and humidity data from a device.
    
    Args:
        ser: Serial port object
        device_id: Modbus device ID to query
        
    Returns:
        Tuple of (device_id, temperature, humidity) or None if unsuccessful
    """
    # Build Modbus RTU request
    payload = bytes([device_id, FUNCTION_CODE]) + START_ADDR.to_bytes(2, 'big') + NUM_REGISTERS.to_bytes(2, 'big')
    crc = modbus_crc(payload)
    request = payload + crc
    
    # Display hex command if enabled
    if SHOW_HEX_COMMANDS:
        hex_request = ' '.join([f'{byte:02X}' for byte in request])
        print(f"Sending to ID {device_id}: {hex_request}")

    # Send request and wait for response
    ser.write(request)
    time.sleep(COMMAND_PAUSE)
    
    # Process response
    response = ser.read(9)  # Expected response is 9 bytes for 2 registers
    if len(response) >= 9:
        data_bytes = response[3:7]
        temp_raw = int.from_bytes(data_bytes[0:2], byteorder='big')
        humid_raw = int.from_bytes(data_bytes[2:4], byteorder='big')
        
        # Convert raw values to physical units
        temperature = temp_raw / 10.0     # Scale factor for temperature
        humidity = humid_raw / 100.0      # Scale factor for humidity
        
        print(f"ID {device_id}: Temperature = {temperature:.1f}°C, Humidity = {humidity:.2f}%")
        
        # Return the sensor data
        return device_id, temperature, humidity
    else:
        print(f"ID {device_id}: No or incomplete response")
        return None

def write_batch_to_influxdb(sensor_data):
    """
    Write multiple sensors' data to InfluxDB in a single batch
    
    Args:
        sensor_data: List of tuples (device_id, temperature, humidity)
    """
    if not sensor_data:
        print("No sensor data to write to InfluxDB")
        return
        
    try:
        # Create a timestamp for all measurements
        timestamp = datetime.utcnow()
        
        # Create points for all measurements
        points = []
        for device_id, temperature, humidity in sensor_data:
            # Temperature point
            temp_point = Point("temperature") \
                .tag("device_id", f"modbus_{device_id}") \
                .field("value", temperature) \
                .time(timestamp)
            points.append(temp_point)
            
            # Humidity point
            humidity_point = Point("humidity") \
                .tag("device_id", f"modbus_{device_id}") \
                .field("value", humidity) \
                .time(timestamp)
            points.append(humidity_point)
        
        # Write all points to InfluxDB in a single batch
        write_api.write(bucket=bucket, record=points)
        print(f"Data for {len(sensor_data)} devices written to InfluxDB successfully")
        
    except Exception as e:
        print(f"Failed to write batch data to InfluxDB: {e}")

######################
# MAIN PROGRAM
######################

def main():
    """Main function to run the continuous polling loop"""
    try:
        with serial.Serial(port=SERIAL_PORT, baudrate=BAUDRATE, timeout=TIMEOUT) as ser:
            print(f"Starting continuous polling every {POLLING_INTERVAL} seconds. Press Ctrl+C to stop.")
            
            while True:
                # Print header for each polling cycle
                print("\n" + "-" * 50)
                print(f"Polling devices at {time.strftime('%H:%M:%S')}")
                print("-" * 50)
                
                # Collect data from all devices
                sensor_data = []
                for device_id in DEVICE_IDS:
                    result = read_modbus_data(ser, device_id)
                    if result:
                        sensor_data.append(result)
                    time.sleep(DEVICE_PAUSE)
                
                # Write all collected data to InfluxDB at once
                if sensor_data:
                    write_batch_to_influxdb(sensor_data)
                    
                # Wait for next polling cycle
                print(f"\nWaiting {POLLING_INTERVAL} seconds until next polling cycle...")
                time.sleep(POLLING_INTERVAL)
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
    except serial.SerialException as e:
        print(f"\nSerial port error: {e}")
        print(f"Please check if port {SERIAL_PORT} exists and is available.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()