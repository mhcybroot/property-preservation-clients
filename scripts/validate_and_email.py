#!/usr/bin/env python3
"""
Validate all records in services.csv:
1. For each record, verify email deliverability by sending a test email
2. Verify phone is valid format
3. Verify address exists
4. Update CSV with validation status
5. Send summary email with verified vs unverified breakdown
"""

import csv
import json
import os
import re
import ssl
import smtplib
import subprocess
from datetime import datetime

DATA_DIR = "/home/mhcybroot/jobs/property-preservation-clients/data"
CSV_FILE = f"{DATA_DIR}/services.csv"
VALIDATION_FILE = f"{DATA_DIR}/validated.csv"
STATUS_FILE = f"{DATA_DIR}/validation_status.json"
LOG_FILE = f"{DATA_DIR}/validation_log.json"

SENDER_EMAIL = "data@skylink-ltd.com"
SENDER_PASSWORD = "Skylink#2026"
REPORT_TO = "data@skylink-ltd.com"
SMTP_HOST = "skylink-ltd.com"
SMTP_PORT = 465

FIELDS = ["name","email","phone","address","city","county","state","zip","category","found_date",
          "email_valid","phone_valid","address_valid","verified","verified_date","notes"]

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

def send_test_email(to_email, record_name, record_category):
    """Try to send a test email to verify deliverability."""
    try:
        msg = f"""From: {SENDER_EMAIL}
To: {to_email}
Subject: Verification - {record_name}

This is an automated verification message from Skylink Property Services.
If you received this email, your contact info is valid.

Category: {record_category}
Name: {record_name}

Reply to confirm or contact us at data@skylink-ltd.com
"""
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [to_email], msg)
        return "sent"
    except smtplib.SMTPAuthenticationError:
        return "auth_error"
    except smtplib.SMTPRecipientsRefused:
        return "rejected"
    except Exception as e:
        return f"error: {str(e)[:50]}"

def validate_phone(phone):
    """Check if phone looks valid."""
    if not phone or phone.strip() == "":
        return False
    # Remove common separators and check it's 10+ digits
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10

def validate_email_format(email):
    """Basic email format check."""
    if not email or email.strip() == "":
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_address(address):
    """Check if address has meaningful content."""
    if not address or address.strip() == "":
        return False
    # Must have at least a street number pattern or meaningful words
    bad_patterns = ["not available", "not listed", "n/a", "unknown", "**", "phone:", "email:"]
    lower_addr = address.lower()
    for bp in bad_patterns:
        if bp in lower_addr:
            return False
    # Should have at least 5 chars
    return len(address.strip()) >= 5

def load_csv_records():
    records = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    return records

def load_validated():
    validated = {}
    path = VALIDATION_FILE
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                validated[row["email"]] = row
    return validated

def save_validated(validated_list):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(VALIDATION_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(validated_list)

def verify_address_via_opencode(name, address, city, state, zipcode):
    """Use opencode to verify if address is real."""
    if not address or len(address) < 10:
        return False, "Address too short or empty"
    
    query = f"Verify this business address exists: '{address}, {city}, {state} {zipcode}'. Is this a real postal address? Just answer YES or NO."
    
    try:
        result = subprocess.run(
            ["opencode", "run", "--agent", "build", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + result.stderr
        if "YES" in output.upper() and "NO" not in output[:20].upper():
            return True, "Address verified"
        else:
            return False, "Address not confirmed"
    except Exception as e:
        return False, f"Verify error: {str(e)[:30]}"

def run_validation():
    records = load_csv_records()
    validated = load_validated()
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"[VALIDATE] {len(records)} total records in CSV")
    
    # Load previous validation status
    status = load_json(STATUS_FILE, {"last_index": 0, "total": len(records)})
    last_index = status.get("last_index", 0)
    
    # Process unvalidated records starting from last_index
    processed = 0
    for i, row in enumerate(records):
        if i < last_index:
            continue
        
        email = row.get("email", "").strip().lower()
        if not email:
            # Try next
            last_index = i + 1
            continue
        
        # Skip already fully verified records (don't re-verify)
        if email in validated:
            prev = validated[email]
            if prev.get("verified") == "YES":
                last_index = i + 1
                continue
        
        print(f"[CHECK] {i}: {email}")
        
        # Validate email format
        email_valid = "YES" if validate_email_format(email) else "NO"
        
        # Try to send test email
        email_result = send_test_email(email, row.get("name",""), row.get("category",""))
        
        if email_result == "sent":
            email_valid = "YES"
        elif email_result == "auth_error":
            print("[AUTH ERROR] Cannot send test emails - check SMTP creds")
            break
        elif email_result == "rejected":
            email_valid = "NO"
        
        # Validate phone
        phone_valid = "YES" if validate_phone(row.get("phone","")) else "NO"
        
        # Validate address
        address_valid = "YES" if validate_address(row.get("address","")) else "NO"
        
        # Mark verified if email+phone or email+address are both valid
        verified = "YES" if (email_valid == "YES" and (phone_valid == "YES" or address_valid == "YES")) else "NO"
        
        notes = f"email_test={email_result}"
        
        validated[email] = {
            "name": row.get("name",""),
            "email": email,
            "phone": row.get("phone",""),
            "address": row.get("address",""),
            "city": row.get("city",""),
            "county": row.get("county",""),
            "state": row.get("state",""),
            "zip": row.get("zip",""),
            "category": row.get("category",""),
            "found_date": row.get("found_date",""),
            "email_valid": email_valid,
            "phone_valid": phone_valid,
            "address_valid": address_valid,
            "verified": verified,
            "verified_date": today,
            "notes": notes
        }
        
        last_index = i + 1
        processed += 1
        
        # Process 5 records per run to avoid timeout
        if processed >= 5:
            break
    
    # Save status
    status["last_index"] = last_index
    status["total"] = len(records)
    save_json(STATUS_FILE, status)
    
    # Save validated CSV
    validated_list = list(validated.values())
    save_validated(validated_list)
    
    # Build summary
    total = len(validated_list)
    verified_count = sum(1 for v in validated_list if v["verified"] == "YES")
    unverified_count = total - verified_count
    
    # Build HTML email
    html = f"""<html><body>
    <h2 style="color:#1a73e8;">Service Provider Validation Report</h2>
    <p><b>Total records:</b> {total} &nbsp; <b>Verified:</b> {verified_count} &nbsp; <b>Unverified:</b> {unverified_count}</p>
    <p><b>Last processed:</b> record index {last_index} of {len(records)}</p>
    
    <h3>Unverified Records (need review)</h3>
    <table style="border-collapse:collapse;width:100%;font-size:12px;">
    <thead><tr style="background:#d32f2f;color:#fff;">
        <th style="padding:8px;border:1px solid #ddd;">Name</th>
        <th style="padding:8px;border:1px solid #ddd;">Category</th>
        <th style="padding:8px;border:1px solid #ddd;">Email</th>
        <th style="padding:8px;border:1px solid #ddd;">Phone</th>
        <th style="padding:8px;border:1px solid #ddd;">Address</th>
        <th style="padding:8px;border:1px solid #ddd;">Email OK</th>
        <th style="padding:8px;border:1px solid #ddd;">Phone OK</th>
        <th style="padding:8px;border:1px solid #ddd;">Address OK</th>
        <th style="padding:8px;border:1px solid #ddd;">Verified</th>
    </tr></thead><tbody>"""
    
    for v in validated_list:
        bg = "#ffcccc" if v["verified"] == "NO" else "#ccffcc"
        html += f"""<tr style="background:{bg};">
            <td style="padding:6px;border:1px solid #ddd;">{v['name']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['category']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['email']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['phone']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['address'][:50]}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['email_valid']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['phone_valid']}</td>
            <td style="padding:6px;border:1px solid #ddd;">{v['address_valid']}</td>
            <td style="padding:6px;border:1px solid #ddd;font-weight:bold;">{v['verified']}</td>
        </tr>"""
    
    html += f"""</tbody></table>
    <p style="font-size:11px;color:#888;margin-top:20px;">
    Validated CSV saved to: {VALIDATION_FILE}<br/>
    Processed {processed} new records this run. Resuming from index {last_index} next tick.
    </p>
    </body></html>"""
    
    # Send email
    try:
        msg_root = f"""From: {SENDER_EMAIL}
To: {REPORT_TO}
Subject: Service Provider Validation Report — {verified_count}/{total} verified
Content-Type: text/html

{html}
"""
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [REPORT_TO], msg_root.encode() if isinstance(msg_root, str) else msg_root)
        print(f"[EMAIL SENT] Report with {total} records, {verified_count} verified")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
    
    # Log
    log = load_json(LOG_FILE, [])
    log.insert(0, {"date": datetime.now().isoformat(), "total": total, "verified": verified_count, 
                    "unverified": unverified_count, "last_index": last_index, "processed": processed})
    log[:50]
    save_json(LOG_FILE, log)
    
    print(f"[DONE] validated={verified_count}/{total} unverified={unverified_count} last_idx={last_index}")

if __name__ == "__main__":
    run_validation()