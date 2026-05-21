import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = '2026-05-22'
body = f"""REO Pipeline Report — Louisville, Kentucky | Home Inspector
Run: {today}

+ Elite Home Inspections LLC | elitehomeinspections@twc.com | 502-648-9294 | 3044 Bardstown Rd, Ste. 226, Louisville KY 40205
+ Home Inspections Services | dougs@hiswebsite.org | 502-817-1915 | 102 Daventry Lane, Ste. #8, Louisville KY 40223
+ Home Inspections Services | jeremyf@hiswebsite.org | 502-423-7575 | 102 Daventry Lane, Ste. #8, Louisville KY 40223
+ Home Inspections Services | jeans@hiswebsite.org | 502-500-9486 | 102 Daventry Lane, Ste. #8, Louisville KY 40223

Phone-only (no email extracted):
- Clarity Home Inspections | 502-251-4888
- ABI Home Inspection Services | 502-938-5190

---
Skylink LTD REO Pipeline | data@skylink-ltd.com"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New REO Leads: Louisville, Kentucky'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)

print("Email sent successfully")