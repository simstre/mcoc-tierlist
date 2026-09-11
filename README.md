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

Rankings aggregated from 4 YouTube creators:
- Vega, Lagacy, MetalSonicDude, Seatin

## Tech Stack

- **Hosting**: Vercel (static CDN)
- **Frontend**: Vanilla HTML/CSS/JS
- **Data**: Pre-generated JSON, refreshed daily via Vercel Cron

## Source auto-discovery

Some creators (notably Vega) publish a brand-new Google Sheet each month. The
GitHub Action `.github/workflows/discover-sources.yml` runs `fetch_sources.py`
once a day, searches YouTube for each creator's most recent tier list video,
parses the description for a Google Sheets link, and commits the result to
`cached_sources.json`. The daily Vercel cron then reads that file and uses the
fresh sheet IDs (falling back to the hardcoded `SOURCES_CONFIG` defaults if the
cache is missing).

To run discovery manually:

```bash
pip install yt-dlp
python fetch_sources.py            # discover + update cached_sources.json
python fetch_sources.py --dry-run  # show what would change without writing
```

## Monthly banner

The header banner tracks the newest champion. Kabam publishes a
[Champion Spotlight](https://playcontestofchampions.com/news/category/champion-spotlights/)
post with a square piece of key art for every release, so
`.github/workflows/refresh-portraits.yml` runs `fetch_banner.py` daily: it
reads that category's WordPress feed, takes the most recent champion the tier
lists actually rank (the creators trail a release by a month or two), crops the
art to the banner's 3:1 shape and writes `public/banner.jpg`.

It only writes when the champion changes — in practice about once a month — and
leaves the current banner alone if anything fails.

```bash
pip install -r requirements.txt Pillow
python fetch_banner.py
```

## Running Locally

```bash
pip install -r requirements.txt
python generate_data.py   # generates public/data/tierlist.json
# Then serve public/ with any static server
```
