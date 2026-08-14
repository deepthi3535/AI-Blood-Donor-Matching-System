import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_secure_otp():
    """
    Generate a cryptographically secure 6-digit OTP
    """
    return str(secrets.SystemRandom().randint(100000, 999999))

def send_otp_email(receiver, otp):
    """
    Send a professionally designed HTML and plain-text OTP verification email.
    Supports a dev-only logging mode when SMTP is not configured or
    EMAIL_VERIFICATION_DEV_MODE is enabled.
    """
    print(f"\n[OTP LOG] Generated code for {receiver}: {otp}\n", flush=True)
    dev_mode = os.getenv("EMAIL_VERIFICATION_DEV_MODE", "false").lower() == "true"
    
    mail_server = os.getenv("MAIL_SERVER")
    mail_port = os.getenv("MAIL_PORT")
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_use_tls = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    mail_default_sender = os.getenv("MAIL_DEFAULT_SENDER", mail_username)

    if dev_mode or not mail_server or not mail_username or not mail_password:
        # Development mode or SMTP not configured
        print(f"\n[DEV ONLY] OTP generated for {receiver}: {otp}\n", flush=True)
        return True
        
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg["Subject"] = "BloodNeed Email Verification OTP"
        msg["From"] = mail_default_sender
        msg["To"] = receiver

        # Plain-text version
        text_content = f"""Hello,

Thank you for registering with BloodNeed. To complete your email verification and activate your account, please use the following One-Time Password (OTP):

OTP Code: {otp}

This OTP is valid for 5 minutes.

Security Reminder: Never share this OTP code with anyone, including BloodNeed staff.

Best regards,
The BloodNeed Team
"""

        # HTML version with custom styles matching the BloodNeed branding
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f7f9fc; margin: 0; padding: 0; color: #333; }}
        .container {{ max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e1e8ed; }}
        .header {{ background-color: #d9534f; padding: 30px; text-align: center; color: white; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px; }}
        .content {{ padding: 40px 30px; line-height: 1.6; }}
        .greeting {{ font-size: 18px; font-weight: 600; margin-bottom: 20px; color: #111; }}
        .otp-box {{ background: #fdf2f2; border: 1px dashed #d9534f; border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0; }}
        .otp-code {{ font-size: 36px; font-weight: 700; color: #d9534f; letter-spacing: 6px; margin: 0; }}
        .expiry {{ font-size: 14px; color: #666; margin-top: 10px; }}
        .warning {{ font-size: 13px; color: #8a6d3b; background-color: #fcf8e3; border: 1px solid #faebcc; padding: 12px; border-radius: 6px; margin-top: 25px; }}
        .footer {{ background-color: #f7f9fc; padding: 20px; text-align: center; font-size: 12px; color: #999; border-top: 1px solid #e1e8ed; }}
        .footer a {{ color: #d9534f; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🩸 BloodNeed</h1>
        </div>
        <div class="content">
            <div class="greeting">Hello,</div>
            <p>Thank you for registering with <strong>BloodNeed</strong>. To complete your email verification and activate your account, please use the following One-Time Password (OTP):</p>
            
            <div class="otp-box">
                <div class="otp-code">{otp}</div>
                <div class="expiry">This OTP is valid for <strong>5 minutes</strong>.</div>
            </div>
            
            <p>If you did not request this code, please ignore this email.</p>
            
            <div class="warning">
                <strong>Security Reminder:</strong> Never share this OTP code with anyone, including BloodNeed staff.
            </div>
            
            <p style="margin-top: 30px;">Best regards,<br><strong>The BloodNeed Team</strong></p>
        </div>
        <div class="footer">
            &copy; 2026 BloodNeed Emergency Response System. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

        # Attach content parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Connect and send
        port = int(mail_port) if mail_port else 587
        server = smtplib.SMTP(mail_server, port)
        if mail_use_tls:
            server.starttls()
        server.login(mail_username, mail_password)
        server.sendmail(mail_default_sender, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        # Avoid printing/logging the actual OTP here
        print(f"Error sending email: {e}", flush=True)
        return False