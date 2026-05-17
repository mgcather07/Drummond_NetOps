from netmiko import ConnectHandler
from dotenv import load_dotenv
import os

load_dotenv()


def show_version(command: str) -> str:

    parts = command.split()

    if len(parts) < 3:
        return "Usage: /show version <device-ip>"

    host = parts[2]

    try:

        device = {
            "device_type": "cisco_ios",
            "host": host,
            "username": os.getenv("NETWORK_USERNAME"),
            "password": os.getenv("NETWORK_PASSWORD"),
            "disabled_algorithms": {
                "kex": [
                    "diffie-hellman-group16-sha512",
                    "diffie-hellman-group18-sha512",
                    "diffie-hellman-group14-sha256",
                    "diffie-hellman-group-exchange-sha256",
                ]
            },
        }

        connection = ConnectHandler(**device)

        output = connection.send_command("show version")

        connection.disconnect()

        return f"""
✅ Connected to {host}

{output[:3000]}
"""

    except Exception as e:

        return f"❌ SSH connection failed:\n{str(e)}"