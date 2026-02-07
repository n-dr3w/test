"""Core scraping logic shared by CLI and Streamlit UI."""

import json
import random
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

INCLUDE_KEYWORDS = [
    "data analyst",
    "data scientist",
    "business analyst",
    "bi developer",
    "analytics engineer",
]

DEFAULT_EXCLUDE_KEYWORDS = [
    "manager",
]


@dataclass
class JobPosting:
    source: str
    title: str
    company: str
    salary: str
    city: str
    country: str
    remote: str
    tech_stack: str
    date_posted: str
    link: str


def normalized_text(text: str) -> str:
    return " ".join(text.lower().split())


def passes_keyword_filters(title: str, exclude_keywords: Iterable[str]) -> bool:
    normalized = normalized_text(title)
    if not any(keyword in normalized for keyword in INCLUDE_KEYWORDS):
        return False
    if any(keyword in normalized for keyword in exclude_keywords):
        return False
    return True


def within_country_filter(country: str, country_filter: Optional[List[str]]) -> bool:
    if not country_filter:
        return True
    return country.upper() in {code.upper() for code in country_filter}


def random_delay() -> None:
    time.sleep(random.uniform(1, 3))


def safe_date(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return date_parser.parse(value).date().isoformat()
    except (ValueError, TypeError):
        return ""


def format_salary(employment_types: List[Dict]) -> str:
    if not employment_types:
        return ""
    salaries = []
    for employment in employment_types:
        salary = employment.get("salary") or {}
        if not salary:
            continue
        from_amount = salary.get("from")
        to_amount = salary.get("to")
        currency = salary.get("currency")
        if from_amount and to_amount and currency:
            salaries.append(f"{from_amount} - {to_amount} {currency}")
    return "; ".join(salaries)


def fetch_justjoin_jobs(session: requests.Session) -> List[JobPosting]:
    jobs: List[JobPosting] = []
    endpoints = [
        "https://justjoin.it/api/offers",
        "https://justjoin.it/api/offers?",  # fallback for edge caching
        "https://justjoin.it/api/offers?language=en",
    ]
    payload = None
    last_error: Optional[Exception] = None

    for url in endpoints:
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            payload = response.json()
            break
        except (requests.RequestException, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    if payload is None:
        print(f"[JustJoin] Failed to fetch: {last_error}", file=sys.stderr)
        return jobs

    for offer in payload:
        title = offer.get("title") or ""
        company = offer.get("company_name") or ""
        city = offer.get("city") or ""
        country = offer.get("country_code") or ""
        remote = "Yes" if offer.get("remote") else "No"
        tech_stack = ", ".join(offer.get("skills") or [])
        date_posted = safe_date(offer.get("published_at"))
        link = offer.get("url") or ""
        salary = format_salary(offer.get("employment_types") or [])

        jobs.append(
            JobPosting(
                source="JustJoin.it",
                title=title,
                company=company,
                salary=salary,
                city=city,
                country=country,
                remote=remote,
                tech_stack=tech_stack,
                date_posted=date_posted,
                link=link,
            )
        )
    return jobs


def parse_germantechjobs_html(html: str) -> List[JobPosting]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[JobPosting] = []

    cards = soup.select("article, div.job-card, div.job-listing")
    if not cards:
        cards = soup.select("a[href*='/jobs/']")

    for card in cards:
        title_tag = (
            card.select_one("h2")
            or card.select_one("h3")
            or card.select_one(".job-title")
        )
        title = title_tag.get_text(strip=True) if title_tag else ""
        if not title:
            continue
        company_tag = (
            card.select_one(".company")
            or card.select_one(".company-name")
            or card.select_one(".job-company")
        )
        company = company_tag.get_text(strip=True) if company_tag else ""
        location_tag = (
            card.select_one(".location")
            or card.select_one(".job-location")
            or card.select_one(".locations")
        )
        location_text = location_tag.get_text(strip=True) if location_tag else ""
        city = location_text
        country = "DE"
        link_tag = card if card.name == "a" else card.select_one("a[href]")
        link = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
        if link and link.startswith("/"):
            link = f"https://germantechjobs.de{link}"
        jobs.append(
            JobPosting(
                source="GermanTechJobs.de",
                title=title,
                company=company,
                salary="",
                city=city,
                country=country,
                remote="",
                tech_stack="",
                date_posted="",
                link=link,
            )
        )
    return jobs


def fetch_germantechjobs(session: requests.Session, query: str) -> List[JobPosting]:
    url = "https://germantechjobs.de/jobs"
    try:
        response = session.get(url, params={"search": query}, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"[GermanTechJobs] Failed to fetch: {exc}", file=sys.stderr)
        return []

    return parse_germantechjobs_html(response.text)


def deduplicate_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (normalized_text(job.company), normalized_text(job.title))
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(job)
    return unique_jobs


def build_dataframe(jobs: List[JobPosting]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Source": job.source,
                "Job Title": job.title,
                "Company": job.company,
                "Salary": job.salary,
                "City": job.city,
                "Country": job.country,
                "Remote": job.remote,
                "Tech Stack": job.tech_stack,
                "Date Posted": job.date_posted,
                "Link": job.link,
            }
            for job in jobs
        ]
    )


def collect_jobs(
    countries: Optional[List[str]] = None,
    exclude_keywords: Optional[List[str]] = None,
) -> pd.DataFrame:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    jobs: List[JobPosting] = []

    jobs.extend(fetch_justjoin_jobs(session))
    random_delay()
    jobs.extend(fetch_germantechjobs(session, "Data Analyst"))

    filtered_jobs = [
        job
        for job in jobs
        if passes_keyword_filters(job.title, exclude_keywords or [])
        and within_country_filter(job.country, countries)
    ]

    filtered_jobs = deduplicate_jobs(filtered_jobs)

    return build_dataframe(filtered_jobs)
