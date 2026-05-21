import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = '2026-05-21'
body = f"""| name | email | phone | address | city | county | state | zip | category | found_date |
|------|-------|-------|---------|------|-------|------|-----|----------|-----------|
| Contact Us | sold@midwayauction.com | 317-996-2402 |  | Indianapolis | Marion | IN |  | Auction Services | {today} |
| Campbell Auction Team | campbellauction@aol.com | 765-914-0397 |  | Indianapolis | Marion | IN |  | Auction Services | {today} |
| Contact Us | media@auction.com |  |  | Indianapolis | Marion | IN |  | Auction Services | {today} |
| Contact | director@indianaauctioneers.org | 317-859-8990 |  | Indianapolis | Marion | IN |  | Auction Services | {today} |"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New REO Leads: Indianapolis, Indiana'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
print('Email sent successfully')