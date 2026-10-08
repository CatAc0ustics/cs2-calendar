import os
import re
import requests
from datetime import datetime, timedelta
from icalendar import Calendar, Event

TOKEN = os.environ.get("PANDASCORE_TOKEN")
URL = "https://api.pandascore.co/csgo/matches/upcoming"

if not TOKEN:
    raise RuntimeError("PANDASCORE_TOKEN is missing or empty")

ALLOWED_ORGANIZERS = [
    "esl",
    "blast",
    "pgl",
    "iem",
    "intel extreme masters",
    "major",
    "ewc",
    "road to ewc",
    "esports world cup",
    "thunderpick world championship"
]

EXCLUDED_PATTERNS = [
    r"\bplayoff\b",
    r"\bplayoffs\b",
    r"\bopen[-\s]?qualifier\b",
    r"\bopen[-\s]?qualifiers\b",
    r"\bclosed[-\s]?qualifier\b",
    r"\bclosed[-\s]?qualifiers\b",
    r"\bchallenger\s+league\b",
    r"\bchallengers\s+league\b",
]

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

all_matches = []

for page in range(1, 11):
    params = {
        "per_page": 100,
        "page": page,
        "sort": "begin_at"
    }

    response = requests.get(URL, headers=headers, params=params, timeout=30)
    request_id = response.headers.get("X-Request-Id") or response.headers.get("X-Request-ID")
    print(f"PandaScore page {page}: HTTP {response.status_code}; request_id={request_id or 'unavailable'}")

    # Never treat an API error as an empty schedule or overwrite a previously good feed.
    response.raise_for_status()
    page_data = response.json()
    if not isinstance(page_data, list):
        raise RuntimeError(f"PandaScore returned unexpected JSON type: {type(page_data).__name__}")

    print(f"PandaScore page {page}: {len(page_data)} matches")
    if not page_data:
        break

    all_matches.extend(page_data)

print(f"PandaScore total matches fetched: {len(all_matches)}")

accepted_events = {}
rejected_missing_start = 0
rejected_organizer = 0
rejected_exclusion = 0
eligible_match_names = []

for match in all_matches:
    if not match.get("begin_at"):
        rejected_missing_start += 1
        continue

    tournament_name = match.get("league", {}).get("name", "")
    stage_name = match.get("tournament", {}).get("name", "Unknown Stage")
    match_name = match.get("name", "")

    opponents = match.get("opponents", [])

    for opp in opponents:
        opp_info = opp.get("opponent", {})
        acronym = opp_info.get("acronym")
        full_name = opp_info.get("name")

        if acronym and full_name:
            match_name = match_name.replace(acronym, full_name)

    full_info = " ".join(
        str(part).strip()
        for part in [tournament_name, stage_name, match_name]
        if part
    ).lower()

    if not any(keyword.lower() in full_info for keyword in ALLOWED_ORGANIZERS):
        rejected_organizer += 1
        if len(eligible_match_names) < 12:
            eligible_match_names.append(f"{tournament_name} / {stage_name} / {match_name}")
        continue

    if any(re.search(pattern, full_info, flags=re.IGNORECASE) for pattern in EXCLUDED_PATTERNS):
        rejected_exclusion += 1
        continue

    num_games = match.get("number_of_games")
    match_format = f"BO{num_games}" if num_games else "Unknown Format"

    start_time = datetime.fromisoformat(match["begin_at"].replace("Z", "+00:00"))
    end_time = start_time + timedelta(hours=2, minutes=30)

    if "blast" in full_info:
        stream_url = "https://twitch.tv/blastpremier"
    elif any(k in full_info for k in ["esl", "iem", "intel extreme masters"]):
        stream_url = "https://twitch.tv/eslcs"
    elif "pgl" in full_info:
        stream_url = "https://twitch.tv/pgl"
    elif any(k in full_info for k in ["ewc", "esports world cup", "road to ewc"]):
        stream_url = "https://twitch.tv/ewc_plus_en"
    else:
        stream_list = match.get("streams_list", [])
        stream_url = (stream_list[0].get("raw_url") or "No stream available") if stream_list else "No stream available"

    event = Event()
    event.add("summary", match_name)
    event.add("dtstart", start_time)
    event.add("dtend", end_time)
    event.add(
        "description",
        f"Tournament: {tournament_name}\n"
        f"Stage: {stage_name}\n"
        f"Format: {match_format}\n"
        f"Stream: {stream_url}"
    )

    uid = f"pandascore-{match.get('id')}@cs2"
    event.add("uid", uid)
    accepted_events[uid] = event

print(
    f"Calendar filter results: accepted={len(accepted_events)}, "
    f"missing_start={rejected_missing_start}, "
    f"organizer_mismatch={rejected_organizer}, "
    f"excluded_tournament={rejected_exclusion}"
)
if not accepted_events and eligible_match_names:
    print("Sample events rejected by organizer filter:")
    for item in eligible_match_names:
        print(f"  {item}")

cal = Calendar()
cal.add("prodid", "-//CS2 Match Schedule//EN")
cal.add("version", "2.0")
cal.add("x-wr-calname", "CS2 Match Schedule")
cal.add("name", "CS2 Match Schedule")
cal.add("title", "CS2 Match Schedule")

for event in accepted_events.values():
    cal.add_component(event)

ics_filename = "cs2_upcoming_matches.ics"
with open(ics_filename, "wb") as f:
    f.write(cal.to_ical())

print(f"Wrote {ics_filename} with {len(accepted_events)} events")
