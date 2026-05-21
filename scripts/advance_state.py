import json

with open('/home/mhcybroot/jobs/property-preservation-clients/data/search_state.json', 'r') as f:
    state = json.load(f)

state_idx = state['state_idx']
cat_idx = state['cat_idx']

STATES = [
    ("Alabama","Birmingham"),("Alaska","Anchorage"),("Arizona","Phoenix"),("Arkansas","Little Rock"),
    ("California","Sacramento"),("Colorado","Denver"),("Connecticut","Hartford"),("Delaware","Wilmington"),
    ("Florida","Jacksonville"),("Georgia","Atlanta"),("Hawaii","Honolulu"),("Idaho","Boise"),
    ("Illinois","Springfield"),("Indiana","Indianapolis"),("Iowa","Des Moines"),("Kansas","Topeka"),
    ("Kentucky","Louisville"),("Louisiana","Baton Rouge"),("Maine","Augusta"),("Maryland","Baltimore"),
    ("Massachusetts","Boston"),("Michigan","Lansing"),("Minnesota","St. Paul"),("Mississippi","Jackson"),
    ("Missouri","Jefferson City"),("Montana","Helena"),("Nebraska","Lincoln"),("Nevada","Las Vegas"),
    ("New Hampshire","Concord"),("New Jersey","Trenton"),("New Mexico","Santa Fe"),("New York","Albany"),
    ("North Carolina","Raleigh"),("North Dakota","Bismarck"),("Ohio","Columbus"),("Oklahoma","Oklahoma City"),
    ("Oregon","Salem"),("Pennsylvania","Harrisburg"),("Rhode Island","Providence"),("South Carolina","Columbia"),
    ("South Dakota","Pierre"),("Tennessee","Nashville"),("Texas","Austin"),("Utah","Salt Lake City"),
    ("Vermont","Montpelier"),("Virginia","Richmond"),("Washington","Olympia"),("West Virginia","Charleston"),
    ("Wisconsin","Madison"),("Wyoming","Cheyenne")
]

CATEGORIES = ["Plumber","HVAC Contractor","Electrician","Roofing Contractor","Handyman",
              "Landscaping Service","Painting Service","Cleaning Service","Snow Removal Service","Moving Service"]

# Advance state
state['state_idx'] = (state_idx + 1) % len(STATES)
state['cat_idx'] = (cat_idx + 1) % len(CATEGORIES)

with open('/home/mhcybroot/jobs/property-preservation-clients/data/search_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f"Advanced to slot {len(STATES)} states: idx={state['state_idx']} cat_idx={state['cat_idx']}")
print(f"Slot: {STATES[state['state_idx']]} / {CATEGORIES[state['cat_idx']]}")