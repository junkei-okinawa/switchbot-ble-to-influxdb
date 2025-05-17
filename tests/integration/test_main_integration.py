import os
import sys
import asyncio

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add the project root to the Python path
# Resolve the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Now you can import the main module
import main as reader_main_module # Changed: Import main.py as a module

# --- Environment Variable Setup ---
# It's good practice to set these for integration tests,
# even if parts are mocked, to ensure the main script's initial checks pass.
@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    monkeypatch.setenv("INFLUXDB_TOKEN", "test_token")
    monkeypatch.setenv("INFLUXDB_URL", "http://localhost:8086")
    monkeypatch.setenv("INFLUXDB_ORG", "test_org")
    monkeypatch.setenv("INFLUXDB_BUCKET", "test_bucket")
    monkeypatch.setenv("INFLUXDB_MEASUREMENT", "test_measurement")
    monkeypatch.setenv("DEVICE_ID", "XX:XX:XX:XX:XX:XX") # Replace with a valid test device ID or mock

# --- Test Cases ---

@pytest.mark.asyncio
async def test_successful_data_fetch_and_write(monkeypatch): # Added monkeypatch here
    """
    Tests the successful fetching of data from SwitchBot and writing to InfluxDB.
    """
    mock_sensor_data = {
        "XX:XX:XX:XX:XX:XX": MagicMock(
            address="XX:XX:XX:XX:XX:XX",
            data={
                "modelFriendlyName": "TestMeter",
                "data": {
                    "temperature": 25.5,
                    "humidity": 60,
                    "battery": 90,
                },
            },
        )
    }

    # Mock GetSwitchbotDevices and its methods
    mock_get_switchbot_devices = AsyncMock()
    mock_get_switchbot_devices.get_tempsensors.return_value = mock_sensor_data

    # Mock InfluxDBClient and its methods
    mock_influx_client_instance = MagicMock()
    mock_write_api = MagicMock()
    mock_influx_client_instance.write_api.return_value = mock_write_api

    with patch('main.GetSwitchbotDevices', return_value=mock_get_switchbot_devices) as mock_switchbot, \
        patch('main.InfluxDBClient', return_value=mock_influx_client_instance) as mock_influx_client, \
        patch('main.logger') as mock_logger: # Optional: mock logger to check logs

        await reader_main_module.main() # Changed: Call main function from the module

        # Assertions
        mock_switchbot.assert_called_once()
        mock_get_switchbot_devices.get_tempsensors.assert_awaited_once()

        mock_influx_client.assert_called_once_with(url="http://localhost:8086", token="test_token")
        mock_influx_client_instance.write_api.assert_called_once()

        # Check if write_api.write was called with the correct data
        # This requires inspecting the 'record' argument of the call
        assert mock_write_api.write.call_count == 1
        args, kwargs = mock_write_api.write.call_args
        assert kwargs['bucket'] == "test_bucket"
        assert kwargs['org'] == "test_org"
        # Detailed check of the Point data
        point = kwargs['record']
        assert point._name == "test_measurement"
        assert point._tags['device_id'] == "XX:XX:XX:XX:XX:XX"
        assert point._tags['friendly_name'] == "TestMeter"
        assert point._fields['temperature'] == 25.5
        assert point._fields['humidity'] == 60
        assert point._fields['battery'] == 90

        mock_logger.info.assert_any_call("InfluxDB client initialized.")
        mock_logger.info.assert_any_call("Data written to InfluxDB for device XX:XX:XX:XX:XX:XX")


@pytest.mark.asyncio
async def test_switchbot_device_not_found(monkeypatch): # Added monkeypatch here
    """
    Tests the scenario where the specified SwitchBot device is not found.
    """
    # Mock GetSwitchbotDevices to return no sensors or an empty dict
    mock_get_switchbot_devices = AsyncMock()
    mock_get_switchbot_devices.get_tempsensors.return_value = {} # No sensors found

    mock_influx_client_instance = MagicMock()
    mock_write_api = MagicMock()
    mock_influx_client_instance.write_api.return_value = mock_write_api

    with patch('main.GetSwitchbotDevices', return_value=mock_get_switchbot_devices) as mock_switchbot, \
        patch('main.InfluxDBClient', return_value=mock_influx_client_instance) as mock_influx_client, \
        patch('main.logger') as mock_logger:

        await reader_main_module.main() # Changed: Call main function from the module

        mock_switchbot.assert_called_once()
        mock_get_switchbot_devices.get_tempsensors.assert_awaited_once()
        mock_influx_client.assert_called_once() # Client is still initialized

        # Ensure write was not called as no device data should be processed
        mock_write_api.write.assert_not_called()
        mock_logger.info.assert_any_call("InfluxDB client initialized.")
        # Check for a log message indicating no matching device or empty sensors
        # Depending on your main.py logic, this log might vary.
        # For example, if it logs when sensors are empty or no device matches:
        # mock_logger.info.assert_any_call("No temperature sensors found.") or similar

@pytest.mark.asyncio
async def test_influxdb_write_failure(monkeypatch): # Added monkeypatch here
    """
    Tests the scenario where writing to InfluxDB fails.
    """
    mock_sensor_data = {
        "XX:XX:XX:XX:XX:XX": MagicMock(
            address="XX:XX:XX:XX:XX:XX",
            data={
                "modelFriendlyName": "TestMeter",
                "data": {
                    "temperature": 25.5,
                    "humidity": 60,
                    "battery": 90,
                },
            },
        )
    }

    mock_get_switchbot_devices = AsyncMock()
    mock_get_switchbot_devices.get_tempsensors.return_value = mock_sensor_data

    mock_influx_client_instance = MagicMock()
    mock_write_api = MagicMock()
    # Simulate an exception during write
    mock_write_api.write.side_effect = Exception("InfluxDB write error")
    mock_influx_client_instance.write_api.return_value = mock_write_api

    with patch('main.GetSwitchbotDevices', return_value=mock_get_switchbot_devices) as mock_switchbot, \
        patch('main.InfluxDBClient', return_value=mock_influx_client_instance) as mock_influx_client, \
        patch('main.logger') as mock_logger:

        await reader_main_module.main() # Changed: Call main function from the module

        mock_switchbot.assert_called_once()
        mock_get_switchbot_devices.get_tempsensors.assert_awaited_once()
        mock_influx_client.assert_called_once()
        mock_write_api.write.assert_called_once() # Write was attempted

        # Check for the error log
        mock_logger.error.assert_any_call("Error writing to InfluxDB: InfluxDB write error")

@pytest.mark.asyncio
async def test_specific_device_id_not_in_scan_results(monkeypatch): # Added monkeypatch here
    """
    Tests the scenario where the DEVICE_ID is set, but no matching device is found in scan results.
    """
    monkeypatch.setenv("DEVICE_ID", "YY:YY:YY:YY:YY:YY") # A specific device ID not in mock_sensor_data
    mock_sensor_data = {
        "XX:XX:XX:XX:XX:XX": MagicMock( # A different device
            address="XX:XX:XX:XX:XX:XX",
            data={
                "modelFriendlyName": "OtherMeter",
                "data": {"temperature": 20.0, "humidity": 50},
            },
        )
    }

    mock_get_switchbot_devices = AsyncMock()
    mock_get_switchbot_devices.get_tempsensors.return_value = mock_sensor_data

    mock_influx_client_instance = MagicMock()
    mock_write_api = MagicMock()
    mock_influx_client_instance.write_api.return_value = mock_write_api

    with patch('main.GetSwitchbotDevices', return_value=mock_get_switchbot_devices) as mock_get_devices, \
        patch('main.InfluxDBClient', return_value=mock_influx_client_instance) as mock_influx_client, \
        patch('main.logger') as mock_logger:

        await reader_main_module.main() # Changed: Call main function from the module

        mock_get_devices.assert_called_once() # Ensure GetSwitchbotDevices was called
        mock_get_switchbot_devices.get_tempsensors.assert_awaited_once()
        mock_write_api.write.assert_not_called() # No data should be written
        mock_logger.info.assert_any_call("Skipping device XX:XX:XX:XX:XX:XX as it does not match DEVICE_ID YY:YY:YY:YY:YY:YY")

@pytest.mark.asyncio
async def test_device_id_filter_selects_correct_device(monkeypatch): # Added monkeypatch here
    """
    Tests that if DEVICE_ID is set, only data from that device is processed.
    """
    monkeypatch.setenv("DEVICE_ID", "TARGET_DEVICE_ADDR")
    mock_sensor_data = {
        "XX:XX:XX:XX:XX:XX": MagicMock(
            address="XX:XX:XX:XX:XX:XX",
            data={"modelFriendlyName": "Meter1", "data": {"temperature": 21.0, "humidity": 51}},
        ),
        "TARGET_DEVICE_ADDR": MagicMock(
            address="TARGET_DEVICE_ADDR",
            data={"modelFriendlyName": "TargetMeter", "data": {"temperature": 22.5, "humidity": 62, "battery": 88}},
        ),
        "ZZ:ZZ:ZZ:ZZ:ZZ:ZZ": MagicMock(
            address="ZZ:ZZ:ZZ:ZZ:ZZ:ZZ",
            data={"modelFriendlyName": "Meter3", "data": {"temperature": 23.0, "humidity": 53}},
        ),
    }

    mock_get_switchbot_devices = AsyncMock()
    mock_get_switchbot_devices.get_tempsensors.return_value = mock_sensor_data

    mock_influx_client_instance = MagicMock()
    mock_write_api = MagicMock()
    mock_influx_client_instance.write_api.return_value = mock_write_api

    with patch('main.GetSwitchbotDevices', return_value=mock_get_switchbot_devices) as mock_get_devices, \
        patch('main.InfluxDBClient', return_value=mock_influx_client_instance) as mock_influx_client, \
        patch('main.logger') as mock_logger:

        await reader_main_module.main() # Changed: Call main function from the module

        mock_get_devices.assert_called_once() # Ensure GetSwitchbotDevices was called
        mock_write_api.write.assert_called_once() # Should be called exactly once for the target device
        args, kwargs = mock_write_api.write.call_args
        point = kwargs['record']
        assert point._tags['device_id'] == "TARGET_DEVICE_ADDR"
        assert point._fields['temperature'] == 22.5

        mock_logger.info.assert_any_call("Skipping device XX:XX:XX:XX:XX:XX as it does not match DEVICE_ID TARGET_DEVICE_ADDR")
        mock_logger.info.assert_any_call("Skipping device ZZ:ZZ:ZZ:ZZ:ZZ:ZZ as it does not match DEVICE_ID TARGET_DEVICE_ADDR")
        mock_logger.info.assert_any_call("Data written to InfluxDB for device TARGET_DEVICE_ADDR")

