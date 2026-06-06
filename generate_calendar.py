import os
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event

# Automatically grabs the hidden token from GitHub's settings
TOKEN = os.environ.get("PANDASCORE_TOKEN")
URL = "https://api.pandascore.co/csgo/matches/upcoming"
ALLOWED_ORGANIZERS = ['esl', 'blast', 'pgl', 'starladder', 'iem', 'intel extreme masters', 'dreamhack', 'major']

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

response = requests.get(URL, headers=headers, params={"per_page": 100, "sort": "begin_at"})
if response.status_code != 200:
    exit()

all_matches = response.json()
cal = Calendar()
cal.add('prodid', '-//CS2 Tier 1 Calendar//EN')
cal.add('version', '2.0')

for match in all_matches:
    if not match.get('begin_at'):
        continue
    tournament_name = match.get('league', {}).get('name', '')
    match_name = match.get('name', '')
    
    if not any(keyword in f"{tournament_name} {match_name}".lower() for keyword in ALLOWED_ORGANIZERS):
        continue
        
    event = Event()
    event.add('summary', match_name)
    event.add('dtstart', datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00')))
    event.add('dtend', datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00')) + timedelta(hours=2, minutes=30))
    
    stream_list = match.get('streams_list', [])
    stream_url = stream_list[0].get('raw_url') if stream_list else "No stream available"
    
    event.add('description', f"🏆 Tournament: {tournament_name}\n📺 Stream: {stream_url}")
    event.add('uid', f"pandascore-{match.get('id')}@cs2")
    cal.add_component(event)

with open("cs2_upcoming_matches.ics", "wb") as f:
    f.write(cal.to_ical())
