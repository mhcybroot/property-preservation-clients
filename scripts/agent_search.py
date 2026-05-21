#!/usr/bin/env python3
"""Coordinator for agent-driven property preservation pipeline."""
import json, os, sys

BASE = "/home/mhcybroot/jobs/property-preservation-clients"
DATA = f"{BASE}/data"
MD_FILE = f"{DATA}/services.md"
STATE_FILE = f"{DATA}/search_state.json"

CATEGORIES = [
    "Plumber", "HVAC Contractor", "Electrician", "Roofing Contractor",
    "Handyman", "Landscaping Service", "Painting Service",
    "Cleaning Service", "Snow Removal Service", "Moving Service"
]

# 50 states in rotation order
STATES = [
    ("Alabama","Birmingham"),("Alaska","Anchorage"),("Arizona","Phoenix"),
    ("Arkansas","Little Rock"),("California","Sacramento"),("Colorado","Denver"),
    ("Connecticut","Hartford"),("Delaware","Wilmington"),("Florida","Jacksonville"),
    ("Georgia","Atlanta"),("Hawaii","Honolulu"),("Idaho","Boise"),
    ("Illinois","Springfield"),("Indiana","Indianapolis"),("Iowa","Des Moines"),
    ("Kansas","Topeka"),("Kentucky","Louisville"),("Louisiana","Baton Rouge"),
    ("Maine","Augusta"),("Maryland","Baltimore"),("Massachusetts","Boston"),
    ("Michigan","Lansing"),("Minnesota","St. Paul"),("Mississippi","Jackson"),
    ("Missouri","Jefferson City"),("Montana","Helena"),("Nebraska","Lincoln"),
    ("Nevada","Las Vegas"),("New Hampshire","Concord"),("New Jersey","Trenton"),
    ("New Mexico","Santa Fe"),("New York","Albany"),("North Carolina","Raleigh"),
    ("North Dakota","Bismarck"),("Ohio","Columbus"),("Oklahoma","Oklahoma City"),
    ("Oregon","Salem"),("Pennsylvania","Harrisburg"),("Rhode Island","Providence"),
    ("South Carolina","Columbia"),("South Dakota","Pierre"),("Tennessee","Nashville"),
    ("Texas","Austin"),("Utah","Salt Lake City"),("Vermont","Montpelier"),
    ("Virginia","Richmond"),("Washington","Olympia"),("West Virginia","Charleston"),
    ("Wisconsin","Madison"),("Wyoming","Cheyenne")
]

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"state_idx": 0, "cat_idx": 0}

def save_state(s):
    with open(STATE_FILE, 'w') as f:
        json.dump(s, f)

def next_slot():
    s = load_state()
    state_idx = s["state_idx"]
    cat_idx = s["cat_idx"]
    state, city = STATES[state_idx]
    category = CATEGORIES[cat_idx]
    # advance
    cat_idx = (cat_idx + 1) % len(CATEGORIES)
    if cat_idx == 0:
        state_idx = (state_idx + 1) % len(STATES)
    save_state({"state_idx": state_idx, "cat_idx": cat_idx})
    return state, city, category

def append_md(name, email, phone, address, city, county, state, zipcode, category):
    date = __import__('datetime').datetime.now().strftime("%Y-%m-%d")
    row = f"| {name} | {email} | {phone} | {address} | {city} | {county} | {state} | {zipcode} | {category} | {date} |"
    with open(MD_FILE, "a") as f:
        f.write(row + "\n")

if __name__ == "__main__":
    state, city, category = next_slot()
    print(f"SEARCH: {category} in {city}, {state}")
    # Signal delegate_task to run mmx search for this slot
    print(f"STATE={state} CITY={city} CATEGORY={category}")