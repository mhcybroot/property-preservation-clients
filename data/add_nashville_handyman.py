import json
import smtplib
import ssl
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

today = date.today().isoformat()

# New records found
new_records = [
    {
        "name": "ER Handyman Services",
        "email": "john@erhandymanservices.net",
        "phone": "(615) 709-6010",
        "address": "4117 Hillsboro Pike, Suite 103-300",
        "city": "Nashville",
        "county": "Davidson",
        "state": "TN",
        "zip": "37215",
        "category": "Handyman",
        "found_date": today,
    },
    {
        "name": "The Nashville Handyman",
        "email": "info@thenashvillehandyman.com",
        "phone": "(615) 243-7426",
        "address": "1921 19th Ave S",
        "city": "Nashville",
        "county": "Davidson",
        "state": "TN",
        "zip": "37212",
        "category": "Handyman",
        "found_date": today,
    },
]

# Load seen emails
with open("data/seen_emails.json") as f:
    seen = json.load(f)
seen_set = set(seen)

# Append new records
lines = []
for r in new_records:
    line = f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |"
    lines.append(line)
    seen.append(r["email"])

with open("data/services.md", "a") as f:
    for line in lines:
        f.write(line + "\n")

# Save updated seen emails
with open("data/seen_emails.json", "w") as f:
    json.dump(seen, f)

# Advance state
with open("data/search_state.json") as f:
    state = json.load(f)

# Tennessee (idx 41) + Handyman (idx 4) -> advance to next
# Tennessee cat_idx 4, next is Moving Service (idx 9), then state 42 Texas
state["cat_idx"] = (state["cat_idx"] + 1) % 10  # 5 -> next slot within Tennessee
# Actually advance properly: if cat_idx was 4 (Handyman), next is 5 (Landscaping), but we want to move to next state's first category
# The pre-run ran the Alabama/Huntsville Handyman (pre-run state=Alabama city=Huntsville category=Handyman)
# Our rotation state was Tennessee/Nashville Handyman (state_idx=41, cat_idx=4)
# Since pre-run handled state_idx=0 (Alabama), we should advance our state to match
# Advance: state_idx=41, cat_idx=4 -> increment to next slot
# After Handyman (idx 4), next cat is Landscaping (idx 5) within same state
# But the pre-run ran Alabama Handyman, so our rotation is behind
# We need to advance past the Handyman slot for our current state
state["state_idx"] = (state["state_idx"] + 1) % 50  # 41 -> 42 (Texas)
state["cat_idx"] = 0  # Reset to Plumber for Texas

with open("data/search_state.json", "w") as f:
    json.dump(state, f)

print(f"State advanced: state_idx={state['state_idx']}, cat_idx={state['cat_idx']}")
print(f"New records added: {len(new_records)}")

# Send email
msg = MIMEMultipart()
msg["From"] = "data@skylink-ltd.com"
msg["To"] = "data@skylink-ltd.com"
msg["Subject"] = "New Leads: Nashville, Tennessee"

body = "New handyman leads found:\n\n"
for r in new_records:
    body += f"| {r['name']} | {r['email']} | {r['phone']} | {r['address']} | {r['city']} | {r['county']} | {r['state']} | {r['zip']} | {r['category']} | {r['found_date']} |\n"

msg.attach(MIMEText(body, "plain"))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL("162.0.235.129", 465, context=ctx, timeout=30) as s:
    s.login("data@skylink-ltd.com", "Skylink#2026")
    s.send_message(msg)

print("Email sent successfully")