"""
telos_disconnect.py

Checks the Telos Z/IP ONE status page to see if a call is still active.
If connected, sends a disconnect command and polls until confirmed idle.
Sends an AWS SES alert only if the disconnect fails.

Environment variables:
    TELOS_AUTH      — Base64-encoded Basic Auth credentials for the Telos unit
    EMAIL_TO        — Destination email address for alerts
    EMAIL_FROM      — Verified SES sender address
    AWS_REGION      — AWS region for SES (default: us-west-2)
"""

import os
import sys
import time

import boto3
import requests
from botocore.exceptions import ClientError

from logger import get_logger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TELOS_HOST = "http://10.10.0.20"
STATUS_URL = f"{TELOS_HOST}/status"
DISCONNECT_URL = f"{TELOS_HOST}/cmd/call/disconnect"

TELOS_AUTH = os.getenv("TELOS_AUTH", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Polling: check status up to MAX_RETRIES times, waiting POLL_INTERVAL seconds between
POLL_INTERVAL = 10
MAX_RETRIES = 6  # 60 seconds total

SCRIPT_NAME = "telos_disconnect"
logger = get_logger(SCRIPT_NAME, __file__)

# Auth headers only needed for the disconnect command
AUTH_HEADERS = {
    "Authorization": f"Basic {TELOS_AUTH}",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def send_ses_email(subject: str, body: str) -> None:
    """Send a plain-text alert email via AWS SES."""
    if not EMAIL_TO or not EMAIL_FROM:
        logger.warning(
            "EMAIL_TO or EMAIL_FROM not set — skipping email alert",
            extra={"script": SCRIPT_NAME},
        )
        return

    ses = boto3.client("ses", region_name=AWS_REGION)
    try:
        ses.send_email(
            Source=EMAIL_FROM,
            Destination={"ToAddresses": [EMAIL_TO]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        logger.info(f"Alert email sent: {subject}", extra={"script": SCRIPT_NAME})
    except ClientError as e:
        logger.error(
            f"SES send failed: {e.response['Error']['Message']}",
            extra={"script": SCRIPT_NAME},
        )


def is_idle() -> bool | None:
    """
    Check the Telos status page (no auth required) for connection state.

    Returns:
        True  — unit is idle ("Not connected")
        False — unit has an active connection
        None  — could not reach the status page
    """
    try:
        resp = requests.get(STATUS_URL, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Could not reach status page: {e}", extra={"script": SCRIPT_NAME})
        return None

    return "Not connected" in resp.text


def send_disconnect() -> bool:
    """Send the disconnect command. Returns True if the request succeeded."""
    try:
        resp = requests.get(DISCONNECT_URL, headers=AUTH_HEADERS, timeout=10)
        resp.raise_for_status()
        logger.info(
            f"Disconnect command sent (HTTP {resp.status_code})",
            extra={"script": SCRIPT_NAME},
        )
        return True
    except requests.RequestException as e:
        logger.error(f"Disconnect request failed: {e}", extra={"script": SCRIPT_NAME})
        return False


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------
def main() -> None:
    logger.info("=== telos_disconnect start ===", extra={"script": SCRIPT_NAME})

    # Step 1 — Check current state
    idle = is_idle()

    if idle is None:
        msg = "Telos Z/IP ONE at 10.10.0.20 is unreachable"
        logger.error(msg, extra={"script": SCRIPT_NAME})
        send_ses_email("Telos unreachable", msg)
        sys.exit(1)

    if idle:
        logger.info("Already disconnected", extra={"script": SCRIPT_NAME})
        logger.info("=== telos_disconnect end ===", extra={"script": SCRIPT_NAME})
        return

    # Step 2 — Still connected; send disconnect
    logger.warning(
        "Call is still active, sending disconnect",
        extra={"script": SCRIPT_NAME},
    )

    if not send_disconnect():
        msg = "Failed to send disconnect command to Telos"
        send_ses_email("Telos disconnect failed", msg)
        sys.exit(1)

    # Step 3 — Poll status page to confirm disconnect
    for attempt in range(1, MAX_RETRIES + 1):
        time.sleep(POLL_INTERVAL)
        logger.info(
            f"Polling status (attempt {attempt}/{MAX_RETRIES})",
            extra={"script": SCRIPT_NAME},
        )

        idle = is_idle()

        if idle is None:
            # Status page disappeared mid-poll — keep trying
            continue

        if idle:
            logger.info(
                "Disconnect confirmed — unit is idle",
                extra={"script": SCRIPT_NAME},
            )
            logger.info("=== telos_disconnect end ===", extra={"script": SCRIPT_NAME})
            return

    # Step 4 — Exhausted retries
    msg = (
        f"Telos still connected after {MAX_RETRIES * POLL_INTERVAL}s of polling. "
        "Manual intervention may be required."
    )
    logger.error(msg, extra={"script": SCRIPT_NAME})
    send_ses_email("Telos NOT disconnected", msg)
    sys.exit(1)


if __name__ == "__main__":
    main()