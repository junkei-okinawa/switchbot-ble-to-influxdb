import os
import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bleak.exc import BleakDBusError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

@pytest.fixture
def mock_env_vars(monkeypatch):
    env_vars = {
        "INFLUXDB_TOKEN": "test_token",
        "INFLUXDB_URL": "http://localhost:8086",
        "INFLUXDB_ORG": "test_org",
        "INFLUXDB_BUCKET": "test_bucket",
        "INFLUXDB_MEASUREMENT": "test_measurement"
    }
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)
    return env_vars

@pytest.fixture
def mock_switchbot_devices():
    mock_device = MagicMock()
    mock_device.address = "test_address"
    mock_device.data = {
        "modelFriendlyName": "Test Meter",
        "data": {
            "temperature": 25.5,
            "humidity": 60,
            "battery": 100
        }
    }
    return {"test_address": mock_device}

@pytest.mark.asyncio
async def test_environment_variables_present(mock_env_vars, mock_switchbot_devices, caplog):
    """環境変数がすべて設定されている場合のテスト"""
    with patch('main._scan_switchbot_devices_once', new=AsyncMock(return_value=mock_switchbot_devices)), \
         patch('main.InfluxDBClient'):
        import main
        # 環境変数が正しく設定されていることをデバッグ
        print("Environment Variables:")
        for key, _ in mock_env_vars.items():
            print(f"{key}: {os.getenv(key)}")
        try:
            await main.main() # main関数を呼び出し
        except OSError: # EnvironmentError は OSError として扱われる
            pytest.fail("OSError (EnvironmentError) was raised unexpectedly with all env vars set.")
        except Exception as e:
            pytest.fail(f"An unexpected exception occurred: {e}")

@pytest.mark.asyncio
async def test_environment_variables_missing_url(monkeypatch):
    """INFLUXDB_URL が不足している場合に OSError が発生するかをテスト"""
    monkeypatch.setenv("INFLUXDB_TOKEN", "test_token")
    monkeypatch.setenv("INFLUXDB_ORG", "test_org")
    monkeypatch.setenv("INFLUXDB_BUCKET", "test_bucket")
    monkeypatch.setenv("INFLUXDB_MEASUREMENT", "test_measurement")
    monkeypatch.delenv("INFLUXDB_URL", raising=False) # 明示的に削除

    with pytest.raises(OSError) as excinfo:
        import main
        await main.main()
    assert "Missing InfluxDB environment variables." in str(excinfo.value)

@pytest.mark.asyncio
async def test_environment_variables_missing_token(monkeypatch):
    """INFLUXDB_TOKEN が不足している場合に OSError が発生するかをテスト"""
    monkeypatch.setenv("INFLUXDB_URL", "http://localhost:8086")
    monkeypatch.setenv("INFLUXDB_ORG", "test_org")
    monkeypatch.setenv("INFLUXDB_BUCKET", "test_bucket")
    monkeypatch.setenv("INFLUXDB_MEASUREMENT", "test_measurement")
    monkeypatch.delenv("INFLUXDB_TOKEN", raising=False) # 明示的に削除

    with pytest.raises(OSError) as excinfo:
        import main
        await main.main()
    assert "Missing InfluxDB environment variables." in str(excinfo.value)

@pytest.mark.asyncio
async def test_environment_variables_missing_measurement(monkeypatch):
    """INFLUXDB_MEASUREMENT が不足している場合に OSError が発生するかをテスト"""
    monkeypatch.setenv("INFLUXDB_TOKEN", "test_token")
    monkeypatch.setenv("INFLUXDB_URL", "http://localhost:8086")
    monkeypatch.setenv("INFLUXDB_ORG", "test_org")
    monkeypatch.setenv("INFLUXDB_BUCKET", "test_bucket")
    monkeypatch.delenv("INFLUXDB_MEASUREMENT", raising=False) # 明示的に削除

    with pytest.raises(OSError) as excinfo:
        import main
        await main.main()
    assert "Missing InfluxDB environment variables." in str(excinfo.value)


@pytest.mark.asyncio
async def test_discovery_retries_on_bleak_dbus_in_progress():
    """Bluetooth discovery should retry the whole scan when the attempt is busy."""
    discovered_sensor = MagicMock()

    with patch(
        "main._scan_switchbot_devices_once",
        side_effect=[
            BleakDBusError("org.bluez.Error.InProgress", ["Operation already in progress"]),
            {"test_address": discovered_sensor},
        ],
    ) as mock_scan_once, patch("main.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        import main

        result = await main.discover_switchbot_devices(scan_timeout=1)

    assert result == {"test_address": discovered_sensor}
    assert mock_scan_once.call_count == 2
    mock_sleep.assert_awaited_once_with(main.DISCOVERY_RETRY_BASE_DELAY_SECONDS)


@pytest.mark.asyncio
async def test_discovery_returns_partial_results_when_stop_is_busy():
    """Bluetooth discovery should return collected devices if stop() keeps failing."""
    discovered_sensor = MagicMock()
    discovered_sensor.address = "test_address"

    class FakeScanner:
        def __init__(self, detection_callback):
            self.detection_callback = detection_callback
            self.start = AsyncMock(side_effect=self._start)
            self.stop = AsyncMock(
                side_effect=[
                    BleakDBusError("org.bluez.Error.InProgress", ["Operation already in progress"]),
                    BleakDBusError("org.bluez.Error.InProgress", ["Operation already in progress"]),
                    BleakDBusError("org.bluez.Error.InProgress", ["Operation already in progress"]),
                ]
            )

        async def _start(self):
            device = MagicMock()
            device.address = "test_address"
            self.detection_callback(device, MagicMock())

    with patch("main.BleakScanner", side_effect=lambda **kwargs: FakeScanner(kwargs["detection_callback"])), \
        patch("main.parse_advertisement_data", return_value=discovered_sensor), \
        patch("main.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        import main

        result = await main._scan_switchbot_devices_once(scan_timeout=1)

    assert result == {"test_address": discovered_sensor}
    mock_sleep.assert_any_await(1)
    assert mock_sleep.await_count == 3
    # stop() is retried three times inside the single scan attempt
    # and no outer retry is needed because partial data is returned.


@pytest.mark.asyncio
async def test_create_scanner_uses_configured_adapter(monkeypatch):
    """Scanner creation should respect an explicit adapter override."""
    monkeypatch.setenv("BLEAK_ADAPTER", "hci1")
    discovered_devices = {}

    with patch("main.BleakScanner") as mock_scanner:
        import main

        main._create_scanner(discovered_devices)

    mock_scanner.assert_called_once()
    _, kwargs = mock_scanner.call_args
    assert kwargs["adapter"] == "hci1"


@pytest.mark.asyncio
async def test_scan_attempt_cleans_up_scanner_when_sleep_is_cancelled():
    """The scanner should still be stopped if the scan coroutine is cancelled."""
    stop_called = AsyncMock()

    class FakeScanner:
        def __init__(self, detection_callback):
            self.detection_callback = detection_callback
            self.start = AsyncMock(return_value=None)
            self.stop = stop_called

    with patch(
        "main.BleakScanner",
        side_effect=lambda **kwargs: FakeScanner(kwargs["detection_callback"]),
    ), patch("main.parse_advertisement_data", return_value=None), patch(
        "main.asyncio.sleep", new=AsyncMock(side_effect=asyncio.CancelledError())
    ):
        import main

        with pytest.raises(asyncio.CancelledError):
            await main._scan_switchbot_devices_once(scan_timeout=1)

    assert stop_called.await_count == 1
