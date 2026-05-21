import json, re, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DATA_DIR = '/home/mhcybroot/jobs/property-preservation-clients/data'
today = date.today().isoformat()

# Load seen emails
with open(f'{DATA_DIR}/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

records = []

# Record 1: Clean Impact Commercial Office Cleaning
email1 = 'info@cleanimpactllc.com'
if email1 not in seen_set:
    records.append({
        'name': 'Clean Impact Commercial Office Cleaning',
        'email': email1,
        'phone': '217-670-2004',
        'address': '2241 Groth St',
        'city': 'Springfield',
        'county': 'Sangamon',
        'state': 'Illinois',
        'zip': '62703',
        'category': 'Cleaning Service',
        'found_date': today
    })
    seen.append(email1)
    seen_set.add(email1)

# Record 2: Cardinal Cleaning (gmail but multi-word proper business name with phone confirmed on own website)
email2 = 'cardinalcleaningonline@gmail.com'
if email2 not in seen_set:
    records.append({
        'name': 'Cardinal Cleaning, Inc.',
        'email': email2,
        'phone': '217-679-6567',
        'address': '3550 Mayflower Dr Suite C',
        'city': 'Springfield',
        'county': 'Sangamon',
        'state': 'Illinois',
        'zip': '62711',
        'category': 'Cleaning Service',
        'found_date': today
    })
    seen.append(email2)
    seen_set.add(email2)

# Save seen_emails.json
with open(f'{DATA_DIR}/seen_emails.json', 'w') as f:
    json.dump(seen, f, indent=2)

# Append to services.md
if records:
    with open(f'{DATA_DIR}/services.md', 'a') as f:
        f.write('\n')
        for r in records:
            f.write(f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |\n")

    # Build email table
    table = "| name | email | phone | address | city | county | state | zip | category | found_date |\n"
    table += "|---|---|---|---|---|---|---|---|---|---|\n"
    for r in records:
        table += f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |\n"

    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = f'New Leads: Springfield, Illinois'
    msg.attach(MIMEText(table, 'plain'))

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
        s.login('data@skylink-ltd.com', 'Skylink#2026')
        s.send_message(msg)

    print(f"Added {len(records)} records and sent email")
else:
    print("No new records")