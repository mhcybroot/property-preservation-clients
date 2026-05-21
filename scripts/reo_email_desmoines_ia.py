import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

today = date.today().isoformat()

body = f"""New REO Leads: Des Moines, Iowa

Date: {today}
Category: Cash Offer Home Buyer
City: Des Moines
State: Iowa

New Records:
| Name | Phone | Notes |
|------|-------|-------|
| We Buy Houses in Des Moines | 515-305-2803 | Cash home buyer, Des Moines IA |
| Sell Now Iowa | 515-531-2274 | Cash home buyer, 20+ years experience |
| Des Moines Home Buyers LLC | 515-344-4341 | BBB accredited, 20 years in business |
| Midwest Property Group | 515-778-7078 | Central Iowa cash buyer, Adam |

Total new records: 4

---
Skylink LTD REO Pipeline
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New REO Leads: Des Moines, Iowa'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
print('Email sent successfully')