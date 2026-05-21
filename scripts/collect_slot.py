import smtplib, ssl, json, re
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BASE = '/home/mhcybroot/jobs/property-preservation-clients/data'

# Load current state
with open(f'{BASE}/search_state.json', 'r') as f:
    state = json.load(f)
state_idx = state['state_idx']
cat_idx = state['cat_idx']

STATES = [
    'Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware',
    'Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky',
    'Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi',
    'Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico',
    'New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania',
    'Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont',
    'Virginia','Washington','West Virginia','Wisconsin','Wyoming'
]
CITIES = [
    'Birmingham','Anchorage','Phoenix','Little Rock','Sacramento','Denver','Hartford','Wilmington',
    'Jacksonville','Atlanta','Honolulu','Boise','Springfield','Indianapolis','Des Moines','Topeka',
    'Louisville','Baton Rouge','Augusta','Baltimore','Boston','Lansing','St. Paul','Jackson',
    'Jefferson City','Helena','Lincoln','Las Vegas','Concord','Trenton','Santa Fe','Albany',
    'Raleigh','Bismarck','Columbus','Oklahoma City','Salem','Harrisburg','Providence','Columbia',
    'Pierre','Nashville','Austin','Salt Lake City','Montpelier','Richmond','Olympia','Charleston',
    'Madison','Cheyenne'
]
CATEGORIES = [
    'Plumber','HVAC Contractor','Electrician','Roofing Contractor','Handyman',
    'Landscaping Service','Painting Service','Cleaning Service','Snow Removal Service','Moving Service'
]

city = CITIES[state_idx]
state_name = STATES[state_idx]
category = CATEGORIES[cat_idx]

print(f'Slot: {city}, {state_name} / {category}')

# Records found (phone-only, no business email for Jacksonville FL Snow Removal)
# Yellowstone Landscape: 904.667.9635, 5329 Powers Ave, Jacksonville FL 32207, Duval County
# BrightView: 844.235.7778 (corporate, national)
# Plowz & Mowz: 800-489-8128, hello@plowz.com (aggregator, not local contractor)
# Imperial Snow Services: cn.services709@gmail.com (from Facebook but wrong city)

new_records = []

# BrightView - national franchise, phone only
new_records.append({
    'name': 'BrightView Landscape',
    'email': '',  # corporate, no local email
    'phone': '844.235.7778',
    'address': 'Jacksonville FL',  # no specific address from search
    'city': 'Jacksonville',
    'county': 'Duval',
    'state': 'FL',
    'zip': '',
    'category': 'Snow Removal Service'
})

today = date.today().isoformat()

# Check for duplicates
with open(f'{BASE}/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

added = 0
for rec in new_records:
    email = rec['email'].lower()
    if email and email not in seen_set:
        seen.append(email)
        seen_set.add(email)
        added += 1
    elif not email:
        # phone-only record - always add (no email to dedup)
        added += 1
    print(f"  + {rec['name']} | {rec['email'] or rec['phone']}")

# Append to services.md
with open(f'{BASE}/services.md', 'a') as f:
    f.write('\n')
    for rec in new_records:
        line = f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | {rec['category']} | {today} |"
        f.write(line + '\n')

# Save seen_emails
with open(f'{BASE}/seen_emails.json', 'w') as f:
    json.dump(seen, f)

# Advance state
state['state_idx'] = (state_idx + 1) % len(STATES)
state['cat_idx'] = (cat_idx + 1) % len(CATEGORIES)
with open(f'{BASE}/search_state.json', 'w') as f:
    json.dump(state, f)
print(f'Advanced to state_idx={state["state_idx"]} cat_idx={state["cat_idx"]}')

# Send email
if added > 0:
    body = f"New leads from Jacksonville, Florida (Snow Removal Service):\n\n"
    body += "| name | email | phone | address | city | county | state | zip | category | found_date |\n"
    body += "|------|-------|-------|---------|------|-------|------|-----|----------|\n"
    for rec in new_records:
        body += f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | {rec['category']} | {today} |\n"
    body += f"\nTotal new records: {added}"
    
    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = 'New Leads: Jacksonville, Florida'
    msg.attach(MIMEText(body, 'plain'))
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
            s.login('data@skylink-ltd.com', 'Skylink#2026')
            s.send_message(msg)
        print(f'Email sent: {added} records')
    except Exception as e:
        print(f'Email failed: {e}')
else:
    print('No new records to email')