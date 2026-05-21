import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

new_records = """| Paint Denver | service@paintdenver.com | 303-710-8555 | 1616 Federal Blvd | Denver | Denver | CO | 80211 | Painting Service | 2026-05-21 |
| The Colorado Painting Company | info@thecoloradopaintingcompany.com | 866-583-1933 | Wheat Ridge, CO | Wheat Ridge | Jefferson | CO | 80033 | Painting Service | 2026-05-21 |
| Performance Painting | | 702-202-2000 | 3705 Kipling St Suite 206 | Wheat Ridge | Jefferson | CO | 80033 | Painting Service | 2026-05-21 |
| American Painting Specialists | zane@americanpaintingspecialists.com | 720-343-4351 | 2476 W 29th Ave | Denver | Denver | CO | 80211 | Painting Service | 2026-05-21 |
| Shaker Painting | | (303) 981-0061 | Denver, CO | Denver | Denver | CO | | Painting Service | 2026-05-21 |"""

body = f"""New Painting Service leads from Denver, Colorado:

| name | email | phone | address | city | county | state | zip | category | found_date |
|------|-------|-------|---------|------|-------|------|-----|----------|------------|
{new_records}

---
Skylink LTD Property Preservation Pipeline
City: Denver, CO
Category: Painting Service
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New Leads: Denver, Colorado'

msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
print("Email sent successfully")