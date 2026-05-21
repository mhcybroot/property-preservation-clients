#!/usr/bin/env python3
import json, re, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = date.today().isoformat()

# Records collected for Baton Rouge LA Roofing Contractor
records = [
    {
        "name": "Golden Roofing & Construction LLC",
        "email": "info@goldenroofingandconstructionllc.com",
        "phone": "(225) 888-7766",
        "address": "Denham Springs, LA",
        "city": "Denham Springs",
        "county": "Livingston",
        "state": "LA",
        "zip": "70726",
        "category": "Roofing Contractor",
        "found_date": today
    },
    {
        "name": "Apex Construction & Roofing",
        "email": "sales@apexroofsla.com",
        "phone": "(225) 788-8518",
        "address": "Baton Rouge, LA 70809",
        "city": "Baton Rouge",
        "county": "East Baton Rouge",
        "state": "LA",
        "zip": "70809",
        "category": "Roofing Contractor",
        "found_date": today
    },
    {
        "name": "Cribbs Inc",
        "email": "cribbsinc@eatel.net",
        "phone": "(225) 344-0422",
        "address": "523 Live Oak Blvd, Baton Rouge, LA 70806",
        "city": "Baton Rouge",
        "county": "East Baton Rouge",
        "state": "LA",
        "zip": "70806",
        "category": "Roofing Contractor",
        "found_date": today
    },
    {
        "name": "Stalwart General Contractor",
        "email": "contact@stalwartgeneralcontractor.com",
        "phone": "(225) 283-1649",
        "address": "3346 Drusilla Lane Suite F, Baton Rouge, LA 70809",
        "city": "Baton Rouge",
        "county": "East Baton Rouge",
        "state": "LA",
        "zip": "70809",
        "category": "Roofing Contractor",
        "found_date": today
    },
    {
        "name": "Cypress Roofing",
        "email": "info@cypressroofingla.com",
        "phone": "(225) 238-6147",
        "address": "Gonzales, LA",
        "city": "Gonzales",
        "county": "Ascension",
        "state": "LA",
        "zip": "",
        "category": "Roofing Contractor",
        "found_date": today
    },
]

# Deduplicate against seen_emails.json
seen_path = '/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json'
with open(seen_path, 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

new_records = []
for r in records:
    email = r['email'].lower()
    if email not in seen_set and email:
        seen_set.add(email)
        seen.append(email)
        new_records.append(r)

if not new_records:
    print("[DONE] new=0 — no new records")
    exit(0)

# Append to services.md
services_path = '/home/mhcybroot/jobs/property-preservation-clients/data/services.md'
with open(services_path, 'r') as f:
    content = f.read()
last_char = content[-1] if content else ''
# Ensure trailing newline
if last_char not in ('', '\n'):
    with open(services_path, 'a') as f:
        f.write('\n')

with open(services_path, 'a') as f:
    for r in new_records:
        line = f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |"
        f.write(line + '\n')

# Save seen_emails
with open(seen_path, 'w') as f:
    json.dump(seen, f, indent=2)

print(f"[DONE] new={len(new_records)}")
for r in new_records:
    print(f"  + {r['name']} | {r['email']}")

# Build email body
body = f"New Roofing Contractor leads for Baton Rouge, Louisiana:\n\n"
body += "| name | email | phone | address |\n"
body += "|------|-------|-------|---------|\n"
for r in new_records:
    body += f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} |\n"

# Send email
msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New Leads: Baton Rouge, Louisiana'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
try:
    with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
        s.login('data@skylink-ltd.com', 'Skylink#2026')
        s.send_message(msg)
    print("Email sent to data@skylink-ltd.com")
except Exception as e:
    print(f"Email error: {e}")