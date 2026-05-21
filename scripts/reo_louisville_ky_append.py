import json

# Read current seen emails
try:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json') as f:
        seen = json.load(f)
except:
    seen = []

new_emails = ['elitehomeinspections@twc.com', 'dougs@hiswebsite.org', 'jeremyf@hiswebsite.org', 'jeans@hiswebsite.org']
seen.extend(new_emails)

with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json', 'w') as f:
    json.dump(seen, f)

print(f"Added {len(new_emails)} emails to seen_emails.json")

# Append to reo_services.md
today = '2026-05-22'
new_lines = [
    "| Elite Home Inspections LLC | elitehomeinspections@twc.com | 502-648-9294 | 3044 Bardstown Rd, Ste. 226 | Louisville | Jefferson | KY | 40205 | Home Inspector | 2026-05-22 |",
    "| Home Inspections Services | dougs@hiswebsite.org | 502-817-1915 | 102 Daventry Lane, Ste. #8 | Louisville | Jefferson | KY | 40223 | Home Inspector | 2026-05-22 |",
    "| Home Inspections Services | jeremyf@hiswebsite.org | 502-423-7575 | 102 Daventry Lane, Ste. #8 | Louisville | Jefferson | KY | 40223 | Home Inspector | 2026-05-22 |",
    "| Home Inspections Services | jeans@hiswebsite.org | 502-500-9486 | 102 Daventry Lane, Ste. #8 | Louisville | Jefferson | KY | 40223 | Home Inspector | 2026-05-22 |",
]

with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_services.md', 'a') as f:
    f.write('\n')
    for line in new_lines:
        f.write(line + '\n')

print("Appended 4 records to reo_services.md")