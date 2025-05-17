import os
import sys

import pytest
from unittest.mock import patch, MagicMock
import importlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# `main` モジュールをインポートする前に、`asyncio.run` がパッチされていることを確認
# これは、`main.py` の最下部にある `asyncio.run(main())` の呼び出しを避けるため
# ただし、`if __name__ == "__main__":` ブロックで囲む方がより良い解決策
with patch('asyncio.run', MagicMock()) as mock_run:
    import main as reader_main

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
@patch('main.GetSwitchbotDevices')
@patch('main.InfluxDBClient')
async def test_environment_variables_present(MockInfluxDBClient, MockGetSwitchbotDevices, mock_env_vars, mock_switchbot_devices, caplog):
    """環境変数がすべて設定されている場合のテスト"""
    MockGetSwitchbotDevices.return_value.get_tempsensors.return_value = mock_switchbot_devices

    # load_dotenv() が if __name__ == "__main__" ブロックに移動したため、
    # テスト時には main.py のトップレベルでは .env は読み込まれない。
    # monkeypatch で設定した環境変数がそのまま使われる。
    importlib.reload(reader_main)
    
    # 環境変数が正しく設定されていることをデバッグ
    print("Environment Variables:")
    for key, _ in mock_env_vars.items():
        print(f"{key}: {os.getenv(key)}")

    try:
        await reader_main.main() # main関数を呼び出し
    except OSError: # EnvironmentError は OSError として扱われる
        pytest.fail("OSError (EnvironmentError) was raised unexpectedly with all env vars set.")
    except Exception as e:
        pytest.fail(f"An unexpected exception occurred: {e}")

    # ログ出力を検証 (オプション)
    # assert "Data written to InfluxDB" in caplog.text

@pytest.mark.asyncio
async def test_environment_variables_missing_url(monkeypatch):
    """INFLUXDB_URL が不足している場合に OSError が発生するかをテスト"""
    monkeypatch.setenv("INFLUXDB_TOKEN", "test_token")
    monkeypatch.setenv("INFLUXDB_ORG", "test_org")
    monkeypatch.setenv("INFLUXDB_BUCKET", "test_bucket")
    monkeypatch.setenv("INFLUXDB_MEASUREMENT", "test_measurement")
    monkeypatch.delenv("INFLUXDB_URL", raising=False) # 明示的に削除

    with pytest.raises(OSError) as excinfo:
        importlib.reload(reader_main)
        await reader_main.main()
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
        importlib.reload(reader_main)
        await reader_main.main()
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
        importlib.reload(reader_main)
        await reader_main.main()
    assert "Missing InfluxDB environment variables." in str(excinfo.value)

