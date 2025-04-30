This Python script continuously reads data from multiple Modbus RTU devices connected via a serial interface. It polls each device for temperature and humidity, displays the values in the terminal, and now integrates seamlessly with InfluxDB for time-series storage and Grafana for visualization.
Key Features

    Supports multiple Modbus RTU slave devices

    Real-time monitoring loop with configurable polling intervals

    Displays temperature and humidity data in the terminal

    Shows raw Modbus hexadecimal requests and responses for debugging

    Sends data to InfluxDB for long-term storage and analysis

    Compatible with Grafana dashboards for real-time data visualization

Configuration

Edit the configuration values in the script to match your system setup. For example:

    SERIAL_PORT: Set this to your system’s serial port. You can run sudo dmesg -w while plugging/unplugging the sensor to identify the correct port.

    POLLING_INTERVAL: Adjust the delay between each polling cycle.

Running the Script

python3 read_modbus.py

Use Ctrl + C to stop the monitoring loop.
Sample Output

--------------------------------------------------
Polling devices at 14:22:10
--------------------------------------------------
Sending to ID 1: 01 03 00 00 00 02 XX XX
ID 1: Temperature = 23.5°C, Humidity = 45.20%
...

Waiting 5 seconds until next polling cycle...

InfluxDB + Grafana Integration

This script sends real-time data to InfluxDB and allows you to build dashboards in Grafana.
InfluxDB Configuration

Configure these values directly in the script or through environment variables:

token = os.environ.get("INFLUXDB_TOKEN", "<your_token>")
org = "<your_organization>"
host = "<your_influxdb_host_url>"  # e.g., https://us-east-1-1.aws.cloud2.influxdata.com
bucket = "<your_bucket_name>"      # e.g., "temperature_humidity_data"
