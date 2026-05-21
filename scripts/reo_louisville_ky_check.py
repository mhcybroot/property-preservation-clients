import json, re

# Load seen emails
try:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json') as f:
        seen = json.load(f)
except:
    seen = []
seen_set = set(seen)

CATS = ['Real Estate Agent', 'Property Manager', 'Auction Services', 'Cash Offer Home Buyer', 'Short Sale Services', 'Foreclosure Attorney', 'Title Company', 'Home Inspector', 'Mortgage Broker', 'Hard Money Lender']
STATES = ['Alabama/Birmingham', 'Alaska/Anchorage', 'Arizona/Phoenix', 'Arkansas/Little Rock', 'California/Sacramento', 'Colorado/Denver', 'Connecticut/Hartford', 'Delaware/Wilmington', 'Florida/Jacksonville', 'Georgia/Atlanta', 'Hawaii/Honolulu', 'Idaho/Boise', 'Illinois/Springfield', 'Indiana/Indianapolis', 'Iowa/Des Moines', 'Kansas/Topeka', 'Kentucky/Louisville', 'Louisiana/Baton Rouge', 'Maine/Augusta', 'Maryland/Baltimore', 'Massachusetts/Boston', 'Michigan/Lansing', 'Minnesota/St. Paul', 'Mississippi/Jackson', 'Missouri/Jefferson City', 'Montana/Helena', 'Nebraska/Lincoln', 'Nevada/Las Vegas', 'New Hampshire/Concord', 'New Jersey/Trenton', 'New Mexico/Santa Fe', 'New York/Albany', 'North Carolina/Raleigh', 'North Dakota/Bismarck', 'Ohio/Columbus', 'Oklahoma/Oklahoma City', 'Oregon/Salem', 'Pennsylvania/Harrisburg', 'Rhode Island/Providence', 'South Carolina/Columbia', 'South Dakota/Pierre', 'Tennessee/Nashville', 'Texas/Austin', 'Utah/Salt Lake City', 'Vermont/Montpelier', 'Virginia/Richmond', 'Washington/Olympia', 'West Virginia/Charleston', 'Wisconsin/Madison', 'Wyoming/Cheyenne']
state = 'Kentucky'
city = 'Louisville'
cat = 'Home Inspector'
today = '2026-05-22'

records = [
    {'name': 'Elite Home Inspections LLC', 'email': 'elitehomeinspections@twc.com', 'phone': '502-648-9294', 'address': '3044 Bardstown Rd, Ste. 226', 'city': 'Louisville', 'county': 'Jefferson', 'state': 'KY', 'zip': '40205'},
    {'name': 'Home Inspections Services', 'email': 'dougs@hiswebsite.org', 'phone': '502-817-1915', 'address': '102 Daventry Lane, Ste. #8', 'city': 'Louisville', 'county': 'Jefferson', 'state': 'KY', 'zip': '40223'},
    {'name': 'Home Inspections Services', 'email': 'jeremyf@hiswebsite.org', 'phone': '502-423-7575', 'address': '102 Daventry Lane, Ste. #8', 'city': 'Louisville', 'county': 'Jefferson', 'state': 'KY', 'zip': '40223'},
    {'name': 'Home Inspections Services', 'email': 'jeans@hiswebsite.org', 'phone': '502-500-9486', 'address': '102 Daventry Lane, Ste. #8', 'city': 'Louisville', 'county': 'Jefferson', 'state': 'KY', 'zip': '40223'},
    {'name': 'Clarity Home Inspections', 'email': '', 'phone': '502-251-4888', 'address': '', 'city': 'Louisville', 'county': 'Jefferson', 'state': 'KY', 'zip': ''},
    {'name': 'ABI Home Inspection Services', 'email': '', 'phone': '502-938-5190', 'address': '', 'city': 'Louisville', 'county': 'Jefferson', 'state': 'KY', 'zip': ''},
]

email_pat = re.compile(r'[\w.%+-]+@[\w.-]+\.[\w.-]+')
BAD_DOMAINS = {'yelp.com','instagram.com','facebook.com','linkedin.com','twitter.com','pinterest.com','bing.com','google.com','hotmail.com','gmail.com','yahoo.com','outlook.com','aol.com','zillow.com','realtor.com','redfin.com','gov','mil'}

def is_junk_email(email, business_name=''):
    if not email or '@' not in email: return True
    d = email.lower().split('@')[1].rstrip('.,; ')
    if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
        if d in ('gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com'):
            words = business_name.split()
            if len(words) >= 2: return False
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']): return True
    return False

new_records = []
added_emails = []
for r in records:
    email = r.get('email','').lower().strip()
    if email and email not in seen_set:
        if not is_junk_email(email, r['name']):
            seen_set.add(email)
            new_records.append(r)
            added_emails.append(email)
            print(f"NEW: {r['name']} | {email}")
        else:
            print(f"JUNK: {r['name']} | {email}")
    elif not email:
        print(f"PHONE-ONLY: {r['name']} | {r['phone']}")
    else:
        print(f"SEEN: {r['name']} | {email}")

print(f'\nTotal new records: {len(new_records)}')
print(f'Emails to add: {added_emails}')