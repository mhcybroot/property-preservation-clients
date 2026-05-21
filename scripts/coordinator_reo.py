#!/usr/bin/env python3
"""REO coordinator — same pattern but for REO services."""
import json, os, subprocess, sys
from datetime import datetime

BASE = "/home/mhcybroot/jobs/property-preservation-clients"
DATA = f"{BASE}/data"
REO_MD = f"{DATA}/reo_services.md"
STATE_FILE = f"{DATA}/reo_search_state.json"
SEEN_FILE = f"{DATA}/reo_seen_emails.json"

CATEGORIES = [
    "Real Estate Agent", "Property Manager", "Auction Services",
    "Cash Offer Home Buyer", "Short Sale Services", "Foreclosure Attorney",
    "Title Company", "Home Inspector", "Mortgage Broker", "Hard Money Lender"
]

STATES = [
    ("Alabama","Birmingham"),("Alaska","Anchorage"),("Arizona","Phoenix"),
    ("Arkansas","Little Rock"),("California","Sacramento"),("Colorado","Denver"),
    ("Connecticut","Hartford"),("Delaware","Wilmington"),("Florida","Jacksonville"),
    ("Georgia","Atlanta"),("Hawaii","Honolulu"),("Idaho","Boise"),
    ("Illinois","Springfield"),("Indiana","Indianapolis"),("Iowa","Des Moines"),
    ("Kansas","Topeka"),("Kentucky","Louisville"),("Louisiana","Baton Rouge"),
    ("Maine","Augusta"),("Maryland","Baltimore"),("Massachusetts","Boston"),
    ("Michigan","Lansing"),("Minnesota","St. Paul"),("Mississippi","Jackson"),
    ("Missouri","Jefferson City"),("Montana","Helena"),("Nebraska","Lincoln"),
    ("Nevada","Las Vegas"),("New Hampshire","Concord"),("New Jersey","Trenton"),
    ("New Mexico","Santa Fe"),("New York","Albany"),("North Carolina","Raleigh"),
    ("North Dakota","Bismarck"),("Ohio","Columbus"),("Oklahoma","Oklahoma City"),
    ("Oregon","Salem"),("Pennsylvania","Harrisburg"),("Rhode Island","Providence"),
    ("South Carolina","Columbia"),("South Dakota","Pierre"),("Tennessee","Nashville"),
    ("Texas","Austin"),("Utah","Salt Lake City"),("Vermont","Montpelier"),
    ("Virginia","Richmond"),("Washington","Olympia"),("West Virginia","Charleston"),
    ("Wisconsin","Madison"),("Wyoming","Cheyenne")
]

BAD_DOMAINS = {
    "yelp.com","instagram.com","facebook.com","linkedin.com","twitter.com",
    "pinterest.com","bing.com","google.com","hotmail.com","gmail.com","yahoo.com",
    "outlook.com","aol.com","zillow.com","realtor.com","redfin.com","gov","mil"
}

def is_junk(email):
    if not email or '@' not in email:
        return True
    d = email.lower().split('@')[1]
    if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
        return True
    if d.endswith('.edu') or any(k in d for k in ['lead','finder','list','data']):
        return True
    return False

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"state_idx": 0, "cat_idx": 0}

def save_state(s):
    with open(STATE_FILE, 'w') as f:
        json.dump(s, f)

def next_slot():
    s = load_state()
    si, ci = s["state_idx"], s["cat_idx"]
    state, city = STATES[si]
    cat = CATEGORIES[ci]
    ci = (ci + 1) % len(CATEGORIES)
    if ci == 0:
        si = (si + 1) % len(STATES)
    save_state({"state_idx": si, "cat_idx": ci})
    return state, city, cat

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(se):
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(se), f)

def ensure_header(path, cols):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, 'w') as f:
            f.write("| " + " | ".join(cols) + " |\n")
            f.write("|" + "|".join(["------"]*len(cols)) + "|\n")

def append_row(path, vals):
    with open(path, 'a') as f:
        f.write("| " + " | ".join(str(v) for v in vals) + " |\n")

if __name__ == "__main__":
    state, city, category = next_slot()
    date = datetime.now().strftime("%Y-%m-%d")
    print(f"[REO SEARCH] {category} | {city}, {state}")

    query = f"{category} services in {city}, {state} real estate"
    social_query = (
        f"site:linkedin.com OR site:facebook.com OR site:instagram.com "
        f'"{category}" "{city}" contact email owner -gmail -yahoo -hotmail -outlook'
    )
    about_query = (
        f'"{category}" "{city}" "@" company "about" OR "contact" page '
        f'-gmail -yahoo -hotmail -outlook -lead -list -finder'
    )

    result = subprocess.run(
        ["mmx", "search", "query", "--q", query, "--output", "json"],
        capture_output=True, text=True, timeout=60
    )
    result_social = subprocess.run(
        ["mmx", "search", "query", "--q", social_query, "--output", "json"],
        capture_output=True, text=True, timeout=60
    )
    result_about = subprocess.run(
        ["mmx", "search", "query", "--q", about_query, "--output", "json"],
        capture_output=True, text=True, timeout=60
    )

    output = result.stdout + result_social.stdout + result_about.stdout

    import re
    email_pat = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

    # Parse concatenated JSON blobs
    all_results = []
    for chunk in re.split(r'(?=\{"organic":)', output.strip()):
        chunk = chunk.strip()
        if not chunk.startswith('{"organic":'):
            continue
        try:
            data = json.loads(chunk)
            all_results.extend(data.get("organic", []))
        except Exception:
            continue

    seen = load_seen()
    ensure_header(REO_MD, ["name","email","phone","address","city","county","state","zip","category","found_date"])

    new_count = 0
    seen_links = set()
    for item in all_results:
        snippet = item.get("snippet", "")
        title = item.get("title", "")
        link = item.get("link", "")

        # Skip titles that look like lead-gen lists
        title_lower = title.lower()
        if any(k in title_lower for k in ['lead finder','list of','prospecting','email list']):
            continue

        emails = email_pat.findall(snippet)
        if not emails:
            continue
        email = emails[0].lower()
        if is_junk(email) or email in seen:
            continue
        if link and link in seen_links:
            continue

        phones = phone_pat.findall(snippet)
        phone = phones[0] if phones else ""

        name = re.sub(r'\s*[-|–].*$', '', title).strip()
        name = re.sub(r'^[\*\s]+|[\*\s]+$', '', name).strip()[:100]
        if not name or len(name) < 3:
            name = f"{category} - {city}"

        addr_m = re.search(r'\d+\s+[A-Za-z][A-Za-z\s]*?(?:ave|blvd|st|rd|dr|ln|way|pl|ct)[.,]?\s*[A-Za-z]*\s*\d{5}', snippet, re.I)
        address = addr_m.group(0)[:200] if addr_m else "unknown"
        city_zip = re.search(r'[A-Z]{2}[.,]?\s*\d{5}', snippet)
        if city_zip and address == "unknown":
            address = city_zip.group(0)

        seen.add(email)
        if link:
            seen_links.add(link)
        append_row(REO_MD, [name, email, phone, address, city, "", state, "", category, date])
        new_count += 1
        print(f"  + {name} | {email}")

    save_seen(seen)
    print(f"[DONE] new={new_count}")