import json
from datetime import date

today = date.today().isoformat()

# New records from Anchorage AK Snow Removal Service
records = [
    {"name": "Anchorage Downtown Partnership", "email": "info@anchoragedowntown.org", "phone": "(907) 277-0141", "address": "unknown", "city": "Anchorage", "county": "Anchorage", "state": "AK", "zip": "", "category": "Snow Removal Service"},
    {"name": "Snow Business LLC", "email": "paul@snowbusinessllc.com", "phone": "(907) 350-1100", "address": "Anchorage, AK 99507", "city": "Anchorage", "county": "Anchorage", "state": "AK", "zip": "99507", "category": "Snow Removal Service"},
    {"name": "Alaska Land Works", "email": "info@alaskalandworks.com", "phone": "(907) 350-1622", "address": "P.O. Box 111613, Anchorage, AK 99511", "city": "Anchorage", "county": "Anchorage", "state": "AK", "zip": "99511", "category": "Snow Removal Service"},
]

# Load seen emails
with open('data/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

# Read current services.md to get last line info
with open('data/services.md', 'r') as f:
    content = f.read()

# Ensure newline before append
if content and not content.endswith('\n'):
    content += '\n'

new_count = 0
for rec in records:
    if rec['email'] in seen_set:
        print(f"SKIP (already seen): {rec['email']}")
        continue
    
    line = f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | {rec['category']} | {today} |"
    content += line + '\n'
    seen.append(rec['email'])
    seen_set.add(rec['email'])
    new_count += 1
    print(f"ADD: {rec['name']} | {rec['email']}")

# Write back
with open('data/services.md', 'w') as f:
    f.write(content)

with open('data/seen_emails.json', 'w') as f:
    json.dump(list(seen_set), f)

print(f"\nTotal new records: {new_count}")