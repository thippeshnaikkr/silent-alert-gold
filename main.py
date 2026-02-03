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
    if len(data) < LOOKBACK_DAYS:
        return False, None

    recent_avg = data["Volume"].tail(LOOKBACK_DAYS).mean().item()
    today_volume = data["Volume"].iloc[-1].item()

    if today_volume >= VOLUME_MULTIPLIER * recent_avg:
        return True, today_volume

    return False, today_volume
    
    if len(data) < LOOKBACK_DAYS:
        return False, None

    recent_avg = data["Volume"].tail(LOOKBACK_DAYS).mean().item()
    today_volume = data["Volume"].iloc[-1].item()

    if today_volume >= VOLUME_MULTIPLIER * recent_avg:
        return True, today_volume
    return False, today_volume

def already_alerted(event):
    try:
        with open("alert_log.txt", "r") as f:
            return event in f.read()
    except:
        return False

def log_alert(event):
    with open("alert_log.txt", "a") as f:
        f.write(event + "\n")

def send_email(event, volume):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "Gold market activity during scheduled event"

    body = f"""
A scheduled economic event occurred today.

Gold trading volume is significantly higher than its recent average.

Event: {event}
Observed Volume: {int(volume)}

This is an informational notice only and does not constitute financial advice.
"""
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def main():
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
                send_email(f"{event} ({asset_name})", volume)
                log_alert(alert_key)

    spike, volume = volume_spike()
    if not spike:
        return

    for event in events_today:
        if not already_alerted(event):
            send_email(event, volume)
            log_alert(event)

if __name__ == "__main__":
    try:
        print("SCRIPT STARTED")
        main()
        print("SCRIPT FINISHED SUCCESSFULLY")
    except Exception as e:
        print("ERROR OCCURRED:")
        print(e)
        raise





