# switchbot-ble-to-influxdb

Collects environmental data from SwitchBot BLE sensors and stores it in InfluxDB.

## Requirements

*   Python 3.12+
*   [uv](https://github.com/astral-sh/uv)
*   [just](https://github.com/casey/just)
*   SwitchBot Meter/Sensor devices
*   InfluxDB instance

## Dependencies

This project uses the following main Python libraries:

*   [pySwitchbot](https://github.com/sblibs/pySwitchbot): For interacting with SwitchBot devices.
*   `influxdb-client`: For sending data to InfluxDB.
*   `python-dotenv`: For managing environment variables.

Development dependencies are managed via `pyproject.toml` and include `pytest` for testing.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/junkei-okinawa/switchbot-ble-to-influxdb.git
    cd switchbot-ble-to-influxdb
    ```

2.  **Install dependencies using uv:**
    ```bash
    uv sync
    ```
    If you also want to install development dependencies (e.g., for running tests):
    ```bash
    uv sync --dev
    ```

## Configuration

This application requires several environment variables to be set. You can create a `.env` file in the root of the project directory to store these variables.

```env
INFLUXDB_TOKEN="your_influxdb_token"
INFLUXDB_URL="http://localhost:8086" # Or your InfluxDB URL
INFLUXDB_ORG="your_influxdb_org"
INFLUXDB_BUCKET="your_influxdb_bucket"
INFLUXDB_MEASUREMENT="switchbot_metrics" # Or your desired measurement name
DEVICE_ID="your_switchbot_device_address" # Address of the target SwitchBot device
```

Replace the placeholder values with your actual InfluxDB credentials and SwitchBot device address.

## Usage

To run the script and start collecting data:

```bash
uv run just dev
```

This command will execute the `main.py` script, which discovers SwitchBot temperature sensors, reads data from the specified device, and writes it to your InfluxDB instance.

Logs will be printed to the console.

## How it Works

The `main.py` script performs the following steps:
1.  Loads environment variables.
2.  Initializes the InfluxDB client.
3.  Uses `GetSwitchbotDevices` from the `pyswitchbot` library to discover nearby SwitchBot temperature and humidity sensors.
4.  Filters for the device matching the `DEVICE_ID` environment variable.
5.  Extracts temperature, humidity, and battery level (if available) from the sensor data.
6.  Formats the data as a `Point` object for InfluxDB.
7.  Writes the data point to the specified InfluxDB bucket.

## Development

### Running Tests

To run tests:
```bash
uv run just test
# unit test
uv run just test tests/unit
# integration test
uv run just test tests/integration
```
