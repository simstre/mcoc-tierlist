# MCOC YouTuber Tier List

**Live:** https://mcoc-tierlist-sims7-f3a1c04d.koyeb.app

A web app that aggregates Marvel Contest of Champions (MCOC) champion rankings from top YouTube creators into a unified tier list.

<img width="673" height="812" alt="image" src="https://github.com/user-attachments/assets/3a490055-7545-484a-aa82-3d5720468a9c" />


## Features

- **Ranking Up** - 310 champions scored 0-100, grouped by tier (God/Great/Good/OK/Low)
- **Awakening Gems** - Champions that benefit most from being awakened
- **Sig Stones** - Champions worth investing signature stones into, grouped by priority
- **Immunities** - Multi-select filter to find champions with specific immunities
- Class filtering and search across all views
- Champion portraits from the Fandom wiki

## Data Sources

Rankings aggregated from 5 YouTube creators via the Summoner's Tier List community spreadsheet:
- KT1, Lagacy, Vega, MGuideBlog, Omega

## Tech Stack

- **Backend**: Python / FastAPI
- **Frontend**: Vanilla HTML/CSS/JS
- **Scheduling**: APScheduler (daily portrait updates at 6:00 AM)

## Running Locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

App runs on `http://localhost:8100`.
