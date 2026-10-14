import smtplib
from email.message import EmailMessage
import config


def send_mail(to, subject, body):
    # SMTP set nahi hai to chupchap skip
    if not config.SMTP_HOST:
        return False
    try:
        msg = EmailMessage()
        msg["From"] = config.SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as s:
            s.starttls()
            s.login(config.SMTP_USER, config.SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print("mail nahi gaya:", e)
        return False
