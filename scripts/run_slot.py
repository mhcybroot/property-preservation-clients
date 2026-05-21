import json, subprocess, re, smtplib, ssl
from datetime import date

STATES = ["Alabama/Birmingham", "Alaska/Anchorage", "Arizona/Phoenix", "Arkansas/Little Rock", "California/Sacramento", "Colorado/Denver", "Connecticut/Hartford", "Delaware/Wilmington", "Florida/Jacksonville", "Georgia/Atlanta", "Hawaii/Honolulu", "Idaho/Boise", "Illinois/Springfield", "Indiana/Indianapolis", "Iowa/Des Moines", "Kansas/Topeka", "Kentucky/Louisville", "Louisiana/Baton Rouge", "Maine/Augusta", "Maryland/Baltimore", "Massachusetts/Boston", "Michigan/Lansing", "Minnesota/St. Paul", "Mississippi/Jackson", "Missouri/Jefferson City", "Montana/Helena", "Nebraska/Lincoln", "Nevada/Las Vegas", "New Hampshire/Concord", "New Jersey/Trenton", "New Mexico/Santa Fe", "New York/Albany", "North Carolina/Raleigh", "North Dakota/Bismarck", "Ohio/Columbus", "Oklahoma/Oklahoma City", "Oregon/Salem", "Pennsylvania/Harrisburg", "Rhode Island/Providence", "South Carolina/Columbia", "South Dakota/Pierre", "Tennessee/Nashville", "Texas/Austin", "Utah/Salt Lake City", "Vermont/Montpelier", "Virginia/Richmond", "Washington/Olympia", "West Virginia/Charleston", "Wisconsin/Madison", "Wyoming/Cheyenne"]
CATEGORIES = ["Plumber", "HVAC Contractor", "Electrician", "Roofing Contractor", "Handyman", "Landscaping Service", "Painting Service", "Cleaning Service", "Snow Removal Service", "Moving Service"]

BASE = '/home/mhcybroot/jobs/property-preservation-clients/data'
today = date.today().isoformat()

# Read current state
with open(f'{BASE}/search_state.json', 'r') as f:
    state = json.load(f)

state_idx = state['state_idx']
cat_idx = state['cat_idx']

# Advance state
state['state_idx'] = (state_idx + 1) % len(STATES)
if state['state_idx'] == 0:
    state['cat_idx'] = (cat_idx + 1) % 10

with open(f'{BASE}/search_state.json', 'w') as f:
    json.dump(state, f)

slot_state = STATES[state_idx]
slot_cat = CATEGORIES[cat_idx]
city = slot_state.split('/')[0]
st = slot_state.split('/')[1]

print(f"Running: {city}, {st} | {slot_cat}")

query = f"{slot_cat} services in {city}, {st} business name phone email address"
result = subprocess.run(["mmx", "search", "query", "--q", query, "--output", "json"], capture_output=True, text=True, timeout=60)

data = json.loads(result.stdout)
items = data.get("organic", [])
print(f"Results: {len(items)}")

BAD_DOMAINS = {'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com','facebook.com','linkedin.com','twitter.com','instagram.com','pinterest.com','zillow.com','realtor.com','redfin.com','bing.com','google.com','gov','mil'}
email_pat = re.compile(r'[\w.%+-]+@[\w.-]+\.[\w.-]+')

seen = []
with open(f'{BASE}/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

new_records = []
for item in items:
    title = item.get('title','')
    snippet = item.get('snippet','')
    link = item.get('link','')
    
    if link in seen_set:
        continue
    
    emails = email_pat.findall(snippet)
    email = None
    if emails:
        email = emails[0].lower().rstrip('.,; ')
        d = email.split('@')[1] if '@' in email else ''
        if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
            # Accept consumer-domain if multi-word business name
            words = title.split()
            if len(words) < 2:
                email = None
            else:
                # Check it's not lead/finder/list/data
                if any(k in d for k in ['lead','finder','list','data']):
                    email = None
        if email and d.endswith('.edu'):
            email = None
    
    if email and email in seen_set:
        continue
    
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', snippet)
    phone = phones[0] if phones else ''
    
    name = title.split(' - ')[0].split(' – ')[0].strip()[:100]
    
    new_records.append({'name': name, 'email': email or '', 'phone': phone, 'address': '', 'city': city, 'county': '', 'state': st, 'zip': '', 'category': slot_cat, 'found_date': today})
    if email:
        seen.append(email)
    seen_set.add(link)

print(f"New records: {len(new_records)}")

# Append to services.md
if new_records:
    with open(f'{BASE}/services.md', 'a') as f:
        # Ensure newline before append
        f.write('\n')
        for rec in new_records:
            f.write(f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} | {rec['zip']} | {rec['category']} | {rec['found_date']} |\n")

    # Update seen_emails
    with open(f'{BASE}/seen_emails.json', 'w') as f:
        json.dump(seen, f)
    
    # Send email
    rows = []
    for rec in new_records:
        rows.append(f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['state']} |")
    body = "New leads found:\n\n| name | email | phone | address | city | state |\n" + "\n".join(rows)
    
    msg = __import__('email.mime.multipart', fromlist=['MIMEMultipart']).MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = f'New Leads: {city}, {st}'
    msg.attach(__import__('email.mime.text', fromlist=['MIMEText']).MIMEText(body, 'plain'))
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
        s.login('data@skylink-ltd.com', 'Skylink#2026')
        s.send_message(msg)
    print("Email sent")

print(f"[SEARCH] {slot_cat} | {city}, {st} → +{len(new_records)} records → [DONE]")