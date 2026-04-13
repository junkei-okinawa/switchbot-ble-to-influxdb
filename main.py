import os
import asyncio
import logging
from collections.abc import Callable

from bleak import BleakScanner
from bleak.exc import BleakDBusError
from switchbot.adv_parser import parse_advertisement_data
from switchbot.discovery import CONNECT_LOCK

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from dotenv import load_dotenv

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SCAN_TIMEOUT_SECONDS = 60
DISCOVERY_RETRY_COUNT = 3
DISCOVERY_RETRY_BASE_DELAY_SECONDS = 1.0
BLUEZ_IN_PROGRESS_ERROR = "org.bluez.Error.InProgress"
BLEAK_ADAPTER_ENV = "BLEAK_ADAPTER"


def _build_detection_callback(discovered_devices: dict) -> Callable[[object, object], None]:
    """Build a callback that accumulates SwitchBot advertisements."""
    def detection_callback(device, advertisement_data) -> None:
        discovery = parse_advertisement_data(device, advertisement_data)
        if discovery:
            discovered_devices[discovery.address] = discovery

    return detection_callback


async def _stop_scanner_with_retry(scanner: BleakScanner) -> None:
    """Stop the scanner, retrying if BlueZ reports the adapter is busy."""
    delay_seconds = DISCOVERY_RETRY_BASE_DELAY_SECONDS

    for attempt in range(1, DISCOVERY_RETRY_COUNT + 1):
        try:
            await scanner.stop()
            return
        except BleakDBusError as exc:
            if getattr(exc, "dbus_error", None) != BLUEZ_IN_PROGRESS_ERROR:
                raise

            if attempt == DISCOVERY_RETRY_COUNT:
                raise

            logger.warning(
                "Bluetooth adapter is busy while stopping discovery (%s/%s). Retrying in %.1f seconds.",
                attempt,
                DISCOVERY_RETRY_COUNT,
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)
            delay_seconds *= 2


def _create_scanner(discovered_devices: dict) -> BleakScanner:
    """Create a scanner, optionally using the configured adapter."""
    scanner_kwargs: dict = {
        "detection_callback": _build_detection_callback(discovered_devices),
    }
    if adapter := os.getenv(BLEAK_ADAPTER_ENV):
        scanner_kwargs["adapter"] = adapter

    return BleakScanner(**scanner_kwargs)


async def _scan_switchbot_devices_once(scan_timeout: int) -> dict:
    """Run one Bluetooth scan and return the collected advertisements."""
    discovered_devices: dict = {}
    scanner = _create_scanner(discovered_devices)

    async with CONNECT_LOCK:
        await scanner.start()
        try:
            await asyncio.sleep(scan_timeout)
        finally:
            try:
                await asyncio.shield(_stop_scanner_with_retry(scanner))
            except BleakDBusError as exc:
                if getattr(exc, "dbus_error", None) != BLUEZ_IN_PROGRESS_ERROR:
                    raise

                if discovered_devices:
                    logger.warning(
                        "Bluetooth discovery stopped with InProgress, but %s devices were already collected. Using partial results.",
                        len(discovered_devices),
                    )
                    return discovered_devices

                raise

    return discovered_devices


async def discover_switchbot_devices(scan_timeout: int = SCAN_TIMEOUT_SECONDS) -> dict:
    """Discover SwitchBot devices, retrying transient BlueZ busy errors."""
    delay_seconds = DISCOVERY_RETRY_BASE_DELAY_SECONDS

    for attempt in range(1, DISCOVERY_RETRY_COUNT + 1):
        try:
            return await _scan_switchbot_devices_once(scan_timeout)
        except BleakDBusError as exc:
            if getattr(exc, "dbus_error", None) != BLUEZ_IN_PROGRESS_ERROR:
                raise

            if attempt == DISCOVERY_RETRY_COUNT:
                logger.exception(
                    "Bluetooth discovery failed after %s attempts because the adapter remained busy.",
                    attempt,
                )
                raise

            logger.warning(
                "Bluetooth adapter is busy during discovery (%s/%s). Retrying in %.1f seconds.",
                attempt,
                DISCOVERY_RETRY_COUNT,
                delay_seconds,
            )
            await asyncio.sleep(delay_seconds)
            delay_seconds *= 2

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

    sensors = await discover_switchbot_devices()
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
