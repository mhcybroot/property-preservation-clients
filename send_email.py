import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = "2026-05-21"
city = "Atlanta"
state = "Georgia"

body = """New Electrician leads found in Atlanta, GA.

| Name | Email | Phone | Address | City | County | State | Zip |
|------|-------|-------|---------|------|--------|-------|-----|
| Pat Murphy Electric | info@patmurphyelectric.com | 404-577-4191 | 3340 Peachtree Rd. NE Suite 1800-001 | Atlanta | Fulton | GA | 30326 |
| Bray Electrical Services | info@brayelectricalservices.com | (404) 378-1212 | 743 E College Ave | Decatur | DeKalb | GA | 30030 |
| Performance Electrical LLC | Info@PerformanceElectricalllc.com | (770) 746-7011 | 2195 Eastview Parkway Suite 103 | Conyers | Rockdale | GA | 30013 |
| Villa3 Electrical | villa3electrical@gmail.com | 770-873-0228 | | Atlanta | Fulton | GA | |

Total: 4 new records
Category: Electrician
Found: """ + today + """
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = f'New Leads: {city}, {state}'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)

print("Email sent")