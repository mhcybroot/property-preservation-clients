import json, re
from datetime import date

today = date.today().isoformat()
new_records = []

# Load seen emails (array format)
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json') as f:
    seen_list = json.load(f)
seen_emails = set(seen_list)

def is_junk_email(email):
    if not email or '@' not in email:
        return True
    d = email.lower().split('@')[1]
    bad = {'yelp.com','instagram.com','facebook.com','linkedin.com','twitter.com',
           'pinterest.com','bing.com','google.com','hotmail.com','gmail.com','yahoo.com',
           'outlook.com','aol.com','zillow.com','realtor.com','redfin.com','gov','mil'}
    if d in bad or any(d.endswith('.'+b) for b in bad):
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']):
        return True
    return False

# Records from browser extraction
records_to_add = [
    ('Bis-Man Outdoor Services', 'bismanoutdoorservices@gmail.com', '(701) 390-2157', '', 'Bismarck', 'Burleigh', 'ND', '', 'Landscaping Service', today),
]

for r in records_to_add:
    name, email, phone, address, city, county, state, zipcode, category, found_date = r
    if email and email in seen_emails:
        print(f'DUPLICATE skip: {email}')
        continue
    if email and is_junk_email(email):
        print(f'JUNK skip: {email}')
        continue
    if email:
        seen_emails.add(email)
    new_records.append(r)
    print(f'NEW: {name} | {email}')

print(f'Total new records: {len(new_records)}')

# Append to services.md
if new_records:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md', 'a') as f:
        for r in new_records:
            line = '| ' + ' | '.join(str(x) for x in r) + ' |'
            f.write(line + '\n')
    print('Appended to services.md')

# Save seen_emails (as array)
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'w') as f:
    json.dump(list(seen_emails), f, indent=2)

# Count total
with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md') as f:
    lines = [l for l in f if l.startswith('|') and '---' not in l]
print(f'Total records in services.md: {len(lines)}')