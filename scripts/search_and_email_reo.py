#!/usr/bin/env python3
"""
REO-specific client acquisition script.
Every run:
  1. Rotate state/category, run opencode search for new REO providers
  2. Validate unvalidated records (up to 5 per run) - send test emails
  3. Save validated.csv with status
  4. Send ONE combined HTML email with CSV attachments (services.csv + validated.csv)
"""

import csv
import json
import os
import re
import ssl
import smtplib
import subprocess
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

DATA_DIR = "/home/mhcybroot/jobs/property-preservation-clients/data"
CSV_FILE = f"{DATA_DIR}/reo_services.csv"
VALIDATED_CSV = f"{DATA_DIR}/reo_validated.csv"
STATE_FILE = f"{DATA_DIR}/reo_last_state.json"
CAT_FILE = f"{DATA_DIR}/reo_last_category.json"
CITY_FILE = f"{DATA_DIR}/reo_last_city.json"
LOG_FILE = f"{DATA_DIR}/reo_combined_log.json"
SEEN_FILE = f"{DATA_DIR}/reo_seen_emails.json"
VALID_STATUS_FILE = f"{DATA_DIR}/reo_validation_status.json"

SENDER = "data@skylink-ltd.com"
REPORT_TO = ["data@skylink-ltd.com"]
SMTP_PASS = "Skylink#2026"
SMTP_HOST = "skylink-ltd.com"
SMTP_PORT = 465

# CRM settings
CRM_BASE = "http://localhost:8080"
CRM_USER = "admin"
CRM_PASS = "password"

STATES_CITIES = {
    "Alabama": ["Birmingham", "Mobile", "Huntsville"],
    "Alaska": ["Anchorage", "Fairbanks", "Juneau"],
    "Arizona": ["Phoenix", "Tucson", "Scottsdale"],
    "Arkansas": ["Little Rock", "Fort Smith", "Fayetteville"],
    "California": ["Los Angeles", "San Diego", "San Francisco"],
    "Colorado": ["Denver", "Colorado Springs", "Boulder"],
    "Connecticut": ["Hartford", "New Haven", "Stamford"],
    "Delaware": ["Wilmington", "Dover", "Newark"],
    "Florida": ["Miami", "Orlando", "Tampa"],
    "Georgia": ["Atlanta", "Savannah", "Augusta"],
    "Hawaii": ["Honolulu", "Hilo", "Kailua"],
    "Idaho": ["Boise", "Nampa", "Idaho Falls"],
    "Illinois": ["Chicago", "Springfield", "Peoria"],
    "Indiana": ["Indianapolis", "Fort Wayne", "Evansville"],
    "Iowa": ["Des Moines", "Cedar Rapids", "Davenport"],
    "Kansas": ["Wichita", "Kansas City", "Topeka"],
    "Kentucky": ["Louisville", "Lexington", "Bowling Green"],
    "Louisiana": ["New Orleans", "Baton Rouge", "Shreveport"],
    "Maine": ["Portland", "Lewiston", "Bangor"],
    "Maryland": ["Baltimore", "Frederick", "Rockville"],
    "Massachusetts": ["Boston", "Worcester", "Springfield"],
    "Michigan": ["Detroit", "Grand Rapids", "Ann Arbor"],
    "Minnesota": ["Minneapolis", "Saint Paul", "Rochester"],
    "Mississippi": ["Jackson", "Gulfport", "Biloxi"],
    "Missouri": ["Kansas City", "St. Louis", "Springfield"],
    "Montana": ["Billings", "Missoula", "Great Falls"],
    "Nebraska": ["Omaha", "Lincoln", "Bellevue"],
    "Nevada": ["Las Vegas", "Reno", "Henderson"],
    "New Hampshire": ["Manchester", "Nashua", "Concord"],
    "New Jersey": ["Newark", "Jersey City", "Trenton"],
    "New Mexico": ["Albuquerque", "Santa Fe", "Las Cruces"],
    "New York": ["New York City", "Buffalo", "Rochester"],
    "North Carolina": ["Charlotte", "Raleigh", "Greensboro"],
    "North Dakota": ["Fargo", "Bismarck", "Grand Forks"],
    "Ohio": ["Columbus", "Cleveland", "Cincinnati"],
    "Oklahoma": ["Oklahoma City", "Tulsa", "Norman"],
    "Oregon": ["Portland", "Eugene", "Salem"],
    "Pennsylvania": ["Philadelphia", "Pittsburgh", "Harrisburg"],
    "Rhode Island": ["Providence", "Warwick", "Cranston"],
    "South Carolina": ["Charleston", "Columbia", "Greenville"],
    "South Dakota": ["Sioux Falls", "Rapid City", "Aberdeen"],
    "Tennessee": ["Nashville", "Memphis", "Knoxville"],
    "Texas": ["Houston", "Dallas", "Austin"],
    "Utah": ["Salt Lake City", "Provo", "Ogden"],
    "Vermont": ["Burlington", "Rutland", "Montpelier"],
    "Virginia": ["Virginia Beach", "Richmond", "Norfolk"],
    "Washington": ["Seattle", "Spokane", "Tacoma"],
    "West Virginia": ["Charleston", "Huntington", "Morgantown"],
    "Wisconsin": ["Milwaukee", "Madison", "Green Bay"],
    "Wyoming": ["Cheyenne", "Casper", "Laramie"],
}
STATES = list(STATES_CITIES.keys())

# REO-specific service categories
CATEGORIES = [
    "REO Property Preservation",
    "Bank Owned Property Maintenance",
    "Real Estate Owned Services",
    "REO Asset Management",
    "Default Property Preservation",
    "Cash Offer Property Services",
    "Pre-Foreclosure Property Services",
    "Auction Property Services",
    "Short Sale Property Services",
    "HUD Property Preservation",
]

FIELDS = ["name", "email", "website", "phone", "address", "city", "county", "state", "zip",
          "category", "found_date", "email_valid", "phone_valid", "address_valid",
          "verified", "verified_date", "notes"]


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


# ── ROTATION HELPERS ──────────────────────────────────────────────────────────

def get_next_state():
    d = load_json(STATE_FILE, {"index": 0})
    s = STATES[d["index"]]
    d["index"] = (d["index"] + 1) % len(STATES)
    save_json(STATE_FILE, d)
    return s


def get_next_category():
    d = load_json(CAT_FILE, {"index": 0})
    c = CATEGORIES[d["index"]]
    d["index"] = (d["index"] + 1) % len(CATEGORIES)
    save_json(CAT_FILE, d)
    return c


def get_next_city(state):
    d = load_json(CITY_FILE, {})
    idx = d.get(state, {}).get("index", 0)
    cities = STATES_CITIES.get(state, ["Main City"])
    city = cities[idx % len(cities)]
    if state not in d:
        d[state] = {"index": 0}
    d[state]["index"] = (idx + 1) % len(cities)
    save_json(CITY_FILE, d)
    return city


def load_seen_emails():
    return set(load_json(SEEN_FILE, []))


def add_seen_emails(emails):
    seen = load_seen_emails()
    seen.update(emails)
    save_json(SEEN_FILE, list(seen))


# ── EMAIL VALIDATION ─────────────────────────────────────────────────────────

def send_test_email(to_email, name, category):
    try:
        msg = f"""From: {SENDER}
To: {to_email}
Subject: Verification - {name}

This is an automated verification from Skylink Property Services.
If you received this, your contact is valid.

Category: {category}
Name: {name}

Reply to confirm or contact data@skylink-ltd.com
"""
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER, SMTP_PASS)
            server.sendmail(SENDER, [to_email], msg)
        return "sent"
    except Exception as e:
        return f"fail: {str(e)[:40]}"


def validate_record(email):
    """Return (email_ok, phone_ok, address_ok) based on format + test email."""
    email_ok = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
    result = send_test_email(email, "", "") if email_ok else None
    if result == "sent":
        email_ok = True
    elif result and result.startswith("fail:auth"):
        return "auth_error", None, None
    return email_ok, None, None


# ── CSV HELPERS ───────────────────────────────────────────────────────────────

def load_csv(path):
    rows = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return rows


def append_to_csv(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "website", "phone", "address", "city", "county", "state", "zip", "category", "found_date"])
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def load_validated():
    d = {}
    if os.path.exists(VALIDATED_CSV):
        for row in load_csv(VALIDATED_CSV):
            d[row["email"]] = row
    return d


def save_validated(all_records):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(VALIDATED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_records)


# ── CRM LEAD CREATION ─────────────────────────────────────────────────────────

_crm_token = None

def get_crm_token():
    global _crm_token
    if _crm_token:
        return _crm_token
    payload = json.dumps({"username": CRM_USER, "password": CRM_PASS}).encode()
    req = urllib.request.Request(f"{CRM_BASE}/api/auth/login",
        data=payload, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        _crm_token = json.loads(resp.read())["token"]
        return _crm_token
    except Exception as e:
        print(f"[CRM AUTH ERROR] {e}")
        return None


def create_crm_lead(name, email, phone, website, address, city, state, zipcode, category):
    """Create a lead in the CRM. Returns lead ID or None."""
    token = get_crm_token()
    if not token:
        return None
    # Truncate fields to DB column limits (companyName=180, contactName=120, email=120, phone=40, source=120)
    contact = name.strip()[:120]
    company = (address or category or "")[:180]
    email = email.strip()[:120]
    phone = phone.strip()[:40]
    source = "WEB"
    notes = f"Category: {category} | Address: {address}, {city}, {state} {zipcode}"[:2000]  # description is TEXT

    payload = json.dumps({
        "contactName": contact,
        "companyName": company,
        "email": email,
        "phone": phone,
        "source": source,
        "status": "NEW",
        "priority": "MEDIUM",
        "notes": notes
    }).encode()

    req = urllib.request.Request(f"{CRM_BASE}/api/leads",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        lead_id = data.get("lead", {}).get("id")
        print(f"[CRM] Created lead {lead_id}: {name}")
        return lead_id
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"[CRM ERROR] {e.code} creating lead {name}: {body}")
        return None
    except Exception as e:
        print(f"[CRM ERROR] {e}")
        return None


def create_crm_leads_from_records(rows):
    """Create CRM leads for all new records. Returns count of created leads."""
    created = 0
    for r in rows:
        lead_id = create_crm_lead(
            name=r.get("name", ""),
            email=r.get("email", ""),
            phone=r.get("phone", ""),
            website=r.get("website", ""),
            address=r.get("address", ""),
            city=r.get("city", ""),
            state=r.get("state", ""),
            zipcode=r.get("zip", ""),
            category=r.get("category", "")
        )
        if lead_id:
            created += 1
    return created


# ── PARSE OPENCODE OUTPUT ────────────────────────────────────────────────────
# Handles opencode build agent output — two formats:
#   1) Markdown table: | Business | Phone | Email | Address |
#   2) Bulleted list: **1. Business\n- Phone: ...\n- Email: ...\n- Address: ...
# Known bad email domains (not business contacts)
BAD_DOMAINS = {
    "yelp.com", "instagram.com", "facebook.com", "linkedin.com",
    "twitter.com", "pinterest.com", "bing.com", "google.com",
    "hotmail.com", "gmail.com", "yahoo.com", "outlook.com", "aol.com",
    "zillow.com", "realtor.com", "redfin.com", "gov", "mil",
}

def is_junk_email(email):
    """Return True if email domain is a known junk/consumer domain."""
    domain = email.lower().split('@')[1] if '@' in email else ''
    if not domain:
        return True
    for bad in BAD_DOMAINS:
        if domain == bad or domain.endswith(f'.{bad}'):
            return True
    return False

def parse_table_row(row_text):
    """Parse one row of a markdown table, return (name, email, phone, address, city, zipcode) or None."""
    cells = [c.strip() for c in row_text.split('|')]
    cells = [c for c in cells if c and c not in ('---', '...')]

    email_pat = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

    name = email = phone = address = city = zipcode = ''

    for i, cell in enumerate(cells):
        cell_lower = cell.lower()
        if i == 0 and cell and not cell.startswith('|'):
            name = cell
        if 'email' in cell_lower and i + 1 < len(cells):
            email = cells[i + 1]
        elif 'phone' in cell_lower and i + 1 < len(cells):
            phone = cells[i + 1]
        elif 'address' in cell_lower and i + 1 < len(cells):
            address = cells[i + 1]
        elif 'street' in cell_lower and i + 1 < len(cells):
            address = cells[i + 1]
        elif 'city' in cell_lower and i + 1 < len(cells):
            city = cells[i + 1]
        if '@' in cell and not email:
            email = cell
        if not phone and phone_pat.search(cell):
            phone = phone_pat.search(cell).group()
        if not address and any(x in cell_lower for x in ('ave', 'blvd', 'st ', 'dr ', 'rd ', 'tr ', 'ln ', 'way')):
            if len(cell) > 5:
                address = cell

    if not name:
        for cell in cells:
            if cell and '@' not in cell and len(cell) > 2:
                name = cell
                break

    if name:
        name = re.sub(r'^[\*\s]+|[\*\s]+$', '', name).strip()[:100]
        if re.match(r'^(Phone:|Email:|Address:|\d+\.|\*\*|---+)', name):
            name = ''

    found_emails = email_pat.findall(email)
    email = found_emails[0].lower() if found_emails else ''

    for marker in ['###', '**2.', '**3.', '---', '2. ', '3. ', '**Note']:
        if marker in address:
            address = address.split(marker)[0].strip()
            break
    address = re.sub(r'\s+', ' ', address)[:200]

    return name.strip(), email, phone, address, city, zipcode


def parse_bulleted_entry(entry_text):
    """Parse a bulleted entry: **N. Business\n- Key: Value\n..."""
    name = email = phone = address = city = zipcode = ''

    header_m = re.match(r'^\s*\*\*\d+\.\s+([^\n]+?)\s*\*\*', entry_text)
    if header_m:
        name = header_m.group(1).strip()[:100]
    else:
        first_line = entry_text.strip().split('\n')[0]
        name = re.sub(r'^\s*\*\*\d+\.\s+|\s*\*\*$', '', first_line).strip()[:100]

    if name:
        name = re.sub(r'^[\*\s]+|[\*\s]+$', '', name).strip()[:100]
        if re.match(r'^(Phone:|Email:|Address:|\d+\. |---+)', name):
            name = ''

    email_pat = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    key_val_pat = re.compile(r'^\s*-\s+(Email|Phone|Address|Website):\s*(.+)$', re.IGNORECASE | re.MULTILINE)

    for m in key_val_pat.finditer(entry_text):
        key = m.group(1).lower()
        val = m.group(2).strip()
        if key == 'email':
            found = email_pat.findall(val)
            if found:
                email = found[0].lower()
        elif key == 'phone':
            phones = phone_pat.findall(val)
            phone = phones[0] if phones else (val if not phone else phone)
        elif key in ('address', 'website'):
            addr = val
            for marker in ['###', '**2.', '**3.', '---', '2. ', '3. ', '**Note']:
                if marker in addr:
                    addr = addr.split(marker)[0].strip()
                    break
            addr = re.sub(r'\s+', ' ', addr)[:200]
            if key == 'address' or ('@' not in addr and not addr.startswith('http')):
                if not address or len(addr) > len(address):
                    address = addr

    zip_m = re.search(r'\b(\d{5}(?:-\d{4})?)\b', address)
    if zip_m:
        zipcode = zip_m.group(1)

    return name, email, phone, address, city, zipcode


def parse_output(output, state, city, category):
    """Parse mmx search JSON output into rows."""
    rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    seen = load_seen_emails()

    try:
        data = json.loads(output)
        results = data.get("organic", [])
    except Exception:
        results = []

    email_pat = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')

    for item in results:
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        title = item.get("title", "")

        emails = email_pat.findall(snippet)
        if not emails:
            continue
        email = emails[0].lower()

        if is_junk_email(email):
            continue
        if email in seen:
            continue

        phones = phone_pat.findall(snippet)
        phone = phones[0] if phones else ""

        name = re.sub(r'\s*[-|–]\s*.*$', '', title).strip()
        name = re.sub(r'^[\*\s]+|[\*\s]+$', '', name).strip()[:100]
        if not name or len(name) < 2:
            name = f"{category} - {city}"

        address = ""
        addr_m = re.search(r'\d+\s+[A-Za-z][A-Za-z\s]+?(?:ave|blvd|st|rd|dr|tr|ln|way|pl|court|ct|highway|hwy)[.,]?\s*[A-Za-z]*\s*\d{5}', snippet, re.I)
        if addr_m:
            address = addr_m.group(0)
        city_zip = re.search(r'(?:CO|CA|TX|FL|NY)[.,]?\s*\d{5}', snippet)
        if city_zip and address:
            address += " " + city_zip.group(0)

        rows.append({
            "name": name, "email": email, "phone": phone,
            "address": address[:200], "city": city, "county": "",
            "state": state, "zip": "", "category": category,
            "found_date": today
        })
        seen.add(email)

    return rows


# ── VALIDATION ───────────────────────────────────────────────────────────────

def validate_all_records(max_per_run=5):
    """Validate up to max_per_run unvalidated records."""
    all_csv = load_csv(CSV_FILE)
    validated = load_validated()
    today = datetime.now().strftime("%Y-%m-%d")

    status = load_json(VALID_STATUS_FILE, {"last_index": 0})
    last_idx = status.get("last_index", 0)

    validated_count = 0
    auth_error = False

    for i, row in enumerate(all_csv):
        if i < last_idx:
            continue

        email = row.get("email", "").strip().lower()
        if not email or email in validated:
            last_idx = i + 1
            continue

        print(f"[VALIDATE] {i}: {email}")

        email_ok = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

        if email_ok:
            result = send_test_email(email, row.get("name", ""), row.get("category", ""))
            if result == "sent":
                email_ok = True
            elif "auth" in result:
                auth_error = True
                break

        phone_raw = row.get("phone", "")
        digits = re.sub(r'\D', '', phone_raw)
        phone_ok = len(digits) >= 10

        addr_raw = row.get("address", "")
        bad = any(b in addr_raw.lower() for b in ["not available", "not listed", "n/a", "**", "phone:", "email:"])
        address_ok = len(addr_raw.strip()) >= 5 and not bad

        website_raw = row.get("website", "")
        # Basic URL format check
        website_ok = bool(re.match(r'^https?://[^\s]+$', website_raw)) or bool(re.match(r'^www\.[^\s]+$', website_raw))

        verified = "YES" if (email_ok and (phone_ok or address_ok)) else "NO"
        notes = f"email_test={result if email_ok else 'format_fail'}"

        validated[email] = {
            **row, "email": email,
            "email_valid": "YES" if email_ok else "NO",
            "phone_valid": "YES" if phone_ok else "NO",
            "address_valid": "YES" if address_ok else "NO",
            "website": website_raw,
            "verified": verified,
            "verified_date": today,
            "notes": notes
        }

        last_idx = i + 1
        validated_count += 1

        if validated_count >= max_per_run:
            break

    status["last_index"] = last_idx
    save_json(VALID_STATUS_FILE, status)
    save_validated(list(validated.values()))

    return validated, validated_count, auth_error


# ── HTML REPORT ─────────────────────────────────────────────────────────────

def build_html_report(new_rows, validated_records, validated_count, auth_error):
    total = len(validated_records)
    verified = sum(1 for v in validated_records if v.get("verified") == "YES")
    unverified = total - verified

    html = f"""<html><body>
    <h2 style="color:#1a73e8;">REO Client Acquisition Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>
    <p><b>New records found this run:</b> {len(new_rows)} &nbsp;|&nbsp;
       <b>Total validated:</b> {verified}/{total} &nbsp;|&nbsp;
       <b>Unverified:</b> {unverified}</p>
    """

    if new_rows:
        html += """
    <h3 style="color:#0f9d58;">New Records (just added)</h3>
    <table style="border-collapse:collapse;width:100%;font-size:12px;">
    <thead><tr style="background:#0f9d58;color:#fff;">
        <th style="padding:8px;border:1px solid #ddd;">Name</th>
        <th style="padding:8px;border:1px solid #ddd;">Category</th>
        <th style="padding:8px;border:1px solid #ddd;">Email</th>
        <th style="padding:8px;border:1px solid #ddd;">Website</th>
        <th style="padding:8px;border:1px solid #ddd;">Phone</th>
        <th style="padding:8px;border:1px solid #ddd;">Address</th>
        <th style="padding:8px;border:1px solid #ddd;">City</th>
        <th style="padding:8px;border:1px solid #ddd;">State</th>
        <th style="padding:8px;border:1px solid #ddd;">ZIP</th>
    </tr></thead><tbody>"""
        for r in new_rows:
            html += f"""<tr style="background:#e6fffa;">
                <td style="padding:6px;border:1px solid #ddd;">{r['name']}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r['category']}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r['email']}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r.get('website','')}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r['phone']}</td>
                <td style="padding:6px;border:1px solid #ddd;">{str(r['address'])[:50]}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r['city']}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r['state']}</td>
                <td style="padding:6px;border:1px solid #ddd;">{r['zip']}</td>
            </tr>"""
        html += "</tbody></table>"

    if validated_records:
        html += """
    <h3 style="color:#1a73e8;">Full Validation Status</h3>
    <table style="border-collapse:collapse;width:100%;font-size:11px;">
    <thead><tr style="background:#1a73e8;color:#fff;">
        <th style="padding:7px;border:1px solid #ddd;">Name</th>
        <th style="padding:7px;border:1px solid #ddd;">Category</th>
        <th style="padding:7px;border:1px solid #ddd;">Email</th>
        <th style="padding:7px;border:1px solid #ddd;">Website</th>
        <th style="padding:7px;border:1px solid #ddd;">Phone</th>
        <th style="padding:7px;border:1px solid #ddd;">Email OK</th>
        <th style="padding:7px;border:1px solid #ddd;">Phone OK</th>
        <th style="padding:7px;border:1px solid #ddd;">Address OK</th>
        <th style="padding:7px;border:1px solid #ddd;">Verified</th>
        <th style="padding:7px;border:1px solid #ddd;">Notes</th>
    </tr></thead><tbody>"""
        for v in validated_records:
            bg = "#ccffcc" if v.get("verified") == "YES" else "#ffcccc"
            html += f"""<tr style="background:{bg};">
                <td style="padding:5px;border:1px solid #ddd;">{v.get('name','')[:30]}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('category','')}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('email','')}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('website','')}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('phone','')}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('email_valid','')}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('phone_valid','')}</td>
                <td style="padding:5px;border:1px solid #ddd;">{v.get('address_valid','')}</td>
                <td style="padding:5px;border:1px solid #ddd;font-weight:bold;">{v.get('verified','')}</td>
                <td style="padding:5px;border:1px solid #ddd;font-size:10px;">{v.get('notes','')}</td>
            </tr>"""
        html += "</tbody></table>"

    if auth_error:
        html += "<p style='color:red;font-weight:bold;'>⚠ SMTP auth error — validation paused</p>"

    html += f"""<p style="font-size:10px;color:#999;margin-top:15px;">
    Validated CSV: {VALIDATED_CSV} | Services CSV: {CSV_FILE}<br/>
    {validated_count} records validated this run. Next run continues from index.<br/>
    Attachments: reo_services.csv (new records) | reo_validated.csv (validated records)
    </p></body></html>"""
    return html


def send_email_with_attachments(html_content, new_rows):
    """Send HTML email with CSV attachments using MIMEMultipart."""
    try:
        recipients = REPORT_TO if isinstance(REPORT_TO, list) else [REPORT_TO]

        msg = MIMEMultipart()
        msg['From'] = SENDER
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = "REO Service Provider Report"

        # Attach HTML body
        msg.attach(MIMEText(html_content, 'html'))

        # Attach services.csv (new records)
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename='reo_services.csv')
                msg.attach(part)

        # Attach validated.csv
        if os.path.exists(VALIDATED_CSV):
            with open(VALIDATED_CSV, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename='reo_validated.csv')
                msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER, SMTP_PASS)
            server.sendmail(SENDER, recipients, msg.as_string())
        print("[EMAIL SENT with attachments]")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


# ── MAIN ─────────────────────────────────────────────────────────────────────

def run(skip_email=False, email_only=False):
    # Email-only mode: skip search/validation, just send latest report
    if email_only:
        validated_all, _, _ = validate_all_records(max_per_run=0)  # no new validations
        html = build_html_report([], list(validated_all.values()), 0, None)
        sent = send_email_with_attachments(html, [])
        print(f"[DONE] email_sent={sent}")
        return

    # 1. Search for new records
    state = get_next_state()
    category = get_next_category()
    city = get_next_city(state)
    print(f"[SEARCH] state={state} city={city} category={category}")

    query = (
        f"{category} services in {city}, {state} business name phone email address"
    )

    result = subprocess.run(
        ["mmx", "search", "query", "--q", query, "--output", "json"],
        capture_output=True, text=True, timeout=60
    )
    output = result.stdout + result.stderr
    print(f"[SEARCH OUTPUT] {len(output)} chars")

    new_rows = parse_output(output, state, city, category)
    print(f"[NEW RECORDS] {len(new_rows)}")

    if new_rows:
        append_to_csv(new_rows, CSV_FILE)
        add_seen_emails([r["email"] for r in new_rows])

    # CRM lead creation removed — only validated records should be pushed

    # 2. Validate unvalidated records (5 per run)
    validated_all, validated_count, auth_error = validate_all_records(max_per_run=5)

    # 3. Build and send combined HTML report with CSV attachments
    html = build_html_report(new_rows, list(validated_all.values()), validated_count, auth_error)
    sent = send_email_with_attachments(html, new_rows)

    # 4. Log
    log = load_json(LOG_FILE, [])
    log.insert(0, {
        "datetime": datetime.now().isoformat(),
        "state": state, "city": city, "category": category,
        "new_records": len(new_rows),
        "crm_leads_created": 0,
        "validated_count": validated_count,
        "total_validated": len(validated_all),
        "email_sent": sent
    })
    log[:100]
    save_json(LOG_FILE, log)

    print(f"[DONE] new={len(new_rows)} validated={validated_count} total={len(validated_all)} email_sent={sent}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="all", choices=["all", "email-only"])
    args = parser.parse_args()
    run(email_only=(args.mode == "email-only"))