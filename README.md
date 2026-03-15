# MCOC YouTubers Tier List

**Live:** https://mcoc.app

A web app that aggregates Marvel Contest of Champions (MCOC) champion rankings from top YouTube creators into a unified tier list.

<img width="673" height="812" alt="image" src="https://github.com/user-attachments/assets/3a490055-7545-484a-aa82-3d5720468a9c" />


## Features

- **Ranking Up** - 317 champions scored 0-100, grouped by tier (God/Great/Good/OK/Low)
- **Awakening Gems** - Champions that benefit most from being awakened
- **Sig Stones** - Champions worth investing signature stones into, grouped by priority
- **Prestige** - Champion prestige values at different signature levels
- **Immunities** - Multi-select filter to find champions with specific immunities
- Class filtering and search across all views
- Champion portraits from the Fandom wiki

## Data Sources

Rankings aggregated from 3 YouTube creators:
- Vega, Lagacy, Omega

## Tech Stack

- **Hosting**: Vercel (static CDN)
- **Frontend**: Vanilla HTML/CSS/JS
- **Data**: Pre-generated JSON, refreshed daily via Vercel Cron

## Running Locally

```bash
pip install -r requirements.txt
python generate_data.py   # generates public/data/tierlist.json
# Then serve public/ with any static server
```
