#!/usr/bin/env python3
import json, re, subprocess, smtplib, ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TODAY = date.today().isoformat()
BASE = "/home/mhcybroot/jobs/property-preservation-clients/data"
STATE_FILE = f"{BASE}/reo_search_state.json"
SEEN_FILE = f"{BASE}/reo_seen_emails.json"
MD_FILE = f"{BASE}/reo_services.md"

STATES = ["Alabama/Birmingham","Alaska/Anchorage","Arizona/Phoenix","Arkansas/Little Rock","California/Sacramento","Colorado/Denver","Connecticut/Hartford","Delaware/Wilmington","Florida/Jacksonville","Georgia/Atlanta","Hawaii/Honolulu","Idaho/Boise","Illinois/Springfield","Indiana/Indianapolis","Iowa/Des Moines","Kansas/Topeka","Kentucky/Louisville","Louisiana/Baton Rouge","Maine/Augusta","Maryland/Baltimore","Massachusetts/Boston","Michigan/Lansing","Minnesota/St. Paul","Mississippi/Jackson","Missouri/Jefferson City","Montana/Helena","Nebraska/Lincoln","Nevada/Las Vegas","New Hampshire/Concord","New Jersey/Trenton","New Mexico/Santa Fe","New York/Albany","North Carolina/Raleigh","North Dakota/Bismarck","Ohio/Columbus","Oklahoma/Oklahoma City","Oregon/Salem","Pennsylvania/Harrisburg","Rhode Island/Providence","South Carolina/Columbia","South Dakota/Pierre","Tennessee/Nashville","Texas/Austin","Utah/Salt Lake City","Vermont/Montpelier","Virginia/Richmond","Washington/Olympia","West Virginia/Charleston","Wisconsin/Madison","Wyoming/Cheyenne"]

CATS = ["Real Estate Agent","Property Manager","Auction Services","Cash Offer Home Buyer","Short Sale Services","Foreclosure Attorney","Title Company","Home Inspector","Mortgage Broker","Hard Money Lender"]

BAD_DOMAINS = {"gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com","facebook.com","linkedin.com","twitter.com","instagram.com","pinterest.com","zillow.com","realtor.com","redfin.com","gov","mil"}

def is_junk_email(email, business_name=""):
    if not email or "@" not in email:
        return True
    d = email.lower().split("@")[1].rstrip(".,; ")
    if d in BAD_DOMAINS or any(d.endswith("."+b) for b in BAD_DOMAINS):
        if d in ("gmail.com","yahoo.com","hotmail.com","outlook.com","aol.com"):
            words = business_name.split()
            if len(words) >= 2:
                return False
        return True
    if d.endswith(".edu") or any(k in d for k in ["lead","finder","list","data"]):
        return True
    return False

# Load seen emails
with open(SEEN_FILE) as f:
    seen = json.load(f)
seen_set = set(seen)

# New records to add
new_records = [
    {"name": "House To Home Inspections", "email": "htohinspections@gmail.com", "phone": "207-577-0395", "address": "", "city": "Lisbon", "county": "Androscoggin", "state": "ME", "zip": "04250", "category": "Home Inspector"},
    {"name": "AnnRuel Home Inspections", "email": "Jamesruelmac@gmail.com", "phone": "(207) 861-1227", "address": "", "city": "Augusta", "county": "Kennebec", "state": "ME", "zip": "04330", "category": "Home Inspector"},
    {"name": "Advanced Inspections Inc.", "email": "Mike@advancedinspectionsinc.com", "phone": "207-248-2690", "address": "126 Western Avenue PMB 135", "city": "Augusta", "county": "Kennebec", "state": "ME", "zip": "04330", "category": "Home Inspector"},
    {"name": "Spotlight Home Inspection LLC", "email": "", "phone": "(207) 441-4182", "address": "103 High Holborn St", "city": "Gardiner", "county": "Kennebec", "state": "ME", "zip": "04345", "category": "Home Inspector"},
    {"name": "Campbell Property Inspections", "email": "", "phone": "(207) 441-9802", "address": "", "city": "Pittston", "county": "Kennebec", "state": "ME", "zip": "04345", "category": "Home Inspector"},
]

# Filter out already-seen and junk, deduplicate
added = []
for r in new_records:
    email = r["email"].lower().strip() if r["email"] else ""
    if email and (email in seen_set or is_junk_email(email, r["name"])):
        continue
    if email and email not in seen_set:
        seen.append(email)
        seen_set.add(email)
    added.append(r)

# Append to markdown
if added:
    with open(MD_FILE) as f:
        content = f.read()
    if not content.endswith("\n"):
        content += "\n"
    for r in added:
        line = f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {TODAY} |"
        content += line + "\n"
    with open(MD_FILE, "w") as f:
        f.write(content)

    # Save seen emails
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f)

    # Send email
    state_idx = 18
    state_name = "Maine"
    city = "Augusta"
    body = "New REO Leads: Augusta, Maine\n\n"
    body += "| name | email | phone | address | city | county | state | zip | category | found_date |\n"
    body += "|------|-------|-------|---------|------|-------|------|-----|----------|\n"
    for r in added:
        body += f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {TODAY} |\n"

    msg = MIMEMultipart()
    msg["From"] = "data@skylink-ltd.com"
    msg["To"] = "data@skylink-ltd.com"
    msg["Subject"] = f"New REO Leads: {city}, {state_name}"
    msg.attach(MIMEText(body, "plain"))

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with smtplib.SMTP_SSL("162.0.235.129", 465, context=ctx, timeout=30) as s:
        s.login("data@skylink-ltd.com", "Skylink#2026")
        s.send_message(msg)
    print(f"Done. Added {len(added)} records. Email sent.")
else:
    print("No new records to add.")