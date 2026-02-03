import yfinance as yf
import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------- SETTINGS ----------------

ASSETS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD"
}

VOLUME_MULTIPLIER = 2.0
LOOKBACK_DAYS = 20

EMAIL_ADDRESS = os.environ["EMAIL_ADDRESS"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]

# ------------------------------------------


def is_event_today():
    today = datetime.date.today().isoformat()
    events = pd.read_csv("events.csv")
    today_events = events[events["date"] == today]
    return today_events["event"].tolist()


def volume_spike(ticker):
    data = yf.download(ticker, period="2mo", progress=False)

    if data.empty or len(data) < LOOKBACK_DAYS:
        return False, None

    recent_avg = data["Volume"].tail(LOOKBACK_DAYS).mean()
    today_volume = data["Volume"].iloc[-1]

    recent_avg = float(recent_avg)
    today_volume = float(today_volume)

    if today_volume >= VOLUME_MULTIPLIER * recent_avg:
        return True, today_volume

    return False, today_volume


def already_alerted(key):
    try:
        with open("alert_log.txt", "r") as f:
            return key in f.read()
    except FileNotFoundError:
        return False


def log_alert(key):
    with open("alert_log.txt", "a") as f:
        f.write(key + "\n")


def send_email(event, asset, volume):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = f"{asset} market activity during scheduled event"

    body = f"""
A scheduled economic event occurred today.

Asset: {asset}
Event: {event}

Trading volume is significantly higher than its recent average.

Observed Volume: {int(volume)}

This is an informational notice only and does not constitute financial advice.
"""

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)


def main():
    events_today = is_event_today()

    if not events_today:
        return

    for asset_name, ticker in ASSETS.items():
        spike, volume = volume_spike(ticker)

        if not spike:
            continue

        for event in events_today:
            alert_key = f"{event}-{asset_name}"

            if not already_alerted(alert_key):
                send_email(event, asset_name, volume)
                log_alert(alert_key)


if __name__ == "__main__":
    main()
