"""Run ICMP pings from the local host using the system ping binary."""

import platform
import subprocess


def ping_host(destination: str, count: int = 4) -> tuple[str, bool]:
    """
    Ping a single destination from the host machine.

    Returns:
        (output, success) where output is the raw ping text and
        success is True when the ping binary exits with code 0.
    """
    system = platform.system().lower()

    if system == "windows":
        cmd = ["ping", "-n", str(count), destination]
    else:
        cmd = ["ping", "-c", str(count), destination]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * 5 + 10,
        )
        output = result.stdout.strip()
        if result.returncode != 0 and result.stderr.strip():
            output = (output + "\n" + result.stderr.strip()).strip()
        return output or "(no output)", result.returncode == 0

    except subprocess.TimeoutExpired:
        return f"ERROR: ping to {destination} timed out", False
    except FileNotFoundError:
        return "ERROR: ping binary not found on this system", False
    except Exception as exc:
        return f"ERROR: {exc}", False
