# CS2 Tier-1 Automated Events Calendar

An automated Python script that fetches upcoming Tier-1 CS2 matches from the PandaScore API and generates a live, updating `.ics` calendar subscription feed.

## Features
* Runs multiple times a day via GitHub Actions.
* Automatically strips out lower-tier tournaments.
* Fully compatible with any calendar supporting `.ics` import.

## Setup Instructions

If you want to fork this repository and host your own live calendar:

1. Create a free account at [PandaScore](https://pandascore.co/) and get a developer API token.
2. Fork this repository.
3. Go to your new repository's **Settings > Secrets and variables > Actions** and add a secret named `PANDASCORE_TOKEN` containing your API key.
4. Go to the **Actions** tab and manually trigger the workflow once to generate your initial calendar file.

## How to add to Calendar

Copy the **Raw** link of the generated `cs2_upcoming_matches.ics` file and paste it into your calendar application's "Subscribe from URL".
