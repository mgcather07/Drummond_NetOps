from dotenv import load_dotenv
import os
import time
import re
from netmiko import ConnectHandler

load_dotenv()

CUCM_HOST = os.getenv("CUCM_HOST")
CUCM_SSH_USERNAME = os.getenv("CUCM_SSH_USERNAME")
CUCM_SSH_PASSWORD = os.getenv("CUCM_SSH_PASSWORD")


def read_until_prompt(connection, max_wait_seconds: int = 90) -> str:
    output = ""
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        chunk = connection.read_channel()

        if chunk:
            output += chunk

            if output.strip().endswith("admin:"):
                break

        time.sleep(2)

    return output


def get_dbreplication_status() -> dict:
    connection = None

    detail_command = None
    detail_output = ""
    clean_output = ""

    try:
        device = {
            "device_type": "generic",
            "host": CUCM_HOST,
            "username": CUCM_SSH_USERNAME,
            "password": CUCM_SSH_PASSWORD,
            "port": 22,
        }

        connection = ConnectHandler(**device)
        connection.find_prompt()

        connection.write_channel("utils dbreplication runtimestate\n")

        output = read_until_prompt(
            connection=connection,
            max_wait_seconds=120
        )

        clean_output = output.strip()
        output_lower = clean_output.lower()

        match = re.search(r"'(file view activelog[^']+)'", clean_output)

        if match:
            detail_command = match.group(1)

            connection.write_channel(f"{detail_command}\n")

            detail_output = read_until_prompt(
                connection=connection,
                max_wait_seconds=90
            ).strip()

        if "errors or data mismatches were found" in output_lower:
            if "(2) setup completed" in output_lower and "y/y/y" in output_lower:
                status = "🟡 Warning - Setup good, previous mismatch detected"
            else:
                status = "❌ Bad - Replication mismatch detected"

        elif "(2) setup completed" in output_lower and "y/y/y" in output_lower:
            status = "✅ Good"

        else:
            status = "⚠️ Review Required"

        print("DBREPLICATION RAW OUTPUT:")
        print(clean_output)

        if detail_command:
            print("DBREPLICATION DETAIL COMMAND:")
            print(detail_command)

        return {
            "status": status,
            "output": clean_output,
            "detail_command": detail_command,
            "detail_output": detail_output,
            "error": None,
        }

    except Exception as e:
        return {
            "status": f"❌ Failed - {type(e).__name__}: {str(e)}",
            "output": clean_output,
            "detail_command": detail_command,
            "detail_output": detail_output,
            "error": str(e),
        }

    finally:
        if connection:
            connection.disconnect()