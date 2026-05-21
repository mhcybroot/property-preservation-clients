import re
import json
from datetime import date

email_pat = re.compile(r'[\w.%+-]+@[\w.-]+\.[\w.-]+')

# Parse both mmx outputs
raw1 = '''{"organic": [{"title": "Christy's of Indiana", "link": "https://www.christys.com/", "snippet": "Christy's of Indiana is a family operated, full service, license auction gallery, founded in 1975."},{"title": "THE BEST 10 Auction Houses in Indianapolis, IN", "link": "https://www.yelp.com/search?cflt=auctionhouses&find_loc=Indianapolis%2C+IN", "snippet": "Best Auction Houses in Indianapolis, IN - Last Updated May 2026 - Christys of Indiana, Wickliff Auctioneers, Heimel Auction Service, Ripley Auctions ..."},{"title": "Earl's Auction Company - Indianapolis", "link": "https://www.earlsauction.com/", "snippet": "Auction Location: 5199 Lafayette Road, Indianapolis, Indiana 46254. Enter ... Earl's Auction Company & Liquidators, Inc."},{"title": "Foreclosure and Bank Owned Auctions in Indianapolis, IN", "link": "https://www.auction.com/residential/in/indianapolis_ct", "snippet": "Want to find and bid on homes in Indianapolis, IN? Auction.com Is the largest online source of properties not on the MLS."},{"title": "Jacksons Indiana Art Auctions & Real Estate", "link": "https://www.jacksons-auction.com/", "snippet": "Jacksons are the pioneers in Indiana Art Auctions and Indiana's Premiere Auction House for Fine Art and Real Estate."},{"title": "Burgess Auctions LLC | Estate Auctions & Liquidation Services ...", "link": "https://www.burgessauctions.com/", "snippet": "Central Indiana's trusted estate auction specialists since 1996. Professional estate liquidation, business auctions, and appraisal services in Indianapolis, ..."}]}'''

raw2 = '''{"organic": [{"title": "[PDF] 8/24/2022 - IN.gov", "link": "https://www.in.gov/pla/files/Auctioneer-CE-Providers2022.pdf", "snippet": "Contact. Street Address. City. State Zipcode. License. Email. Indiana Auctioneers. Association. 3178598990. Kathy Baber. GreenwoodIN. 46143."},{"title": "Contact Us - Midway Auction Company", "link": "https://midwayauction.com/contact-us/", "snippet": "Contact Us. Midway Auction Company 554 West State Road 42. Mooresville Indiana 46158. Phone: 317-996-2402. Email: sold@midwayauction.com. Contact Us."},{"title": "Campbell Auction Team | Licensed Auctioneers | Indiana and Ohio", "link": "https://www.campbellauctionteam.com/", "snippet": "auction team. Contact Us. Email: CampbellAuction@AOL.com. Phone: 765-914-0397."},{"title": "Indiana Auction Exchange Inc - GoToAuction.COM", "link": "https://www.gotoauction.com/companies/view/5358/Indiana-Auction-Exchange-Inc.html", "snippet": "Indiana Auction Exchange Inc. Contact Information. GoToAuction.com ID#:5358. Location: Elwood, IN Contact: Steve Goodman"},{"title": "Contact - Kraft Auction Service", "link": "https://kraftauctions.com/contact/", "snippet": "Email. Phone Number. Location. I'm an interested seller, I'm ... Managed by Kyle Dukes, this facility is the premiere auction facility of Northeast Indiana."},{"title": "Contact Us - Indiana Auto Auction", "link": "https://indianaautoauction.net/contact/", "snippet": "Indiana Auto Auction Physical Address 4425 W Washington Center Road Fort Wayne, IN 46818 Arbitration - (260) 740-7267 Call or Text: (260) 489-2776 Fax: (260"},{"title": "Huber Auction Group - Premier Local Auction Services in Central ...", "link": "https://huberauctiongroup.com/", "snippet": "Trust our experienced local team for professional auction management and outstanding results. Contact us today ... Indiana's Premiere Auction House. Email List. 0."},{"title": "Contact Us - Auction.com", "link": "https://www.auction.com/lp/contact-us/", "snippet": "Visit our Auction Help Center to learn how to buy properties and find answers to FAQs. media inquiries. Email us at media@auction.com."},{"title": "Contact - Indiana Auctioneers Association", "link": "https://indianaauctioneers.org/contact/", "snippet": "Indiana Auctioneers Association. 48 N. Emerson Avenue, Ste 300. Greenwood, IN 46143. Phone: 317-859-8990. Email: director@indianaauctioneers.org. Get Directions."}]}'''

data1 = json.loads(raw1)
data2 = json.loads(raw2)

items1 = data1.get('organic', [])
items2 = data2.get('organic', [])

print('Search 1 items:', len(items1))
print('Search 2 items:', len(items2))

# Check seen emails
with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json', 'r') as f:
    seen = json.load(f)
seen_set = set(seen)

new_records = []
today = date.today().isoformat()
BAD_DOMAINS = {'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com','facebook.com','linkedin.com','twitter.com','pinterest.com','bing.com','google.com','zillow.com','realtor.com','redfin.com','gov','mil','edu'}

def is_junk(email, name=''):
    if not email or '@' not in email:
        return True
    d = email.lower().split('@')[1].rstrip('.,; ')
    if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
        if d in ('gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com'):
            words = name.split()
            if len(words) >= 2:
                return False
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']):
        return True
    return False

def extract_record(item):
    title = item.get('title', '')
    snippet = item.get('snippet', '')
    link = item.get('link', '')
    
    emails_in_snippet = email_pat.findall(snippet)
    email = None
    if emails_in_snippet:
        email = emails_in_snippet[0].lower().rstrip('.,; ')
    
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', snippet)
    phone = phones[0] if phones else ''
    
    addr = ''
    
    name = title.split('|')[0].strip().split('-')[0].strip().split('–')[0].strip()[:100]
    
    return name, email, phone, addr

# Process both searches
all_items = items1 + items2
for item in all_items:
    name, email, phone, addr = extract_record(item)
    if email and is_junk(email, name):
        email = None
    if email and email in seen_set:
        print(f'SKIP (seen): {email}')
        continue
    if email:
        new_records.append({'name': name, 'email': email, 'phone': phone, 'address': addr, 'city': 'Indianapolis', 'county': 'Marion', 'state': 'IN', 'category': 'Auction Services', 'found_date': today})
        print(f'NEW: {name} | {email} | {phone}')

print(f'\nTotal new records: {len(new_records)}')

# Write new records to file
if new_records:
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_services.md', 'a') as f:
        # Ensure newline before append
        f.write('\n')
        for rec in new_records:
            line = f"| {rec['name']} | {rec['email']} | {rec['phone']} | {rec['address']} | {rec['city']} | {rec['county']} | {rec['state']} |  | {rec['category']} | {rec['found_date']} |"
            f.write(line + '\n')
    
    # Update seen_emails
    for rec in new_records:
        seen.append(rec['email'])
    with open('/home/mhcybroot/jobs/property-preservation-clients/data/reo_seen_emails.json', 'w') as f:
        json.dump(seen, f)
    
    print('Records appended and seen_emails updated')
else:
    print('No new records to append')