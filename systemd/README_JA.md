# systemdによるSwitchBot BLE to InfluxDBの自動実行設定

このディレクトリには、Raspberry Pi等のLinux環境で`switchbot-ble-to-influxdb`を10分ごとに自動実行するためのsystemd Unitファイルが含まれています。

## ファイル構成
- `switchbot-ble-to-influxdb.service`: アプリ本体を実行するService Unit
- `switchbot-ble-to-influxdb.timer`: 10分ごとにServiceを起動するTimer Unit

## 前提条件
リポジトリのルートディレクトリで以下の手順を実行しアプリケーションが動作することを確認しておく
```bash
uv venv # 仮想環境作成
source .venv/bin/activate # 仮想環境有効か
uv sync # 依存関係のインストール
.venv/bin/python main.py
```

## 設定手順
1. Serviceファイル内の内容を環境に合わせて修正してください：
    - `User`：サービスを実行するユーザー名（例：`pi`）
    - `WorkingDirectory`：アプリのディレクトリ（例：`/home/pi/switchbot-ble-to-influxdb`）
    - `ExecStart`：アプリの実行コマンド（例：`/home/pi/switchbot-ble-to-influxdb/.venv/bin/python main.py`）

    **修正例：**
    ```ini
    [Service]
    Type=oneshot
    User=pi
    WorkingDirectory=/home/pi/switchbot-ble-to-influxdb
    ExecStart=/home/pi/switchbot-ble-to-influxdb/.venv/bin/python main.py
    ```

2. ユニットファイルの配置
    ```bash
    sudo cp switchbot-ble-to-influxdb.service /etc/systemd/system/
    sudo cp switchbot-ble-to-influxdb.timer /etc/systemd/system/
    ```
3. systemdにリロードを通知
    ```bash
    sudo systemctl daemon-reload
    ```
4. タイマーの有効化と起動
    ```bash
    sudo systemctl enable --now switchbot-ble-to-influxdb.timer
    ```
5. 動作確認
    ```bash
    systemctl status switchbot-ble-to-influxdb.timer
    # ● switchbot-ble-to-influxdb.timer - Run switchbot-ble-to-influxdb every 10 minutes
    #      Loaded: loaded (/etc/systemd/system/switchbot-ble-to-influxdb.timer; enabled; preset: enabled)
    #      Active: active (waiting) since Wed 2025-05-21 09:35:27 JST; 6s ago
    #      Trigger: Wed 2025-05-21 09:40:00 JST; 4min 26s left
    #  Triggers: ● switchbot-ble-to-influxdb.service

    #  May 21 09:35:27 <hostname>[1]: Started switchbot-ble-to-influxdb.timer - Run switchbot-ble-to-influxdb every 10 minutes.
    ```

    ```bash
    systemctl status switchbot-ble-to-influxdb.service
    # ○ switchbot-ble-to-influxdb.service - Run switchbot-ble-to-influxdb script periodically
    #     Loaded: loaded (/etc/systemd/system/switchbot-ble-to-influxdb.service; static)
    #     Active: inactive (dead)
    # TriggeredBy: ● switchbot-ble-to-influxdb.timer
    ```

    設定したtimerの初回実行前は `-- No entries --`が表示されます。
    ```bash
    journalctl -u switchbot-ble-to-influxdb.service
    # -- No entries --
    ```

    初回実行後は以下のようなログが表示されます。
    ```bash
    journalctl -u switchbot-ble-to-influxdb.service
    # May 21 09:40:11 <hostname> systemd[1]: Starting switchbot-ble-to-influxdb.service - Run switchbot-ble-to-influxdb script periodically...
    # May 21 09:40:11 <hostname> uv[164698]: Using CPython 3.12.9
    # May 21 09:40:11 <hostname> uv[164698]: Creating virtual environment at: .venv
    # May 21 09:40:11 <hostname> uv[164698]: Installed 38 packages in 359ms
    # May 21 09:40:11 <hostname> uv[164711]: python main.py
    # May 21 09:40:17 <hostname> uv[164714]: 2025-05-21 09:44:17,841 - INFO - InfluxDB client initialized.
    # May 21 09:41:17 <hostname> uv[164714]: 2025-05-21 09:45:17,890 - INFO - address: CA:5F:45:86:47:93
    # May 21 09:41:17 <hostname> uv[164714]: 2025-05-21 09:45:17,890 - INFO - Friendly name: Indoor/Outdoor Meter
    # May 21 09:41:17 <hostname> uv[164714]: 2025-05-21 09:45:17,891 - INFO - temperature: 29.5 °C
    # May 21 09:41:17 <hostname> uv[164714]: 2025-05-21 09:45:17,891 - INFO - humidity: 51 %
    # May 21 09:41:17 <hostname> uv[164714]: 2025-05-21 09:45:17,892 - INFO - battery: 90 %
    # May 21 09:41:17 <hostname> uv[164714]: 2025-05-21 09:45:17,921 - INFO - Data written to InfluxDB for device CA:5F:45:86:47:93
    # May 21 09:41:18 <hostname> systemd[1]: switchbot-ble-to-influxdb.service: Deactivated successfully.
    # May 21 09:41:18 <hostname> systemd[1]: Finished switchbot-ble-to-influxdb.service - Run switchbot-ble-to-influxdb script periodically.
    # May 21 09:41:18 <hostname> systemd[1]: switchbot-ble-to-influxdb.service: Consumed 6.527s CPU time.
    ```

## 備考
- サービスは10分ごとに1回だけ実行されます（間欠動作）。
- サービスの実行ユーザーやパスは環境に合わせて必ず修正してください。
- サービスのログは`journalctl`で確認できます。
