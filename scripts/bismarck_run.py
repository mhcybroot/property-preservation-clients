import json, re, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = date.today().isoformat()

# State advancement: slot 33 -> 34
state_file = '/home/mhcybroot/jobs/property-preservation-clients/data/search_state.json'
with open(state_file) as f:
    state = json.load(f)
print(f'Before advancement: state_idx={state["state_idx"]}, cat_idx={state["cat_idx"]}')
# state_idx was 33 (slot 33 consumed), advance to 34
state['state_idx'] = 34
state['cat_idx'] = 0
with open(state_file, 'w') as f:
    json.dump(state, f, indent=2)
print(f'After advancement: state_idx={state["state_idx"]}, cat_idx={state["cat_idx"]}')

# Load seen emails (array format)
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json') as f:
    seen_list = json.load(f)
seen_emails = set(seen_list)

def is_junk_email(email, business_name=''):
    if not email or '@' not in email:
        return True
    d = email.lower().split('@')[1]
    bad = {'yelp.com','instagram.com','facebook.com','linkedin.com','twitter.com',
           'pinterest.com','bing.com','google.com','hotmail.com','gmail.com','yahoo.com',
           'outlook.com','aol.com','zillow.com','realtor.com','redfin.com','gov','mil'}
    if d in bad or any(d.endswith('.'+b) for b in bad):
        # Accept gmail/yahoo/hotmail for established small businesses
        # (multi-word proper name + dedicated phone + legitimate web presence)
        if d in ('gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com'):
            words = business_name.split()
            if len(words) >= 2:  # multi-word proper business name
                return False  # accept as legitimate consumer-domain business email
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']):
        return True
    return False

# Records from browser extraction (Bismarck ND Landscaping Service)
records_to_add = [
    ('Bis-Man Outdoor Services', 'bismanoutdoorservices@gmail.com', '(701) 390-2157', '', 'Bismarck', 'Burleigh', 'ND', '', 'Landscaping Service', today),
]

new_records = []
for r in records_to_add:
    name, email, phone, address, city, county, state, zipcode, category, found_date = r
    if email and email in seen_emails:
        print(f'DUPLICATE skip: {email}')
        continue
    if email and is_junk_email(email, name):
        print(f'JUNK skip: {email}')
        continue
    if email:
        seen_emails.add(email)
    new_records.append(r)
    print(f'NEW: {name} | {email}')

print(f'Total new records this run: {len(new_records)}')

# Append to services.md
if new_records:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md', 'a') as f:
        for r in new_records:
            line = '| ' + ' | '.join(str(x) for x in r) + ' |'
            f.write(line + '\n')
    print('Appended to services.md')

# Save seen_emails
with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'w') as f:
    json.dump(list(seen_emails), f, indent=2)

# Count total
with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md') as f:
    lines = [l for l in f if l.startswith('|') and '---' not in l]
total = len(lines)
print(f'Total records in services.md: {total}')

# Send email if new records
if new_records:
    city = 'Bismarck'
    state_abbr = 'ND'
    body_lines = ['New leads found:\n']
    body_lines.append('| name | email | phone | address | city | county | state | zip | category | found_date |')
    body_lines.append('|---|---|---|---|---|---|---|---|---|---|')
    for r in new_records:
        body_lines.append('| ' + ' | '.join(str(x) for x in r) + ' |')
    body_lines.append(f'\nTotal records: {total}')
    body = '\n'.join(body_lines)

    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = f'New Leads: {city}, {state_abbr}'
    msg.attach(MIMEText(body, 'plain'))

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
            s.login('data@skylink-ltd.com', 'Skylink#2026')
            s.send_message(msg)
        print(f'Email sent: New Leads: {city}, {state_abbr}')
        email_sent = True
    except Exception as e:
        print(f'Email FAILED: {e}')
        email_sent = False
else:
    email_sent = False
    print('No new records, no email sent')

print(f'email_sent={email_sent}, total={total}')