"""Ping command builder and output parser for network devices.

Pings are sent to the remote device as a CLI command over the existing SSH
session (Netmiko) — they are NOT executed on the application server.
"""

import re


def build_ping_command(destination: str, count: int, device_type: str) -> str:
    """
    Return the appropriate ping CLI command for the device type.

    Most Cisco-family and Arista devices use 'repeat' for the packet count;
    NX-OS and Junos use 'count'.
    """
    dt = device_type.lower()

    if "junos" in dt or "juniper" in dt:
        return f"ping {destination} count {count} rapid"
    elif "nxos" in dt:
        return f"ping {destination} count {count}"
    else:
        # Cisco IOS, IOS-XE, IOS-XR, Arista EOS, and most others
        return f"ping {destination} repeat {count}"


def parse_ping_success(output: str) -> bool:
    """
    Return True if the device ping output indicates at least one reply.

    Handles output formats from Cisco IOS/IOS-XE/NX-OS, Arista EOS,
    and Juniper JunOS.  Falls back to scanning for '!' (Cisco success
    character) when no known pattern is matched.
    """
    lower = output.lower()

    # Cisco IOS / IOS-XE / IOS-XR
    # "Success rate is 80 percent (4/5)"  →  success
    # "Success rate is 0 percent (0/5)"   →  failure
    m = re.search(r"success rate is (\d+) percent", lower)
    if m:
        return int(m.group(1)) > 0

    # Cisco NX-OS / Arista EOS / Junos
    # "5 packets transmitted, 4 packets received"
    m = re.search(r"(\d+)\s+packets?\s+received", lower)
    if m:
        return int(m.group(1)) > 0

    # Generic fallback: '!' means a reply was received on most Cisco platforms
    return "!" in output
