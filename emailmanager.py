import os
import smtplib

SUBJECT = "Subject:Blog Contact"
SMTP_SERVER = os.getenv("SMTP_SERVER")
USER = os.getenv("EMAIL_APP_USER")
PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")


def send_email(form):
    name = form['name']
    email_local = form['email']
    phone = form['phone']
    message = form['message']

    body = f"Name: {name}\n" \
           f"Email: {email_local}\n" \
           f"Phone: {phone}\n" \
           f"Message:\n {message}"

    with smtplib.SMTP(SMTP_SERVER) as connection:
        connection.starttls()
        connection.login(
            user=USER,
            password=PASSWORD
        )
        connection.sendmail(
            from_addr=email_local,
            to_addrs=RECIPIENT_EMAIL,
            msg=f"{SUBJECT}\n\n{body}".encode("utf-8")
            )
