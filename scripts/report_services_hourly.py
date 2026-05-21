#!/usr/bin/env python3
"""
Hourly services.md report — reads, verifies, calculates, sends HTML email.
"""
import json, os, re, ssl, smtplib, sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DATA      = "/home/mhcybroot/jobs/property-preservation-clients/data"
SERVICES_MD = f"{DATA}/services.md"
LOG_FILE   = "/home/mhcybroot/jobs/property-preservation-clients/data/.report_services.log"

SENDER    = "data@skylink-ltd.com"
RECIPIENT = "data@skylink-ltd.com"
SMTP_PASS = "Skylink#2026"
SMTP_HOST = "162.0.235.129"
SMTP_PORT = 465

BAD_DOMAINS = {
    'gmail.com','yahoo.com','hotmail.com','outlook.com','aol.com',
    'instagram.com','facebook.com','linkedin.com','twitter.com',
    'pinterest.com','zillow.com','realtor.com','redfin.com','gov','mil'
}

def is_business_email(email):
    if not email or '@' not in email:
        return False
    d = email.lower().split('@')[1]
    if d in BAD_DOMAINS or any(d.endswith('.'+b) for b in BAD_DOMAINS):
        return False
    if any(x in d for x in ['lead','finder','list','data','procurement']):
        return False
    return True

def read_md_table(path):
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
        while cells and cells[0] == '': cells.pop(0)
        while cells and cells[-1] == '': cells.pop()
        if not cells: continue
        if all(re.match(r'^[-_ ]+$', c) for c in cells): continue
        if i == 0:
            header = cells
        else:
            while len(cells) < len(header): cells.append('')
            if len(cells) > len(header): cells = cells[:len(header)]
            rows.append(dict(zip(header, cells)))
    return rows

def calculate_stats(rows):
    total = len(rows)
    with_email = sum(1 for r in rows if r.get('email','').strip())
    biz_email  = sum(1 for r in rows if is_business_email(r.get('email','')))
    with_phone = sum(1 for r in rows if r.get('phone','').strip())
    states = {}
    categories = {}
    for r in rows:
        st = r.get('state','').strip()
        cat = r.get('category','').strip()
        if st:  states[st]   = states.get(st,0)   + 1
        if cat: categories[cat] = categories.get(cat,0) + 1
    return {
        'total': total,
        'with_email': with_email,
        'biz_email': biz_email,
        'with_phone': with_phone,
        'states': states,
        'categories': categories,
    }

def build_html(rows, stats, report_type="General Services"):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    s = stats

    # Top stats cards
    cards = f"""
    <div style="display:flex;gap:16px;margin-bottom:20px;">
      <div style="flex:1;background:#e8f0fe;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:28px;font-weight:bold;color:#1a73e8;">{s['total']}</div>
        <div style="font-size:12px;color:#555;">Total Records</div>
      </div>
      <div style="flex:1;background:#e6f4ea;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:28px;font-weight:bold;color:#0f9d58;">{s['biz_email']}</div>
        <div style="font-size:12px;color:#555;">Business Emails</div>
      </div>
      <div style="flex:1;background:#fef7e0;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:28px;font-weight:bold;color:#f9ab00;">{s['with_phone']}</div>
        <div style="font-size:12px;color:#555;">With Phone</div>
      </div>
      <div style="flex:1;background:#f3e8ff;border-radius:8px;padding:14px;text-align:center;">
        <div style="font-size:28px;font-weight:bold;color:#9334e6;">{s['with_email']}</div>
        <div style="font-size:12px;color:#555;">Total Emails</div>
      </div>
    </div>"""

    # Category breakdown
    cat_rows = "".join(
        f"<tr style='border-bottom:1px solid #eee;'><td style='padding:6px 12px;'>{k}</td>"
        f"<td style='padding:6px 12px;text-align:center;'>{v}</td></tr>"
        for k,v in sorted(s['categories'].items(), key=lambda x:-x[1])
    )
    cat_html = f"""
    <div style="display:flex;gap:20px;margin-top:20px;">
      <div style="flex:1;">
        <h4 style="color:#1a73e8;margin-bottom:8px;">Categories</h4>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">{cat_rows}</table>
      </div>
      <div style="flex:1;">
        <h4 style="color:#1a73e8;margin-bottom:8px;">Top States</h4>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">"""
    for st,v in sorted(s['states'].items(), key=lambda x:-x[1])[:10]:
        cat_html += f"<tr style='border-bottom:1px solid #eee;'><td style='padding:6px 12px;'>{st}</td>"
        cat_html += f"<td style='padding:6px 12px;text-align:center;'>{v}</td></tr>"
    cat_html += "</table></div></div>"

    # Data table
    table_rows = ""
    for r in rows[:200]:  # cap at 200 for email size
        email = r.get('email','')
        biz = is_business_email(email)
        row_bg = "#e6fffa" if biz else "#fff"
        email_display = email if email else "<span style='color:#ccc;'>—</span>"
        email_style = "font-weight:bold;color:#1a73e8;" if biz else "color:#999;"
        table_rows += f"""<tr style="background:{row_bg};">
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('name','')}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;{email_style}" nowrap>{email_display}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('phone','')}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('city','')}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('state','')}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('category','')}</td>
          <td style="padding:5px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('found_date','')}</td>
        </tr>"""

    table_html = f"""
    <h3 style="color:#1a73e8;margin-top:20px;">Full Record List ({len(rows)} total, showing first 200)</h3>
    <table style="border-collapse:collapse;width:100%;font-size:12px;">
      <thead>
        <tr style="background:#1a73e8;color:#fff;">
          <th style="padding:8px;border:1px solid #ddd;">Name</th>
          <th style="padding:8px;border:1px solid #ddd;">Email</th>
          <th style="padding:8px;border:1px solid #ddd;">Phone</th>
          <th style="padding:8px;border:1px solid #ddd;">City</th>
          <th style="padding:8px;border:1px solid #ddd;">State</th>
          <th style="padding:8px;border:1px solid #ddd;">Category</th>
          <th style="padding:8px;border:1px solid #ddd;">Date</th>
        </tr>
      </thead>
      <tbody>{table_rows}</tbody>
    </table>"""

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:1200px;margin:0 auto;padding:20px;">
    <h1 style="color:#1a73e8;border-bottom:2px solid #1a73e8;padding-bottom:8px;">
      {report_type} — Hourly Report
    </h1>
    <p style="color:#555;font-size:12px;">Generated: {now} UTC</p>
    {cards}
    {cat_html}
    {table_html}
    <p style="font-size:10px;color:#999;margin-top:20px;">
      Source: {SERVICES_MD}<br/>
      Skylink LTD Property Preservation Pipeline
    </p>
    </body></html>"""
    return html

def send_email(html_content, subject):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER
    msg['To'] = RECIPIENT
    msg.attach(MIMEText(html_content, 'html'))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(SENDER, SMTP_PASS)
        s.send_message(msg)
    print(f"[EMAIL SENT] {subject}")

def log_result(result: dict):
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **result}) + "\n")

if __name__ == "__main__":
    rows = read_md_table(SERVICES_MD)
    stats = calculate_stats(rows)
    html  = build_html(rows, stats, "General Services Pipeline")
    subject = f"General Services Report — {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC"
    try:
        send_email(html, subject)
        result = {"status": "ok", "records": stats['total'], "biz_email": stats['biz_email'],
                  "with_phone": stats['with_phone'], "email_sent": True}
    except Exception as e:
        result = {"status": "error", "error": str(e), "email_sent": False}
    log_result(result)
    print(json.dumps(result))