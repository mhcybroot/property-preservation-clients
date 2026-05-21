import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

today = date.today().isoformat()

new_records = [
    {"name": "NH Tax Deed & Property Auctions", "email": "info@nhtaxdeedauctions.com", "phone": "(603) 301-0185", "city": "Concord", "state": "NH", "category": "Auction Services"},
    {"name": "LandVest", "email": "info@landvest.com", "phone": "603-228-2020", "city": "Concord", "state": "NH", "category": "Auction Services"},
    {"name": "Bird's Nest Auctions", "email": "help@birdsnestauctions.com", "phone": "603-556-8295", "city": "Derry", "state": "NH", "category": "Auction Services"},
]

rows_html = "<tr><th>Name</th><th>Email</th><th>Phone</th><th>City</th><th>State</th><th>Category</th><th>Found Date</th></tr>"
for r in new_records:
    rows_html += f"<tr><td>{r['name']}</td><td><a href='mailto:{r['email']}'>{r['email']}</a></td><td>{r['phone']}</td><td>{r['city']}</td><td>{r['state']}</td><td>{r['category']}</td><td>{today}</td></tr>"

html = f"""<html><body>
<h2>New REO Service Provider Leads: Concord, New Hampshire</h2>
<p><b>Category:</b> Auction Services | <b>Date:</b> {today}</p>
<table border='1' cellpadding='8' cellspacing='0' style='border-collapse:collapse'>
{rows_html}
</table>
<p>{len(new_records)} new records added to reo_services.md</p>
</body></html>"""

msg = MIMEMultipart('alternative')
msg['Subject'] = 'REO Service Provider Report: Concord, NH - Auction Services'
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg.attach(MIMEText(html, 'html'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

password = "User_#$$2026"

with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', password)
    s.send_message(msg)
    print('Email sent successfully')