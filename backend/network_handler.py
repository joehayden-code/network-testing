"""Network device handler using Netmiko.

Credentials are read from environment variables:
  NET_USERNAME  — SSH login username
  NET_PASSWORD  — SSH login password
  NET_SECRET    — Enable/privilege password (optional; leave blank if not needed)

The inventory YAML only needs 'name' (used as the SSH host) and 'device_type'.
SSH port is always 22.
"""

import os

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

_USERNAME = os.environ.get("NET_USERNAME", "")
_PASSWORD = os.environ.get("NET_PASSWORD", "")
_SECRET = os.environ.get("NET_SECRET", "")


def run_device_tests(device, tests):
    """
    Generator that opens one SSH session to a device and yields
    (test_name, command, output) for each enabled test.

    'device' must have at minimum:
      name        — hostname or IP used for the SSH connection
      device_type — Netmiko device type string (e.g. 'cisco_ios')

    Raises ConnectionError if the device cannot be reached or authenticated.
    """
    host = device.get("name", "")
    device_params = {
        "device_type": device.get("device_type", "cisco_ios"),
        "host": host,
        "username": _USERNAME,
        "password": _PASSWORD,
        "port": 22,
        "timeout": 30,
        "session_timeout": 60,
        "banner_timeout": 15,
        "conn_timeout": 10,
        "fast_cli": False,
    }

    if _SECRET:
        device_params["secret"] = _SECRET

    try:
        with ConnectHandler(**device_params) as conn:
            if _SECRET:
                try:
                    conn.enable()
                except Exception:
                    pass  # Not all devices require enable mode

            for test in tests:
                test_name = test.get("name") or test.get("command", "Unknown")
                command = test.get("command", "").strip()

                if not command:
                    yield test_name, command, "ERROR: No command specified"
                    continue

                try:
                    output = conn.send_command(command, read_timeout=30)
                    yield test_name, command, output
                except Exception as exc:
                    yield test_name, command, f"ERROR: {type(exc).__name__}: {exc}"

    except NetmikoAuthenticationException as exc:
        raise ConnectionError(f"Authentication failed: {exc}") from exc
    except NetmikoTimeoutException as exc:
        raise ConnectionError(f"Connection timed out: {exc}") from exc
    except Exception as exc:
        raise ConnectionError(f"{type(exc).__name__}: {exc}") from exc
