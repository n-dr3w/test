import io

import pandas as pd
import streamlit as st

from scraper import DEFAULT_EXCLUDE_KEYWORDS, collect_jobs

st.set_page_config(page_title="Data Analyst Job Scraper", layout="wide")

st.title("Automated Data Analyst Job Scraper")

st.markdown(
    """
    Use the controls below to fetch and filter Data Analyst job postings.
    Results can be downloaded as an Excel file.
    """
)

with st.sidebar:
    st.header("Filters")
    countries_input = st.text_input(
        "Country codes (comma-separated)",
        value="PL, DE",
        help="Example: PL, DE, CH, Remote",
    )
    exclude_senior = st.checkbox("Exclude Senior roles", value=False)
    exclude_intern = st.checkbox("Exclude Intern roles", value=False)
    extra_excludes = st.text_input(
        "Additional exclude keywords (comma-separated)", value=""
    )
    run_button = st.button("Run Scraper")

status_placeholder = st.empty()
results_placeholder = st.empty()

if run_button:
    status_placeholder.info("Fetching jobs...")
    countries = [code.strip() for code in countries_input.split(",") if code.strip()]
    exclude_keywords = list(DEFAULT_EXCLUDE_KEYWORDS)

    if extra_excludes.strip():
        exclude_keywords.extend(
            [kw.strip().lower() for kw in extra_excludes.split(",") if kw.strip()]
        )
    if exclude_senior:
        exclude_keywords.append("senior")
    if exclude_intern:
        exclude_keywords.append("intern")

    try:
        df = collect_jobs(countries=countries or None, exclude_keywords=exclude_keywords)
        if df.empty:
            status_placeholder.warning("No jobs found with the selected filters.")
        else:
            status_placeholder.success(f"Found {len(df)} jobs.")
        results_placeholder.dataframe(df, use_container_width=True)

        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            "Download Excel",
            data=output,
            file_name="jobs_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as exc:  # noqa: BLE001
        status_placeholder.error(f"Scraper failed: {exc}")
