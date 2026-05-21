import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

body = """REO Title Company Leads — Topeka, Kansas (2026-05-22)
====================================================================

+ Heartland Title Services, Inc. | toml@heartlandtitleco.com | 785-224-4451 | 2914 SW Macvicar Ave, Topeka, KS 66614
+ Heartland Title Services, Inc. | tjl@heartlandtitleco.com | 785-640-7896 | 2914 SW Macvicar Ave, Topeka, KS 66614
+ Verity Title | info@veritytitle.com | 785-284-5933 | 5930 SW 29th St STE #200, Topeka, KS 66614
+ Kansas Secured Title | butler@kstitle.com | 316-775-6941 | 614 State Street Suite B, Augusta, KS 67010
+ Lawyers Title of Kansas, Inc. | info@ltkansas.com | 785-271-9500 | 5715 SW 21st Street, Topeka, KS 66604
+ Security 1st Title | (785) 329-5813 | 2655 SW Wanamaker Rd., Ste C, Topeka, KS 66614

Total: 6 new records (2 email-only, 1 phone-only, 3 with both)
"""

msg = MIMEMultipart()
msg['From'] = 'data@skylink-ltd.com'
msg['To'] = 'data@skylink-ltd.com'
msg['Subject'] = 'New REO Leads: Topeka, Kansas'
msg.attach(MIMEText(body, 'plain'))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
with smtplib.SMTP_SSL('162.0.235.129', 465, context=ctx, timeout=30) as s:
    s.login('data@skylink-ltd.com', 'Skylink#2026')
    s.send_message(msg)
print("Email sent.")