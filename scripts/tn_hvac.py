import json, subprocess, re, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

STATES = ["Alabama/Birmingham", "Alaska/Anchorage", "Arizona/Phoenix", "Arkansas/Little Rock", "California/Sacramento", "Colorado/Denver", "Connecticut/Hartford", "Delaware/Wilmington", "Florida/Jacksonville", "Georgia/Atlanta", "Hawaii/Honolulu", "Idaho/Boise", "Illinois/Springfield", "Indiana/Indianapolis", "Iowa/Des Moines", "Kansas/Topeka", "Kentucky/Louisville", "Louisiana/Baton Rouge", "Maine/Augusta", "Maryland/Baltimore", "Massachusetts/Boston", "Michigan/Lansing", "Minnesota/St. Paul", "Mississippi/Jackson", "Missouri/Jefferson City", "Montana/Helena", "Nebraska/Lincoln", "Nevada/Las Vegas", "New Hampshire/Concord", "New Jersey/Trenton", "New Mexico/Santa Fe", "New York/Albany", "North Carolina/Raleigh", "North Dakota/Bismarck", "Ohio/Columbus", "Oklahoma/Oklahoma City", "Oregon/Salem", "Pennsylvania/Harrisburg", "Rhode Island/Providence", "South Carolina/Columbia", "South Dakota/Pierre", "Tennessee/Nashville", "Texas/Austin", "Utah/Salt Lake City", "Vermont/Montpelier", "Virginia/Richmond", "Washington/Olympia", "West Virginia/Charleston", "Wisconsin/Madison", "Wyoming/Cheyenne"]
CATEGORIES = ["Plumber", "HVAC Contractor", "Electrician", "Roofing Contractor", "Handyman", "Landscaping Service", "Painting Service", "Cleaning Service", "Snow Removal Service", "Moving Service"]

STATE_FILE = '/home/mhcybroot/jobs/property-preservation-clients/data/search_state.json'
SEEN_FILE = '/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json'
SERVICES_FILE = '/home/mhcybroot/jobs/property-preservation-clients/data/services.md'

# Load state
with open(STATE_FILE, 'r') as f:
    state = json.load(f)
state_idx = state['state_idx']
cat_idx = state['cat_idx']

# Tennessee/Nashville -> search Clarksville (largest city, Montgomery County)
city_state = STATES[state_idx]
state_name, capital_city = city_state.split('/')
city = "Clarksville"
state_abbr = state_name[:2].upper()

category = CATEGORIES[cat_idx]

# Advance state
next_state_idx = (state_idx + 1) % len(STATES)
next_cat_idx = cat_idx
with open(STATE_FILE, 'w') as f:
    json.dump({'state_idx': next_state_idx, 'cat_idx': next_cat_idx}, f)

print(f"[SEARCH] {category} | {city}, {state_name}")
print(f"State idx: {state_idx} -> {next_state_idx}, cat_idx: {cat_idx}")

# Load seen emails
with open(SEEN_FILE, 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

# Search query (city disambiguation: Clarksville TN, not Clarksville wherever else)
query = f"{category} services in {city} {state_name} business name phone email address"
result = subprocess.run(["mmx", "search", "query", "--q", query, "--output", "json"],
    capture_output=True, text=True, timeout=60)

try:
    data = json.loads(result.stdout)
    items = data.get("organic", [])
except:
    items = []

email_pat = re.compile(r'[\w.%+-]+@[\w.-]+\.[\w.-]+')
phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
BAD_DOMAINS = {'yelp.com','instagram.com','facebook.com','linkedin.com','twitter.com','pinterest.com','bing.com','google.com','hotmail.com','gmail.com','yahoo.com','outlook.com','aol.com','zillow.com','realtor.com','redfin.com','gov','mil'}

def is_junk_email(email, business_name=''):
    if not email or '@' not in email: return True
    d = email.lower().split('@')[1]
    if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
        if d in ('gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com'):
            words = business_name.split()
            if len(words) >= 2:
                return False
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']):
        return True
    return False

new_records = []
today = date.today().isoformat()

for item in items:
    title = item.get('title', '')
    snippet = item.get('snippet', '')
    link = item.get('link', '')

    emails = email_pat.findall(snippet)
    phones = phone_pat.findall(snippet)

    if emails:
        email = emails[0].lower().rstrip('.,; ')
        if is_junk_email(email, title):
            continue
        if email in seen_set:
            continue
    else:
        email = None

    if email:
        seen_set.add(email)
        seen.append(email)
        phones_found = phones[0] if phones else ''
        new_records.append({
            'name': title[:100],
            'email': email,
            'phone': phones_found,
            'address': '',
            'city': city,
            'county': 'Montgomery',
            'state': state_abbr,
            'zip': '',
            'category': category,
            'found_date': today
        })
        print(f"  + {title[:60]} | {email}")

print(f"New records: {len(new_records)}")

# Append to services.md
if new_records:
    with open(SERVICES_FILE, 'a') as f:
        f.write('\n')
        for r in new_records:
            f.write(f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |\n")

    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f)

    # Send email
    body_lines = [f"New Leads: {city}, {state_name}\n"]
    body_lines.append("| name | email | phone | address | city | county | state | zip | category | found_date |")
    body_lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in new_records:
        body_lines.append(f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |")

    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = f"New Leads: {city}, {state_name}"
    msg.attach(MIMEText('\n'.join(body_lines), 'plain'))

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
            s.login('data@skylink-ltd.com', 'Skylink#2026')
            s.send_message(msg)
        print("Email sent OK")
    except Exception as e:
        print(f"Email error: {e}")

print(f"[DONE] new={len(new_records)}")