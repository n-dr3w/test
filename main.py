import argparse

from scraper import DEFAULT_EXCLUDE_KEYWORDS, collect_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Data Analyst job scraper")
    parser.add_argument(
        "--countries",
        nargs="*",
        default=None,
        help="Country codes to include (e.g., PL DE CH Remote)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=DEFAULT_EXCLUDE_KEYWORDS,
        help="Keywords to exclude from job titles",
    )
    parser.add_argument(
        "--exclude-senior",
        action="store_true",
        help="Exclude Senior roles",
    )
    parser.add_argument(
        "--exclude-intern",
        action="store_true",
        help="Exclude Intern roles",
    )
    parser.add_argument(
        "--output",
        default="jobs_data.xlsx",
        help="Output Excel file path",
    )
    args = parser.parse_args()

    exclude_keywords = list(args.exclude)
    if args.exclude_senior:
        exclude_keywords.append("senior")
    if args.exclude_intern:
        exclude_keywords.append("intern")

    df = collect_jobs(countries=args.countries, exclude_keywords=exclude_keywords)
    df.to_excel(args.output, index=False)

    print(f"Saved {len(df)} jobs to {args.output}")


if __name__ == "__main__":
    main()
