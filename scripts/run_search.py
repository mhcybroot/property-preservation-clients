#!/usr/bin/env python3
"""Run one iteration of the property preservation client search."""
import subprocess, re, os, json, csv, ssl, smtplib
from datetime import datetime

DATA_DIR = "/home/mhcybroot/jobs/property-preservation-clients/data"
CSV_FILE = f"{DATA_DIR}/services.csv"
VALIDATED_CSV = f"{DATA_DIR}/validated.csv"
STATE_FILE = f"{DATA_DIR}/last_state.json"
CAT_FILE = f"{DATA_DIR}/last_category.json"
CITY_FILE = f"{DATA_DIR}/last_city.json"
SEEN_FILE = f"{DATA_DIR}/seen_emails.json"
VALID_STATUS_FILE = f"{DATA_DIR}/validation_status.json"
LOG_FILE = f"{DATA_DIR}/combined_log.json"

SENDER = "data@skylink-ltd.com"
REPORT_TO = ["data@skylink-ltd.com"]
SMTP_PASS = "Skylink#2026"
SMTP_HOST = "skylink-ltd.com"
SMTP_PORT = 465

STATES_CITIES = {
    "Alabama": ["Birmingham","Mobile","Huntsville"],
    "Alaska": ["Anchorage","Fairbanks","Juneau"],
    "Arizona": ["Phoenix","Tucson","Scottsdale"],
    "Arkansas": ["Little Rock","Fort Smith","Fayetteville"],
    "California": ["Los Angeles","San Diego","San Francisco"],
    "Colorado": ["Denver","Colorado Springs","Boulder"],
    "Connecticut": ["Hartford","New Haven","Stamford"],
    "Delaware": ["Wilmington","Dover","Newark"],
    "Florida": ["Miami","Orlando","Tampa"],
    "Georgia": ["Atlanta","Savannah","Augusta"],
    "Hawaii": ["Honolulu","Hilo","Kailua"],
    "Idaho": ["Boise","Nampa","Idaho Falls"],
    "Illinois": ["Chicago","Springfield","Peoria"],
    "Indiana": ["Indianapolis","Fort Wayne","Evansville"],
    "Iowa": ["Des Moines","Cedar Rapids","Davenport"],
    "Kansas": ["Wichita","Kansas City","Topeka"],
    "Kentucky": ["Louisville","Lexington","Bowling Green"],
    "Louisiana": ["New Orleans","Baton Rouge","Shreveport"],
    "Maine": ["Portland","Lewiston","Bangor"],
    "Maryland": ["Baltimore","Frederick","Rockville"],
    "Massachusetts": ["Boston","Worcester","Springfield"],
    "Michigan": ["Detroit","Grand Rapids","Ann Arbor"],
    "Minnesota": ["Minneapolis","Saint Paul","Rochester"],
    "Mississippi": ["Jackson","Gulfport","Biloxi"],
    "Missouri": ["Kansas City","St. Louis","Springfield"],
    "Montana": ["Billings","Missoula","Great Falls"],
    "Nebraska": ["Omaha","Lincoln","Bellevue"],
    "Nevada": ["Las Vegas","Reno","Henderson"],
    "New Hampshire": ["Manchester","Nashua","Concord"],
    "New Jersey": ["Newark","Jersey City","Trenton"],
    "New Mexico": ["Albuquerque","Santa Fe","Las Cruces"],
    "New York": ["New York City","Buffalo","Rochester"],
    "North Carolina": ["Charlotte","Raleigh","Greensboro"],
    "North Dakota": ["Fargo","Bismarck","Grand Forks"],
    "Ohio": ["Columbus","Cleveland","Cincinnati"],
    "Oklahoma": ["Oklahoma City","Tulsa","Norman"],
    "Oregon": ["Portland","Eugene","Salem"],
    "Pennsylvania": ["Philadelphia","Pittsburgh","Harrisburg"],
    "Rhode Island": ["Providence","Warwick","Cranston"],
    "South Carolina": ["Charleston","Columbia","Greenville"],
    "South Dakota": ["Sioux Falls","Rapid City","Aberdeen"],
    "Tennessee": ["Nashville","Memphis","Knoxville"],
    "Texas": ["Houston","Dallas","Austin"],
    "Utah": ["Salt Lake City","Provo","Ogden"],
    "Vermont": ["Burlington","Rutland","Montpelier"],
    "Virginia": ["Virginia Beach","Richmond","Norfolk"],
    "Washington": ["Seattle","Spokane","Tacoma"],
    "West Virginia": ["Charleston","Huntington","Morgantown"],
    "Wisconsin": ["Milwaukee","Madison","Green Bay"],
    "Wyoming": ["Cheyenne","Casper","Laramie"],
}
STATES = list(STATES_CITIES.keys())
CATEGORIES = [
    "Handyman","General Contractor","HVAC Contractor","Appliance Technician",
    "Plumber","Electrician","Lawn Care Services","Landscaper","Roofer","Inspection Crew"
]
FIELDS = ["name","email","phone","address","city","county","state","zip",
          "category","found_date","email_valid","phone_valid","address_valid",
          "verified","verified_date","notes"]

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
        writer = csv.DictWriter(f, fieldnames=["name","email","phone","address","city","county","state","zip","category","found_date"])
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
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_records)

def parse_output(output, state, city, category):
    rows = []
    seen = load_seen_emails()
    today = datetime.now().strftime("%Y-%m-%d")
    email_pat = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    phone_pat = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    for entry in re.split(r'(?:^|\n)\s*(?:\d+\.|\*\*\d+\s)\s*', output):
        entry = entry.strip()
        if not entry:
            continue
        emails = email_pat.findall(entry)
        if not emails:
            continue
        for email in emails:
            email_lc = email.lower().strip()
            if email_lc in seen:
                continue
            name_m = re.search(r'\*\*([^*]+)\*\*', entry)
            if not name_m:
                name_m = re.search(r'^([A-Z][^$\n]{2,60})', entry)
            name = name_m.group(1).replace("**","").strip() if name_m else f"{category} - {city}"
            name = re.sub(r'^\*+|\*+$', '', name).strip()[:100]
            phones = phone_pat.findall(entry)
            phone = phones[0] if phones else ""
            addr_m = re.search(r'(?:Address[:]?\s*)(.+?)(?=\n\s*(?:Phone|Email|Website)|$)', entry, re.DOTALL|re.IGNORECASE)
            address = addr_m.group(1).strip() if addr_m else ""
            address = re.sub(r'\s+', ' ', address)[:200]
            city_m = re.search(r'([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*),\s*[A-Z]{2}', entry)
            city_found = city_m.group(1).strip() if city_m else city
            zip_m = re.search(r'\b(\d{5}(?:-\d{4})?)\b', entry)
            zipcode = zip_m.group(1) if zip_m else ""
            rows.append({
                "name": name, "email": email_lc, "phone": phone,
                "address": address, "city": city_found, "county": "",
                "state": state, "zip": zipcode, "category": category,
                "found_date": today
            })
            seen.add(email_lc)
    return rows

def validate_all_records(max_per_run=5):
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
        email = row.get("email","").strip().lower()
        if not email or email in validated:
            last_idx = i + 1
            continue
        print(f"[VALIDATE] {i}: {email}")
        email_ok = bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
        if email_ok:
            result = send_test_email(email, row.get("name",""), row.get("category",""))
            if result == "sent":
                email_ok = True
            elif "auth" in result:
                auth_error = True
                break
        phone_raw = row.get("phone","")
        digits = re.sub(r'\D', '', phone_raw)
        phone_ok = len(digits) >= 10
        addr_raw = row.get("address","")
        bad = any(b in addr_raw.lower() for b in ["not available","not listed","n/a","**","phone:","email:"])
        address_ok = len(addr_raw.strip()) >= 5 and not bad
        verified = "YES" if (email_ok and (phone_ok or address_ok)) else "NO"
        notes = f"email_test={result if email_ok else 'format_fail'}"
        validated[email] = {
            **row, "email": email,
            "email_valid": "YES" if email_ok else "NO",
            "phone_valid": "YES" if phone_ok else "NO",
            "address_valid": "YES" if address_ok else "NO",
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

def build_html_report(new_rows, validated_records, validated_count, auth_error):
    total = len(validated_records)
    verified = sum(1 for v in validated_records if v.get("verified") == "YES")
    unverified = total - verified
    html = f"""<html><body>
    <h2 style="color:#1a73e8;">Service Provider Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>
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
    {validated_count} records validated this run. Next run continues from index.
    </p></body></html>"""
    return html

def send_email(html_content):
    try:
        recipients = REPORT_TO if isinstance(REPORT_TO, list) else [REPORT_TO]
        msg = f"From: {SENDER}\nTo: {', '.join(recipients)}\nSubject: Service Provider Report\nContent-Type: text/html\n\n{html_content}"
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER, SMTP_PASS)
            server.sendmail(SENDER, recipients, msg.encode() if isinstance(msg, str) else msg)
        print("[EMAIL SENT]")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

# ── MAIN ─────────────────────────────────────────────────────────────────────
state = get_next_state()
category = get_next_category()
city = get_next_city(state)
print(f"[SEARCH] state={state} city={city} category={category}")

query = (
    f"Find local {category} services in {city}, {state}. "
    f"List business name, email address, phone number, street address, city, state, and ZIP for as many providers as possible. Format as a structured list with all contact details."
)

result = subprocess.run(
        ["opencode", "run", "--agent", "build", query],
        capture_output=True, text=True, timeout=180
    )
output = result.stdout + result.stderr
print(f"[SEARCH OUTPUT] {len(output)} chars")

new_rows = parse_output(output, state, city, category)
print(f"[NEW RECORDS] {len(new_rows)}")

if new_rows:
    append_to_csv(new_rows, CSV_FILE)
    add_seen_emails([r["email"] for r in new_rows])

validated_all, validated_count, auth_error = validate_all_records(max_per_run=5)

html = build_html_report(new_rows, list(validated_all.values()), validated_count, auth_error)
sent = send_email(html)

log = load_json(LOG_FILE, [])
log.insert(0, {
    "datetime": datetime.now().isoformat(),
    "state": state, "city": city, "category": category,
    "new_records": len(new_rows),
    "validated_count": validated_count,
    "total_validated": len(validated_all),
    "email_sent": sent
})
log[:100]
save_json(LOG_FILE, log)

print(f"[DONE] new={len(new_rows)} validated={validated_count} total={len(validated_all)} email_sent={sent}")