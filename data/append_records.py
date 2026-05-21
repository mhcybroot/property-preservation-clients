import json, re, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = date.today().isoformat()

# Records found
new_records = [
    {
        "name": "Tecta America Kentucky",
        "email": "Service.JBRoofing@tectaamerica.com",
        "phone": "(800) 472-0969",
        "address": "4045 McCollum Court",
        "city": "Louisville",
        "county": "Jefferson",
        "state": "KY",
        "zip": "",
        "category": "Roofing Contractor"
    },
    {
        "name": "Highland Roofing",
        "email": "",
        "phone": "502-968-2009",
        "address": "4007 Produce Rd",
        "city": "Louisville",
        "county": "Jefferson",
        "state": "KY",
        "zip": "40218",
        "category": "Roofing Contractor"
    },
    {
        "name": "Pure Roofing Company",
        "email": "info@pureroofingky.com",
        "phone": "(502) 547-7375",
        "address": "11909 Plantside Drive",
        "city": "Louisville",
        "county": "Jefferson",
        "state": "KY",
        "zip": "40299",
        "category": "Roofing Contractor"
    },
    {
        "name": "Simply Clean BR",
        "email": "br.simplyclean@gmail.com",
        "phone": "(225) 276-8494",
        "address": "",
        "city": "Baton Rouge",
        "county": "East Baton Rouge",
        "state": "LA",
        "zip": "",
        "category": "Cleaning Service"
    },
    {
        "name": "Priority Cleaning LLC",
        "email": "",
        "phone": "(225) 320-4377",
        "address": "",
        "city": "Baton Rouge",
        "county": "East Baton Rouge",
        "state": "LA",
        "zip": "",
        "category": "Cleaning Service"
    },
    {
        "name": "Robillards",
        "email": "info@robillardsmanagement.org",
        "phone": "(225) 439-4840",
        "address": "1651 Lobdell Avenue, Suite 201",
        "city": "Baton Rouge",
        "county": "East Baton Rouge",
        "state": "LA",
        "zip": "70806",
        "category": "Cleaning Service"
    },
]

# Dedupe against seen_emails.json
seen_file = '/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json'
with open(seen_file, 'r') as f:
    seen_list = json.load(f)
seen_set = set(seen_list)

# Check for Baton Rouge cleaning - need to verify city is actually Baton Rouge
# Simply Clean BR - Facebook post explicitly says Baton Rouge service
# Robillards - address is Baton Rouge

added = []
for r in new_records:
    key = r['email'] if r['email'] else r['phone']
    if key and key not in seen_set:
        seen_set.add(key)
        seen_list.append(key)
        added.append(r)
        print(f"ADDED: {r['name']} | {r['email']} | {r['phone']} | {r['city']}, {r['state']} | {r['category']}")
    else:
        print(f"SKIP (dup): {r['name']} | {key}")

# Append to services.md
if added:
    services_md = '/home/mhcybroot/jobs/property-preservation-clients/data/services.md'
    with open(services_md, 'a') as f:
        last_char = None
        with open(services_md, 'r') as fr:
            fr.seek(0, 2)
            fr.seek(fr.tell() - 1)
            last_char = fr.read(1)
        if last_char and last_char != '\n':
            f.write('\n')
        for r in added:
            line = f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {today} |\n"
            f.write(line)

    # Update seen_emails.json
    with open(seen_file, 'w') as f:
        json.dump(seen_list, f)

    # Send email
    city_state = f"{added[0]['city']}, {added[0]['state']}"
    body = f"New leads found:\n\n"
    for r in added:
        body += f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {today} |\n"

    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = f'New Leads: {city_state}'
    msg.attach(MIMEText(body, 'plain'))

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
            s.login('data@skylink-ltd.com', 'Skylink#2026')
            s.send_message(msg)
        email_sent = True
        print(f"EMAIL SENT to data@skylink-ltd.com")
    except Exception as e:
        email_sent = False
        print(f"EMAIL FAILED: {e}")
else:
    print("No new records to add")
    email_sent = False

print(f"\nSUMMARY: new={len(added)}, email_sent={email_sent}")