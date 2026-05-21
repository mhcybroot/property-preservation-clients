import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

body = """New REO Leads: Wilmington, Delaware

+ Quality Home Inspections | Ted@InspectDelaware.com | (302) 883-8797 | 45 Browning Cir, Middletown, DE 19709
+ First State Inspection Agency | Inspections@FirstStateInspection.com | 1-800-468-7338 | Wilmington, DE
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New REO Leads: Wilmington, Delaware'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
print("Email sent")