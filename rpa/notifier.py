"""
Step 7 — Notify

Sends a notification after processing completes (or fails).
Supports:
  - Slack webhook (set SLACK_WEBHOOK_URL in .env)
  - Email via Gmail SMTP (set EMAIL_* vars in .env)

Both are optional — the bot works fine without either.
"""

import os
import logging
import smtplib
import json
from email.mime.text import MIMEText

try:
    import urllib.request
except ImportError:
    pass

log = logging.getLogger("rpa.notifier")


def _notify_slack(message: str):
    """Send a Slack notification via incoming webhook."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return

    try:
        payload = json.dumps({"text": message}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        log.info("[NOTIFY] Slack notification sent.")
    except Exception as e:
        log.warning(f"[NOTIFY] Slack failed: {e}")


def _notify_email(subject: str, body: str):
    """Send an email notification via Gmail SMTP."""
    smtp_user = os.getenv("EMAIL_USER", "")
    smtp_pass = os.getenv("EMAIL_PASSWORD", "")
    to_addr   = os.getenv("EMAIL_TO", "")

    if not all([smtp_user, smtp_pass, to_addr]):
        return

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"]    = smtp_user
        msg["To"]      = to_addr

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_addr, msg.as_string())

        log.info(f"[NOTIFY] Email sent to {to_addr}.")
    except Exception as e:
        log.warning(f"[NOTIFY] Email failed: {e}")


def notify_success(filename: str, stats: dict, output_path: str):
    """Notify on successful processing."""
    lines = [
        f"✅ PDF processed successfully!",
        f"",
        f"File     : {filename}",
        f"Pages    : {stats.get('total_pages', '?')}",
        f"Headings : {stats.get('total_headings', 0)}",
        f"Paragraphs: {stats.get('total_paragraphs', 0)}",
        f"Tables   : {stats.get('total_tables', 0)}",
        f"Images   : {stats.get('total_images', 0)}",
        f"Output   : {output_path}",
    ]
    message = "\n".join(lines)
    log.info(f"[NOTIFY] {message}")
    _notify_slack(message)
    _notify_email(f"[PDF RPA Bot] Processed: {filename}", message)


def notify_failure(filename: str, error: str):
    """Notify on processing failure."""
    message = f"❌ PDF processing FAILED!\nFile: {filename}\nError: {error}"
    log.error(f"[NOTIFY] {message}")
    _notify_slack(message)
    _notify_email(f"[PDF RPA Bot] FAILED: {filename}", message)
