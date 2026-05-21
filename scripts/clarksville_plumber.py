import json, re
from datetime import date

# New record
record = {
    'name': 'Mac Plumbing Heating & Air',
    'email': 'admin@macplumbing.com',
    'phone': '(931) 346-0675',
    'address': '2968B E. Old Ashland City Rd.',
    'city': 'Clarksville',
    'county': 'Montgomery',
    'state': 'Tennessee',
    'zip': '37043',
    'category': 'Plumber',
    'found_date': '2026-05-21'
}

# Append to services.md
with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md', 'r') as f:
    content = f.read()

# Ensure trailing newline
if not content.endswith('\n'):
    content += '\n'

new_row = "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n".format(
    record['name'], record['email'], record['phone'], record['address'],
    record['city'], record['county'], record['state'], record['zip'],
    record['category'], record['found_date']
)
content += new_row

with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md', 'w') as f:
    f.write(content)

print('Appended to services.md')

# Update seen_emails.json
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen.append(record['email'])
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'w') as f:
    json.dump(seen, f)

print('Updated seen_emails.json, total:', len(seen))
print('Record:', record['name'], '|', record['email'])