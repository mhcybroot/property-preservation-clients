#!/usr/bin/env python3
import json
import smtplib
import ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE = '/home/mhcybroot/jobs/property-preservation-clients'
DATA = f'{BASE}/data'

# Current state (MISMATCHED - pre-run ran Montana/Billings, we ran Georgia)
# Pre-run consumed Montana/Billings Electrician (state_idx=27). We ran Georgia/Electrician.
# We need to advance from state_idx=9, cat_idx=5 to state_idx=10, cat_idx=6

# Load current state
with open(f'{DATA}/search_state.json') as f:
    state = json.load(f)
print(f"Before: state_idx={state['state_idx']}, cat_idx={state['cat_idx']}")

# Advance: Georgia (9) + Landscaping (5) -> Hawaii (10) + Painting Service (6)
state['state_idx'] = (state['state_idx'] + 1) % 50
state['cat_idx'] = (state['cat_idx'] + 1) % 10
print(f"After:  state_idx={state['state_idx']}, cat_idx={state['cat_idx']}")

with open(f'{DATA}/search_state.json', 'w') as f:
    json.dump(state, f)

# Load seen_emails
with open(f'{DATA}/seen_emails.json') as f:
    seen = json.load(f)
seen_set = set(seen)

# New records found
new_records = [
    {'name': 'The Painting Group', 'email': 'contact@thepaintinggroup.com', 'phone': '770-818-9885', 'address': '3350 Riverwood Parkway SE Suite 1900 #5107', 'city': 'Atlanta', 'county': 'Fulton', 'state': 'GA', 'zip': '30339', 'category': 'Painting Service'},
    {'name': 'Prodigy Electrician', 'email': 'proelectric2025@gmail.com', 'phone': '404-671-9488', 'address': '', 'city': 'Atlanta', 'county': 'Fulton', 'state': 'GA', 'zip': '', 'category': 'Electrician'},
    {'name': 'Elohim Electrical Services', 'email': 'eloimelectricalst@gmail.com', 'phone': '404-784-2674', 'address': '', 'city': 'Atlanta', 'county': 'Fulton', 'state': 'GA', 'zip': '', 'category': 'Electrician'},
]

today = date.today().isoformat()

# Read existing services.md to check for double-pipe corruption
with open(f'{DATA}/services.md', 'r') as f:
    lines = f.readlines()

# Ensure last line ends with newline
if lines and not lines[-1].endswith('\n'):
    lines[-1] += '\n'

# Check if last line has content (not a separator)
last_line = lines[-1].strip() if lines else ''
has_trailing_sep = last_line.startswith('|') and '---' in last_line

# Append newline if last line was a separator
if has_trailing_sep or not last_line:
    if lines and not lines[-1].endswith('\n'):
        pass
    else:
        pass

# Build markdown rows
rows = []
for r in new_records:
    row = f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {today} |"
    rows.append(row)

# Ensure blank line before new rows if last line was a separator
if lines and not lines[-1].endswith('\n'):
    lines[-1] += '\n'
if lines and '|---' in lines[-1]:
    lines.append('\n')

with open(f'{DATA}/services.md', 'a') as f:
    f.writelines(lines)
    if lines and lines[-1].strip() and not lines[-1].endswith('\n'):
        f.write('\n')
    for row in rows:
        f.write(row + '\n')

# Update seen_emails
new_emails = [r['email'] for r in new_records if r['email']]
for e in new_emails:
    if e not in seen_set:
        seen.append(e)
        seen_set.add(e)

with open(f'{DATA}/seen_emails.json', 'w') as f:
    json.dump(seen, f)

print(f"Appended {len(new_records)} records to services.md")
print(f"Updated seen_emails.json with {len(new_emails)} new emails")

# Build email body
category = 'Electrician'
city = 'Atlanta'
state_name = 'Georgia'
email_subject = f'New Leads: {city}, {state_name}'

table_header = '| name | email | phone | address | city | county | state | zip | category | found_date |'
table_sep    = '|------|-------|-------|---------|------|-------|------|-----|----------|'
email_body_lines = [f'New leads found for {category} in {city}, {state_name}:', '', table_header, table_sep]
for r in new_records:
    email_body_lines.append(f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {today} |")

email_body = '\n'.join(email_body_lines)

# Send email
msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = email_subject
msg.attach(MIMEText(email_body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
        s.login('data@skylink-ltd.com', 'Skylink#2026')
        s.send_message(msg)
    print(f"Email sent: {email_subject}")
    email_sent = True
except Exception as e:
    print(f"Email failed: {e}")
    email_sent = False

print(f"[SEARCH] Electrician | Atlanta, Georgia")
for r in new_records:
    print(f"  + {r['name']} | {r['email']}")
print(f"[DONE] new={len(new_records)} validated=0")
print(f"Email sent: {email_sent}")