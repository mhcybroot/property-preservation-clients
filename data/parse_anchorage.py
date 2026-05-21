import json, re

raw = '''{"organic": [
    {"title": "Business Licensing - commerce.Alaska.gov", "link": "https://www.commerce.alaska.gov/web/cbpl/BusinessLicensing", "snippet": "Contact Information. Please provide a Business Name and Business License Number (if you have one) in the subject line of your e-mail. For security ...", "date": ""},
    {"title": "Snow Removal & Plowing - Anchorage - Be Happy Property Services", "link": "https://behappyps.com/services/snow-removal/", "snippet": "Commercial & residential snow plowing and de-icing services in Anchorage. We keep your parking lot or driveway snow and ice free all winter long.", "date": ""},
    {"title": "Sidewalk Snow Removal - Anchorage Downtown Partnership", "link": "https://anchoragedowntown.org/services-programs/snow-removal/", "snippet": "Please dial (907) 277-0141 for status updates or to ... Please dial (907) 279-5650 opt. 5, or email info@anchoragedowntown.org.", "date": ""},
    {"title": "CONTACT - Snow Business, LLC - Snow Plowing Near Me", "link": "https://snowbusinessllc.com/contact/", "snippet": "Get in Touch with Our Snow Removal Experts · Anchorage, AK 99507 · (907) 350-1100 · paul@snowbusinessllc.com.", "date": ""},
    {"title": "Expert Snow Management in Anchorage, Alaska", "link": "http://alaskalandworks.com/expert-snows-management-in-anchorage-alaska/", "snippet": "Contact Info. P.O. Box 111613. Anchorage, AK 99511 (907) 350-1622 info@alaskalandworks.com.", "date": ""},
    {"title": "Alaska Snow Removal Overview, Address & Contact - Prospeo", "link": "https://prospeo.io/c/alaska-snow-removal", "snippet": "Alaska Snow Removal uses 5 email formats. The most common is {first name}.{last name}@company.com (e.g., john.doe@company.com) ...", "date": ""},
    {"title": "Plow Now AK | Anchorage AK - Facebook", "link": "https://www.facebook.com/PlowNowAK/", "snippet": "Plow Now AK, Anchorage. 413 likes · 1 talking about this. Commercial/Residential Plowing and Sanding...on call 24/7 call,text or email for an estimate.", "date": ""},
    {"title": "Contact Northern Snow Removal: Get a Free Quote Today!", "link": "https://www.northernsnowremoval.co/contact", "snippet": "Phone. (907) 317-7396. Available for emergencies ; Email. northernsnowremoval382@gmail.com. We respond within 24 hours ; Service Area. Anchorage, Eagle River, ...", "date": ""},
    {"title": "THE BEST 10 SNOW REMOVAL IN ANCHORAGE, AK - HOURS", "link": "https://www.yelp.com/search?cflt=snowremoval&find_loc=Anchorage%2C+AK", "snippet": "These are some businesses with a large number of reviews for snow removal in Anchorage, AK: Gage Tree Service (30 reviews). Just Lawns (25 reviews). Nordic ...", "date": ""}
  ]}'''

data = json.loads(raw)
items = data.get('organic', [])

email_pat = re.compile(r'[\w.%+-]+@[\w.-]+\.[\w.-]+')
phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

BAD_DOMAINS = {'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com','facebook.com','instagram.com','linkedin.com','twitter.com','pinterest.com','zillow.com','realtor.com','redfin.com','gov','mil','edu','bing.com','google.com'}

records = []
for item in items:
    title = item['title']
    snippet = item['snippet']
    link = item['link']
    
    if any(x in link.lower() for x in ['commerce.alaska.gov','yelp.com','prospeo.io','facebook.com']):
        continue
    if any(x in title.lower() for x in ['business licensing','prospeo']):
        continue
    
    emails = email_pat.findall(snippet)
    phones = phone_pat.findall(snippet)
    
    if not emails:
        continue
    
    e = emails[0].lower().rstrip('.,; ')
    domain = e.split('@')[1]
    
    # consumer domain exception for multi-word business names
    if domain in ('gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com'):
        words = title.split()
        if len(words) < 2:
            continue
    
    if any(domain.endswith('.'+b) or domain == b for b in BAD_DOMAINS):
        continue
    
    phone = phones[0] if phones else ''
    name = re.sub(r'[-–].*', '', title).strip()
    name = re.sub(r'[\* ]+', ' ', name).strip()[:100]
    
    print(f'Name: {name[:80]} | Email: {e} | Phone: {phone} | Link: {link}')