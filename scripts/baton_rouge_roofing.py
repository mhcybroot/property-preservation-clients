import smtplib, ssl, json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load seen emails
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

# New records found
new_records = [
    {"name": "Apex Construction & Roofing", "email": "sales@apexroofsla.com", "phone": "(225) 788-8518", "address": "Baton Rouge, LA 70809", "city": "Baton Rouge", "county": "East Baton Rouge", "state": "LA", "zip": "70809"},
    {"name": "Cribbs Inc", "email": "cribbsinc@eatel.net", "phone": "(225) 344-0422", "address": "523 Live Oak Blvd, Baton Rouge, LA 70806", "city": "Baton Rouge", "county": "East Baton Rouge", "state": "LA", "zip": "70806"},
    {"name": "Stalwart General Contractor", "email": "contact@stalwartgeneralcontractor.com", "phone": "(225) 283-1649", "address": "3346 Drusilla Lane Suite F, Baton Rouge, LA 70809", "city": "Baton Rouge", "county": "East Baton Rouge", "state": "LA", "zip": "70809"},
    {"name": "Cypress Roofing", "email": "info@cypressroofingla.com", "phone": "(225) 238-6147", "address": "Gonzales, LA", "city": "Gonzales", "county": "Ascension", "state": "LA", "zip": ""},
]

# Check for new emails
emails_to_add = []
for rec in new_records:
    if rec['email'] and rec['email'] not in seen_set:
        emails_to_add.append(rec['email'])
        seen.append(rec['email'])

if emails_to_add:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'w') as f:
        json.dump(seen, f)

# Append to services.md
today = "2026-05-21"
with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md', 'a') as f:
    for rec in new_records:
        line = f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | Roofing Contractor | {today} |"
        f.write(line + '\n')

# Build email table
table = "| name | email | phone | address | city | county | state | zip | category | found_date |\n|------|-------|-------|---------|------|-------|------|-----|----------|\n"
for rec in new_records:
    table += f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | Roofing Contractor | {today} |\n"

body = f"""New property preservation leads found:

{table}
Total: {len(new_records)} new records
State: Louisiana/Baton Rouge
Category: Roofing Contractor

---
Skylink LTD Property Preservation Pipeline
data@skylink-ltd.com
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New Leads: Baton Rouge, Louisiana'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
    print("Email sent")