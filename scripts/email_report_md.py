#!/usr/bin/env python3
"""
Email report generator for property preservation leads.
Reads from .md files, sends formatted HTML email.
"""
import json, os, re, ssl, smtplib
from datetime import datetime

DATA = "/home/mhcybroot/jobs/property-preservation-clients/data"
SERVICES_MD = f"{DATA}/services.md"
REO_MD = f"{DATA}/reo_services.md"
VALIDATED_MD = f"{DATA}/validated.md"

SENDER = "data@skylink-ltd.com"
REPORT_TO = ["data@skylink-ltd.com"]
SMTP_PASS = "Skylink#2026"
SMTP_HOST = "skylink-ltd.com"
SMTP_PORT = 465

def read_md_table(path):
    """Parse a markdown table into list of dicts. Handles missing/empty cells."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        lines = f.readlines()
    header = []
    for i, line in enumerate(lines):
        line = line.rstrip()
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')]
        # Remove leading/trailing empty cells (markdown table leading/trailing |)
        while cells and cells[0] == '':
            cells.pop(0)
        while cells and cells[-1] == '':
            cells.pop()
        if not cells:
            continue
        # Skip separator rows
        if all(re.match(r'^[-_ ]+$', c) for c in cells):
            continue
        if i == 0:
            header = cells
            print(f"  [{path}] header: {len(header)} cols")
        else:
            # Pad or trim to match header length
            while len(cells) < len(header):
                cells.append('')
            if len(cells) > len(header):
                cells = cells[:len(header)]
            rows.append(dict(zip(header, cells)))
    return rows

def is_business_email(email):
    bad = {'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com',
           'instagram.com','facebook.com','linkedin.com','twitter.com',
           'pinterest.com','zillow.com','realtor.com','redfin.com','gov','mil'}
    if not email or '@' not in email:
        return False
    d = email.lower().split('@')[1]
    if d in bad or any(d.endswith('.'+b) for b in bad):
        return False
    if any(x in d for x in ['lead','finder','list','data','procurement']):
        return False
    return True

def build_html(all_services, all_reo, validated):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    biz_count = sum(1 for r in all_services if is_business_email(r.get('email','')))
    reo_count = sum(1 for r in all_reo if r.get('email',''))
    reo_biz = sum(1 for r in all_reo if is_business_email(r.get('email','')))

    html = f"""<html><body>
<h2 style="color:#1a73e8;">Property Preservation Service Providers — {now}</h2>
<p>
<b>General Pipeline:</b> {len(all_services)} records, {biz_count} with business emails<br/>
<b>REO Pipeline:</b> {len(all_reo)} records, {reo_biz} with business emails<br/>
<b>Validated & Ready for CRM:</b> {len(validated)} records
</p>
"""

    if all_services:
        html += """<h3 style="color:#0f9d58;">General Services Pipeline</h3>
<table style="border-collapse:collapse;width:100%;font-size:12px;">
<thead><tr style="background:#0f9d58;color:#fff;">
<th style="padding:8px;border:1px solid #ddd;">Name</th>
<th style="padding:8px;border:1px solid #ddd;">Email</th>
<th style="padding:8px;border:1px solid #ddd;">Phone</th>
<th style="padding:8px;border:1px solid #ddd;">City</th>
<th style="padding:8px;border:1px solid #ddd;">State</th>
<th style="padding:8px;border:1px solid #ddd;">Category</th>
<th style="padding:8px;border:1px solid #ddd;">Date</th>
</tr></thead><tbody>"""
        for r in all_services:
            email = r.get('email','')
            biz = "background:#e6fffa;" if is_business_email(email) else "background:#fff;"
            html += f"""<tr style="{biz}">
<td style="padding:6px;border:1px solid #ddd;">{r.get('name','')}</td>
<td style="padding:6px;border:1px solid #ddd;{'font-weight:bold;color:#1a73e8;' if is_business_email(email) else 'color:#999;'}" nowrap>{email}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('phone','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('city','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('state','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('category','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('found_date','')}</td>
</tr>"""
        html += "</tbody></table>"

    if all_reo:
        html += """<h3 style="color:#9334e6;">REO Pipeline</h3>
<table style="border-collapse:collapse;width:100%;font-size:12px;">
<thead><tr style="background:#9334e6;color:#fff;">
<th style="padding:8px;border:1px solid #ddd;">Name</th>
<th style="padding:8px;border:1px solid #ddd;">Email</th>
<th style="padding:8px;border:1px solid #ddd;">Phone</th>
<th style="padding:8px;border:1px solid #ddd;">City</th>
<th style="padding:8px;border:1px solid #ddd;">State</th>
<th style="padding:8px;border:1px solid #ddd;">Category</th>
</tr></thead><tbody>"""
        for r in all_reo:
            email = r.get('email','')
            biz = "background:#f3e8ff;" if is_business_email(email) else "background:#fff;"
            html += f"""<tr style="{biz}">
<td style="padding:6px;border:1px solid #ddd;">{r.get('name','')}</td>
<td style="padding:6px;border:1px solid #ddd;{'font-weight:bold;color:#9334e6;' if is_business_email(email) else 'color:#999;'}" nowrap>{email}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('phone','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('city','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('state','')}</td>
<td style="padding:6px;border:1px solid #ddd;">{r.get('category','')}</td>
</tr>"""
        html += "</tbody></table>"

    html += f"""<p style="font-size:10px;color:#999;margin-top:15px;">
Data source: {SERVICES_MD} | {REO_MD}<br/>
Generated: {now}
</p></body></html>"""
    return html

def send_email(html_content):
    try:
        recipients = REPORT_TO if isinstance(REPORT_TO, list) else [REPORT_TO]
        msg = f"From: {SENDER}\nTo: {', '.join(recipients)}\nSubject: Property Preservation Service Providers Report\nContent-Type: text/html\n\n{html_content}"
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SENDER, SMTP_PASS)
            server.sendmail(SENDER, recipients, msg.encode() if isinstance(msg, str) else msg)
        print("[EMAIL SENT]")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False

if __name__ == "__main__":
    all_services = read_md_table(SERVICES_MD)
    all_reo = read_md_table(REO_MD)
    validated = read_md_table(VALIDATED_MD)

    print(f"services.md: {len(all_services)} records")
    print(f"reo_services.md: {len(all_reo)} records")
    print(f"validated.md: {len(validated)} records")

    biz_services = [r for r in all_services if is_business_email(r.get('email',''))]
    biz_reo = [r for r in all_reo if is_business_email(r.get('email',''))]
    print(f"business emails — general: {len(biz_services)}, reo: {len(biz_reo)}")

    html = build_html(all_services, all_reo, validated)
    sent = send_email(html)
    print(f"[DONE] email_sent={sent}")