import random
import smtplib

from email.mime.text import MIMEText


EMAIL="yourgmail@gmail.com"

PASSWORD="YourAppPassword"


def generate_otp():

    return str(random.randint(100000,999999))


def send_email(receiver,otp):

    msg=MIMEText(
        f"Your OTP is {otp}"
    )

    msg["Subject"]="Blood Need OTP"

    msg["From"]=EMAIL

    msg["To"]=receiver

    server=smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        EMAIL,
        PASSWORD
    )

    server.sendmail(
        EMAIL,
        receiver,
        msg.as_string()
    )

    server.quit()