# Automated Data Analyst Job Scraper

This project provides a Python script and UI to scrape and aggregate "Data Analyst" job postings from European job boards.

## Features
- Sources: JustJoin.it (API) and GermanTechJobs.de (HTML).
- Keyword filters for data roles with optional exclusions.
- Country code filtering.
- Deduplication by company + title.
- Excel output (`.xlsx`).
- Streamlit-based UI for interactive filtering and downloads.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## CLI Usage
```bash
python main.py --countries PL DE --exclude-senior --exclude-intern
```

The script writes `jobs_data.xlsx` by default. Use `--output` to change the file name.

## UI Usage
```bash
streamlit run app.py
```

Open the provided local URL to run the scraper interactively and download the Excel file.
