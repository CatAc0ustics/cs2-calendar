import os
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event

TOKEN = os.environ.get("PANDASCORE_TOKEN")
URL = "https://api.pandascore.co/csgo/matches/upcoming"
ALLOWED_ORGANIZERS = ['esl', 'blast', 'pgl', 'starladder', 'iem', 'intel extreme masters', 'dreamhack', 'major']

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

all_matches = []

for page in range(1, 4):
    params = {
        "per_page": 100, 
        "page": page,
        "sort": "begin_at"
    }
    response = requests.get(URL, headers=headers, params=params)
    if response.status_code == 200:
        page_data = response.json()
        if not page_data: 
            break
        all_matches.extend(page_data)
    else:
        break

if not all_matches:
    exit()

cal = Calendar()
cal.add('prodid', '-//CS2 Match Schedule//EN')
cal.add('version', '2.0')

cal.add('x-wr-calname', 'CS2 Match Schedule')
cal.add('name', 'CS2 Match Schedule')
cal.add('title', 'CS2 Match Schedule')

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
