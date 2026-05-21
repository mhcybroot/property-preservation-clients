import json, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE = '/home/mhcybroot/jobs/property-preservation-clients/data'

with open(f'{BASE}/seen_emails.json', 'r') as f:
    seen = json.load(f)

records = [
    {'name': 'Lawn ReLeaf', 'email': '', 'phone': '501-476-0540', 'address': '8100 Highway 107', 'city': 'Sherwood', 'county': 'Pulaski', 'state': 'AR', 'zip': '72120', 'category': 'Snow Removal Service'},
    {'name': 'AF&G LLC', 'email': 'info@arfence.com', 'phone': '(501) 771-9929', 'address': '6700 Allied Rd', 'city': 'Little Rock', 'county': 'Pulaski', 'state': 'AR', 'zip': '72209', 'category': 'Snow Removal Service'},
]

today = date.today().isoformat()
seen_set = set(seen)
added = 0

for rec in records:
    email = rec['email'].lower()
    if email and email not in seen_set:
        seen.append(email)
        seen_set.add(email)
        added += 1
        print(f"  + {rec['name']} | {rec['email']} | {rec['phone']}")
    elif not email:
        added += 1
        print(f"  + {rec['name']} | {rec['phone']} (phone-only)")

with open(f'{BASE}/services.md', 'a') as f:
    f.write('\n')
    for rec in records:
        line = f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | {rec['category']} | {today} |"
        f.write(line + '\n')

with open(f'{BASE}/seen_emails.json', 'w') as f:
    json.dump(seen, f)

print(f'Added {added} records')

if added > 0:
    body = 'New leads from Little Rock, Arkansas (Snow Removal Service):\n\n'
    body += '| name | email | phone | address | city | county | state | zip | category | found_date |\n'
    body += '|------|-------|-------|---------|------|-------|------|-----|----------|\n'
    for rec in records:
        body += f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | {rec['category']} | {today} |\n"
    body += f'\nTotal: {added}'
    
    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = 'New Leads: Little Rock, Arkansas'
    msg.attach(MIMEText(body, 'plain'))
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
            s.login('data@skylink-ltd.com', 'Skylink#2026')
            s.send_message(msg)
        print('Email sent')
    except Exception as e:
        print(f'Email failed: {e}')