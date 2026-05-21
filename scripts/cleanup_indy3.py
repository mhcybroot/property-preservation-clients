import subprocess, json, re
from datetime import date

STATES = ["Alabama/Birmingham","Alaska/Anchorage","Arizona/Phoenix","Arkansas/Little Rock","California/Sacramento","Colorado/Denver","Connecticut/Hartford","Delaware/Wilmington","Florida/Jacksonville","Georgia/Atlanta","Hawaii/Honolulu","Idaho/Boise","Illinois/Springfield","Indiana/Indianapolis","Iowa/Des Moines","Kansas/Topeka","Kentucky/Louisville","Louisiana/Baton Rouge","Maine/Augusta","Maryland/Baltimore","Massachusetts/Boston","Michigan/Lansing","Minnesota/St. Paul","Mississippi/Jackson","Missouri/Jefferson City","Montana/Helena","Nebraska/Lincoln","Nevada/Las Vegas","New Hampshire/Concord","New Jersey/Trenton","New Mexico/Santa Fe","New York/Albany","North Carolina/Raleigh","North Dakota/Bismarck","Ohio/Columbus","Oklahoma/Oklahoma City","Oregon/Salem","Pennsylvania/Harrisburg","Rhode Island/Providence","South Carolina/Columbia","South Dakota/Pierre","Tennessee/Nashville","Texas/Austin","Utah/Salt Lake City","Vermont/Montpelier","Virginia/Richmond","Washington/Olympia","West Virginia/Charleston","Wisconsin/Madison","Wyoming/Cheyenne"]
CATEGORIES = ["Plumber","HVAC Contractor","Electrician","Roofing Contractor","Handyman","Landscaping Service","Painting Service","Cleaning Service","Snow Removal Service","Moving Service"]

city = "Indianapolis"
state_name = "Indiana"
cat_name = "Cleaning Service"

queries = [
    "Cleaning Service in Indianapolis Indiana business name phone email address",
    "site:facebook.com OR site:instagram.com Cleaning Service Indianapolis Indiana contact email",
    "Maid Service Indianapolis Indiana business email contact phone"
]

organic_results = []
for q in queries:
    result = subprocess.run(["mmx", "search", "query", "--q", q, "--output", "json"],
        capture_output=True, text=True, timeout=60)
    data = json.loads(result.stdout)
    organic_results.extend(data.get("organic", []))

with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

email_pat = re.compile(r'[\w.%+-]+@[\w.-]+\.[\w.-]+')
phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

BAD_DOMAINS = {'yelp.com','instagram.com','facebook.com','linkedin.com','twitter.com',
               'pinterest.com','bing.com','google.com','hotmail.com','gmail.com','yahoo.com',
               'outlook.com','aol.com','zillow.com','realtor.com','redfin.com','gov','mil'}

def is_proper_business_name(name):
    """Strict check: 2+ alpha words, no hashtags/social artifacts, has capital letter in first word"""
    # Remove social artifacts
    name = re.sub(r'[@#]\w+', '', name)  # Remove @mentions and #hashtags
    name = re.sub(r'\s+', ' ', name).strip()
    words = [w for w in name.split() if w.isalpha()]
    if len(words) < 2:
        return False
    # Must have at least 2 words with letters
    has_capital = any(w[0].isupper() for w in words if w)
    return has_capital

def is_junk_email(email, business_name=''):
    if not email or '@' not in email:
        return True
    d = email.lower().split('@')[1].rstrip('.,; ')
    if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
        if is_proper_business_name(business_name):
            return False
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']):
        return True
    return False

new_records = []
seen_links = set()

for item in organic_results:
    snippet = item.get('snippet', '')
    title = item.get('title', '')
    link = item.get('link', '')
    
    if link in seen_links:
        continue
    
    emails_in_snippet = email_pat.findall(snippet)
    phones_in_snippet = phone_pat.findall(snippet)
    
    email = None
    for e in emails_in_snippet:
        e_clean = e.lower().rstrip('.,; ')
        if not is_junk_email(e_clean, title):
            if e_clean not in seen_set:
                email = e_clean
                break
    
    phone = phones_in_snippet[0] if phones_in_snippet else ''
    name = re.sub(r'[-–].*$', '', title).strip()
    name = re.sub(r'[@#]\w+', '', name)
    name = re.sub(r'\s+', ' ', name).strip()[:100]
    
    if email:
        new_records.append({
            'name': name, 'email': email, 'phone': phone,
            'address': 'unknown', 'city': city, 'county': 'Marion',
            'state': state_name, 'zip': '', 'category': cat_name,
            'found_date': date.today().isoformat()
        })
        seen_links.add(link)
        seen_set.add(email)

# Phone-only: proper business names with phone but no email
for item in organic_results:
    snippet = item.get('snippet', '')
    title = item.get('title', '')
    link = item.get('link', '')
    
    if link in seen_links:
        continue
    
    emails_in_snippet = email_pat.findall(snippet)
    phones_in_snippet = phone_pat.findall(snippet)
    
    if not emails_in_snippet and phones_in_snippet:
        name = re.sub(r'[-–].*$', '', title).strip()
        name = re.sub(r'[@#]\w+', '', name)
        name = re.sub(r'\s+', ' ', name).strip()[:100]
        if is_proper_business_name(name):
            new_records.append({
                'name': name, 'email': '', 'phone': phones_in_snippet[0],
                'address': 'unknown', 'city': city, 'county': 'Marion',
                'state': state_name, 'zip': '', 'category': cat_name,
                'found_date': date.today().isoformat()
            })
            seen_links.add(link)

print(f"Total organic results: {len(organic_results)}")
print(f"Email records: {len([r for r in new_records if r['email']])}")
print(f"Phone-only records: {len([r for r in new_records if not r['email']])}")
for r in new_records:
    print(f"  + {r['name'][:50]} | {r['email']} | {r['phone']}")

unique = {}
for r in new_records:
    if r['email']:
        unique[r['email']] = r
    else:
        unique[r['phone']] = r

print(f"Unique records: {len(unique)}")

# Write to services.md
if unique:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/services.md', 'a') as f:
        f.write('\n')
        for r in unique.values():
            line = f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |"
            f.write(line + '\n')

    for r in unique.values():
        if r['email'] and r['email'] not in seen:
            seen.append(r['email'])
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/seen_emails.json', 'w') as f:
        json.dump(seen, f)

    # Send email
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    body = f"New Cleaning Service leads found for Indianapolis, Indiana:\n\n"
    body += "| name | email | phone | address | city | county | state | category | found_date |\n"
    body += "|------|-------|-------|---------|------|-------|------|----------|\n"
    for r in unique.values():
        body += f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['category']} | {r['found_date']} |\n"
    
    msg = MIMEMultipart()
    msg['From'] = 'data@skylink-ltd.com'
    msg['To'] = 'data@skylink-ltd.com'
    msg['Subject'] = f'New Leads: Indianapolis, Indiana'
    msg.attach(MIMEText(body, 'plain'))
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
            s.login('data@skylink-ltd.com', 'Skylink#2026')
            s.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Email error: {e}")

# Advance state: Indiana/Indianapolis -> Iowa/Des Moines/Plumber
new_state = {"state_idx": 14, "cat_idx": 0}
with open('/home/mhcybroot/jobs/property-preservation-clients/data/search_state.json', 'w') as f:
    json.dump(new_state, f)

print("DONE")