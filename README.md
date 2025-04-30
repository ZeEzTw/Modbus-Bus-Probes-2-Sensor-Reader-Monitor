This Python script continuously reads data from multiple Modbus RTU devices connected via a serial interface.
It polls each device for temperature and humidity, displays the values in the terminal, and can be easily extended to integrate with a database or dashboard.
Key Features:

    Supports multiple Modbus RTU slave devices

    Real-time monitoring loop with configurable polling intervals

    Prints temperature and humidity data

    Displays raw hexadecimal requests and responses (for debugging purposes)

Configuration:

Edit the configuration values inside the script to match your system’s setup. For example:

    SERIAL_PORT: Change this to match your system’s serial port. To find the port, run the command sudo dmesg -w, plug in the sensors, then unplug them to see the port.

    POLLING_INTERVAL, etc.

How to Run the Script:

    Clone or download the script:
    python3 read_modbus.py
    
    Press Ctrl + C to stop the monitoring loop.

Output Example:

--------------------------------------------------
Polling devices at 14:22:10
--------------------------------------------------
Sending to ID 1: 01 03 00 00 00 02 XX XX
ID 1: Temperature = 23.5°C, Humidity = 45.20%
...

Waiting 5 seconds until next polling cycle...

Optional Integrations:

This script can be extended to integrate with:

    InfluxDB for time-series data storage

    Grafana for visualization dashboards

Let me know if you would like me to add these integrations!
