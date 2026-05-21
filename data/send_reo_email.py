import smtplib, ssl, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

body = """New REO Leads: Boston, Massachusetts (Property Manager)

| name | email | phone | address | city | county | state | zip |
| Green Ocean Property Management | hello@greenoceanpm.com | (617) 487-4868 | 268 Centre Street | Newton | Middlesex | MA | 02458 |
| Trinity Management LLC | info@trinitymanagementllc.net | 617-542-3019 | One Beacon Street, Suite 22100 | Boston | Suffolk | MA | 02108 |
| Premier Property Solutions | info@premierpropertyma.com | 1-857-PREMIER | 190 High Street, Floor #6 | Boston | Suffolk | MA | 02110 |
| EDGE Realty Advisors | info@edgerealtyboston.com | (617) 477-0601 | 1660 Soldiers Field Road | Boston | Suffolk | MA | 02135 |

Total: 4 new records
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New REO Leads: Boston, Massachusetts'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
print('Email sent')