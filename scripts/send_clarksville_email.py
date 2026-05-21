import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

record = {
    'name': 'Mac Plumbing Heating & Air',
    'email': 'admin@macplumbing.com',
    'phone': '(931) 346-0675',
    'address': '2968B E. Old Ashland City Rd.',
    'city': 'Clarksville',
    'county': 'Montgomery',
    'state': 'Tennessee',
    'zip': '37043',
    'category': 'Plumber',
    'found_date': '2026-05-21'
}

body = """New leads found for Clarksville, Tennessee.

| Name | Email | Phone | Address | City | County | State | Zip | Category | Found |
|------|-------|-------|---------|------|--------|-------|-----|----------|-------|"""
body += "\n| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
    record['name'], record['email'], record['phone'], record['address'],
    record['city'], record['county'], record['state'], record['zip'],
    record['category'], record['found_date']
)

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New Leads: Clarksville, Tennessee'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
    print('Email sent successfully')