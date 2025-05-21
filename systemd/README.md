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
     - `ExecStart`: Set the full command to run your app (e.g., `/usr/bin/python3 /home/pi/switchbot-ble-to-influxdb/main.py`)
   
   **Example:**
   ```ini
   [Service]
   Type=oneshot
   User=pi
   WorkingDirectory=/home/pi/switchbot-ble-to-influxdb
   ExecStart=/usr/bin/python3 /home/pi/switchbot-ble-to-influxdb/main.py
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
   systemctl status switchbot-ble-to-influxdb.service
   journalctl -u switchbot-ble-to-influxdb.service
   ```

## Notes
- The service runs once every 10 minutes (intermittent operation).
- Be sure to update the user and paths in the service file to match your environment.
- Service logs can be checked with `journalctl`.
