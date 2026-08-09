import os
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event

TOKEN = os.environ.get("PANDASCORE_TOKEN")
URL = "https://api.pandascore.co/csgo/matches/upcoming"

ALLOWED_ORGANIZERS = [
    'esl', 'blast', 'pgl', 'iem', 'intel extreme masters', 
    'dreamhack', 'major', 'ewc', 'road to ewc', 'esports world cup'
]

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

existing_events = {}
ics_filename = "cs2_upcoming_matches.ics"

if os.path.exists(ics_filename):
    try:
        with open(ics_filename, "rb") as f:
            old_cal = Calendar.from_ical(f.read())
            for component in old_cal.walk('vevent'):
                uid = str(component.get('uid'))
                if uid:
                    existing_events[uid] = component
    except Exception:
        pass

for match in all_matches:
    if not match.get('begin_at'):
        continue
    tournament_name = match.get('league', {}).get('name', '')
    match_name = match.get('name', '')
    
    opponents = match.get('opponents', [])
    for opp in opponents:
        opp_info = opp.get('opponent', {})
        acronym = opp_info.get('acronym')
        full_name = opp_info.get('name')
        if acronym and full_name:
            match_name = match_name.replace(acronym, full_name)
            
    if not any(keyword in f"{tournament_name} {match_name}".lower() for keyword in ALLOWED_ORGANIZERS):
        continue
        
    stage_name = match.get('tournament', {}).get('name', 'Unknown Stage')
    
    full_info = f"{tournament_name} {stage_name} {match_name}".lower()
    if "challenger league" in full_info or "challengers league" in full_info or ("blast open" in full_info and "playoff" in full_info):
        continue

    num_games = match.get('number_of_games')
    match_format = f"BO{num_games}" if num_games else "Unknown Format"
        
    event = Event()
    event.add('summary', match_name)
    event.add('dtstart', datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00')))
    event.add('dtend', datetime.fromisoformat(match['begin_at'].replace('Z', '+00:00')) + timedelta(hours=2, minutes=30))
    
    stream_list = match.get('streams_list', [])
    stream_url = stream_list[0].get('raw_url') if stream_list else "No stream available"
    
    event.add('description', f"Tournament: {tournament_name}\nStage: {stage_name}\nFormat: {match_format}\nStream: {stream_url}")
    uid = f"pandascore-{match.get('id')}@cs2"
    event.add('uid', uid)
    
    existing_events[uid] = event

cal = Calendar()
cal.add('prodid', '-//CS2 Match Schedule//EN')
cal.add('version', '2.0')

cal.add('x-wr-calname', 'CS2 Match Schedule')
cal.add('name', 'CS2 Match Schedule')
cal.add('title', 'CS2 Match Schedule')

for event in existing_events.values():
    cal.add_component(event)

with open(ics_filename, "wb") as f:
    f.write(cal.to_ical())
