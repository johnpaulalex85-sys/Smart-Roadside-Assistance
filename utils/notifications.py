import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Notifications")

def send_email_notification(to_email, subject, body):
    """Simulate sending an email."""
    msg = f"\n=== EMAIL SIMULATION ===\nTo: {to_email}\nSubject: {subject}\nBody:\n{body}\n========================\n"
    logger.info(f"[EMAIL MOCK] {to_email} : {subject}")
    print(msg)
    return True

def send_sms_alert(to_phone, message):
    """Simulate sending an SMS alert."""
    msg = f"\n=== SMS SIMULATION ===\nTo: {to_phone}\nMessage: {message}\n======================\n"
    logger.info(f"[SMS MOCK] {to_phone} : {message}")
    print(msg)
    return True
