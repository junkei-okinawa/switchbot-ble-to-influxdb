# systemdによるSwitchBot BLE to InfluxDBの自動実行設定

このディレクトリには、Raspberry Pi等のLinux環境で`switchbot-ble-to-influxdb`を10分ごとに自動実行するためのsystemd Unitファイルが含まれています。

## ファイル構成
- `switchbot-ble-to-influxdb.service`: アプリ本体を実行するService Unit
- `switchbot-ble-to-influxdb.timer`: 10分ごとにServiceを起動するTimer Unit

## 設定手順
1. Serviceファイル内の内容を環境に合わせて修正してください：
   - `User`：サービスを実行するユーザー名（例：`pi`）
   - `WorkingDirectory`：アプリのディレクトリ（例：`/home/pi/switchbot-ble-to-influxdb`）
   - `ExecStart`：アプリの実行コマンド（例：`/usr/bin/python3 /home/pi/switchbot-ble-to-influxdb/main.py`）

   **修正例：**
   ```ini
   [Service]
   Type=oneshot
   User=pi
   WorkingDirectory=/home/pi/switchbot-ble-to-influxdb
   ExecStart=/usr/bin/python3 /home/pi/switchbot-ble-to-influxdb/main.py
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
   systemctl status switchbot-ble-to-influxdb.service
   journalctl -u switchbot-ble-to-influxdb.service
   ```

## 備考
- サービスは10分ごとに1回だけ実行されます（間欠動作）。
- サービスの実行ユーザーやパスは環境に合わせて必ず修正してください。
- サービスのログは`journalctl`で確認できます。
