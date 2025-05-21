# systemd Setup for SwitchBot BLE to InfluxDB

This directory contains systemd unit files to run `switchbot-ble-to-influxdb` automatically every 10 minutes on Linux environments such as Raspberry Pi.

## Files
- `switchbot-ble-to-influxdb.service`: Service unit to run the application
- `switchbot-ble-to-influxdb.timer`: Timer unit to trigger the service every 10 minutes

## Setup Steps
1. Edit the Service file to match your environment:
   - Open `switchbot-ble-to-influxdb.service` and update the following fields:
     - `User`: Set to the user that should run the service (e.g., `pi`)
     - `WorkingDirectory`: Set to the directory where your app resides (e.g., `/home/pi/switchbot-ble-to-influxdb`)
     - `ExecStart`: Set the full command to run your app (e.g., `/home/pi/switchbot-ble-to-influxdb/.venv/bin/python main.py`)
   
   **Example:**
   ```ini
   [Service]
   Type=oneshot
   User=pi
   WorkingDirectory=/home/pi/switchbot-ble-to-influxdb
   ExecStart=/home/pi/switchbot-ble-to-influxdb/.venv/bin/python main.py
   ```

2. Copy the unit files to the systemd directory:
   ```bash
   sudo cp switchbot-ble-to-influxdb.service /etc/systemd/system/
   sudo cp switchbot-ble-to-influxdb.timer /etc/systemd/system/
   ```

3. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

4. Enable and start the timer:
   ```bash
   sudo systemctl enable --now switchbot-ble-to-influxdb.timer
   ```

5. Check status:
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

    If it has never been executed, `-- No entries --` will be displayed.
    ```bash
    journalctl -u switchbot-ble-to-influxdb.service
    # -- No entries --
    ```

    Logs are displayed after the first execution.
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

## Notes
- The service runs once every 10 minutes (intermittent operation).
- Be sure to update the user and paths in the service file to match your environment.
- Service logs can be checked with `journalctl`.
