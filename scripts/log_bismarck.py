import json
from datetime import datetime

log_entry = {
    "datetime": datetime.now().isoformat(),
    "state": "North Dakota",
    "city": "Bismarck",
    "category": "Landscaping Service",
    "new_records": 1,
    "validated_count": 0,
    "total_validated": 34,
    "email_sent": True
}

with open('/home/mhcybroot/jobs/property-preservation-clients/data/combined_log.json') as f:
    log = json.load(f)

log.append(log_entry)

with open('/home/mhcybroot/jobs/property-preservation-clients/data/combined_log.json', 'w') as f:
    json.dump(log, f, indent=2)

print("Logged:", json.dumps(log_entry, indent=2))