import os
import asyncio
import logging

from switchbot.discovery import GetSwitchbotDevices

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from dotenv import load_dotenv

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Main Function ---
async def main():
    # --- InfluxDB Setup ---
    token = os.getenv("INFLUXDB_TOKEN")
    url = os.getenv("INFLUXDB_URL")
    org = os.getenv("INFLUXDB_ORG")
    bucket = os.getenv("INFLUXDB_BUCKET")
    mem = os.getenv("INFLUXDB_MEASUREMENT")
    device_id = os.getenv("DEVICE_ID")


    # デバッグ用 環境変数を表示
    logger.debug("Environment Variables:")
    for key in ["INFLUXDB_TOKEN", "INFLUXDB_URL", "INFLUXDB_ORG", "INFLUXDB_BUCKET", "INFLUXDB_MEASUREMENT"]:
        logger.debug(f"{key}: {os.getenv(key)}")
    if not token or not url or not org or not bucket or not mem:
        logger.error("INFLUXDB_TOKEN, INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET, and INFLUXDB_MEASUREMENT must be set in the environment variables.")
        raise EnvironmentError("Missing InfluxDB environment variables.")

    client = InfluxDBClient(url=url, token=token)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    logger.info("InfluxDB client initialized.")

    sensors = await GetSwitchbotDevices().discover(scan_timeout=60)
    if not sensors:
        logger.warning("No temperature sensors found. Exiting.")
        return
    # logger.info(sensors)
    # logger.info(sensors['7688CA37-E4ED-E6F2-5D7A-B71CCE01D61D'])
    for address in sensors:
        if address == device_id:
            logger.info(f"address: {sensors[address].address}")
        else:
            logger.info(f"Skipping device {sensors[address].address} as it does not match DEVICE_ID {device_id}")
            continue

        logger.info(f"Friendly name: {sensors[address].data['modelFriendlyName']}")
        logger.info(f"temperature: {sensors[address].data['data']['temperature']} °C")
        logger.info(f"humidity: {sensors[address].data['data']['humidity']} %")

        # Write data to InfluxDB
        point = (
            Point(mem)
                .tag("device_id", sensors[address].address)
                .tag("friendly_name", sensors[address].data['modelFriendlyName'])
                .field("temperature", float(sensors[address].data['data']['temperature']))
                .field("humidity", int(sensors[address].data['data']['humidity']))
        )

        if "battery" in sensors[address].data['data']:
            point = point.field("battery", int(sensors[address].data['data']['battery']))
            logger.info(f"battery: {sensors[address].data['data']['battery']} %")

        try:
            write_api.write(bucket=bucket, org=org, record=point)
            logger.info(f"Data written to InfluxDB for device {sensors[address].address}")
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())
