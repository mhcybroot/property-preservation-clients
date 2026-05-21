import json, re, smtplib, ssl
from datetime import date

today = date.today().isoformat()

records = [
    {
        "name": "Quality Home Inspections",
        "email": "Ted@InspectDelaware.com",
        "phone": "(302) 883-8797",
        "address": "45 Browning Cir",
        "city": "Middletown",
        "county": "New Castle",
        "state": "DE",
        "zip": "19709",
        "category": "Home Inspector",
        "found_date": today,
    },
    {
        "name": "First State Inspection Agency",
        "email": "Inspections@FirstStateInspection.com",
        "phone": "1-800-468-7338",
        "address": "",
        "city": "Wilmington",
        "county": "New Castle",
        "state": "DE",
        "zip": "",
        "category": "Home Inspector",
        "found_date": today,
    },
]

with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

new_records = []
for r in records:
    email = r['email'].lower()
    if email and email not in seen_set:
        seen_set.add(email)
        seen.append(email)
        new_records.append(r)
        print("NEW: " + r['name'] + " | " + r['email'])
    elif not email:
        phone_clean = re.sub(r'\D','',r['phone'])
        phone_key = "phone_" + phone_clean + "@unknown.local"
        if phone_key not in seen_set:
            seen_set.add(phone_key)
            seen.append(phone_key)
            new_records.append(r)
            print("NEW (phone): " + r['name'] + " | " + r['phone'])
    else:
        print("SKIP (dup): " + r['name'] + " | " + r['email'])

with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json', 'w') as f:
    json.dump(seen, f, indent=2)

if new_records:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_services.md', 'a') as f:
        f.write('\n')
        for r in new_records:
            line = "| " + r['name'] + " | " + r['email'] + " | " + r['phone'] + " | " + r['address'] + " | " + r['city'] + " | " + r['county'] + " | " + r['state'] + " | " + r['zip'] + " | " + r['category'] + " | " + r['found_date'] + " |"
            f.write(line + '\n')

print("\nTotal new records: " + str(len(new_records)))