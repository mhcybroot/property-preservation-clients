import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

today = date.today().isoformat()

body = f"""New Leads: Anchorage, Alaska

Category: Snow Removal Service

| Name | Email | Phone | Address | City | County | State | Zip | Category | Found |
|------|-------|-------|---------|------|--------|-------|-----|----------|-------|
| Anchorage Downtown Partnership | info@anchoragedowntown.org | (907) 277-0141 | unknown | Anchorage | Anchorage | AK | | Snow Removal Service | {today} |
| Snow Business LLC | paul@snowbusinessllc.com | (907) 350-1100 | Anchorage, AK 99507 | Anchorage | Anchorage | AK | 99507 | Snow Removal Service | {today} |
| Alaska Land Works | info@alaskalandworks.com | (907) 350-1622 | P.O. Box 111613, Anchorage, AK 99511 | Anchorage | Anchorage | AK | 99511 | Snow Removal Service | {today} |

---
Skylink LTD Property Preservation Pipeline
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New Leads: Anchorage, Alaska'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
    print("Email sent successfully")