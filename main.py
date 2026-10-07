"""Main entry point for the Multi-Source Web Scraping & Data Consolidation ETL pipeline."""
import argparse
import csv
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import time
from typing import Optional

from processing.cleaning import clean_record
from processing.deduplication import deduplicate_records
from processing.validation import validate_records
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

CSV_FIELDNAMES = [
    "source",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "source_url",
    "scraped_at",
]


def setup_logging(log_file_path: Path) -> logging.Logger:
    """Configure unified logging to both console and a time-stamped log file.

    Args:
        log_file_path: Path to write the log file.

    Returns:
        Root logger instance.
    """
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicate lines
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    # Console Handler (ensure proper encoding on Windows)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(str(log_file_path), mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger


def write_csv_dataset(output_path: Path, records: list[dict]) -> None:
    """Write cleaned, validated, and deduplicated records to CSV file.

    Args:
        output_path: Target path for the output CSV file.
        records: List of final record dictionaries.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)


def write_summary_report(output_path: Path, report_data: dict) -> None:
    """Write structured execution metrics to JSON file.

    Args:
        output_path: Target path for summary report JSON.
        report_data: Dictionary of execution metrics.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, mode="w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def run_pipeline(
    output_dir: Path,
    log_file: Path,
    rate_limit: float = 0.5,
    timeout: int = 15,
    max_pages: Optional[int] = None,
    sources_to_scrape: str = "both",
) -> dict:
    """Execute the end-to-end web scraping, cleaning, validation, and deduplication pipeline.

    Args:
        output_dir: Directory where final_dataset.csv and summary_report.json will be saved.
        log_file: Path for log file output.
        rate_limit: Request delay in seconds.
        timeout: HTTP request timeout in seconds.
        max_pages: Maximum pages per source (None for all pages).
        sources_to_scrape: Which sources to scrape ('both', 'books', or 'quotes').

    Returns:
        Summary report dictionary.
    """
    logger = setup_logging(log_file)
    start_dt = datetime.now(timezone.utc)
    start_time_sec = time.time()

    logger.info("=" * 60)
    logger.info("Starting Multi-Source Web Scraping & Consolidation Pipeline")
    logger.info("Start Time (UTC): %s", start_dt.isoformat())
    logger.info("Target sources: %s | Max pages: %s", sources_to_scrape, max_pages or "Unlimited")
    logger.info("Rate limit: %.2fs | Timeout: %ds", rate_limit, timeout)
    logger.info("=" * 60)

    raw_records_by_source: dict[str, list[dict]] = {
        "Books to Scrape": [],
        "Quotes to Scrape": [],
    }

    # Stage 4: Scrape Books
    if sources_to_scrape in ("both", "books"):
        try:
            books_scraper = BooksScraper(
                rate_limit_delay=rate_limit,
                timeout=timeout,
            )
            raw_books = books_scraper.scrape(max_pages=max_pages)
            raw_records_by_source["Books to Scrape"] = raw_books
        except Exception as exc:
            logger.error("BooksScraper encountered an unhandled exception: %s", exc, exc_info=True)

    # Stage 4: Scrape Quotes
    if sources_to_scrape in ("both", "quotes"):
        try:
            quotes_scraper = QuotesScraper(
                rate_limit_delay=rate_limit,
                timeout=timeout,
            )
            raw_quotes = quotes_scraper.scrape(max_pages=max_pages)
            raw_records_by_source["Quotes to Scrape"] = raw_quotes
        except Exception as exc:
            logger.error("QuotesScraper encountered an unhandled exception: %s", exc, exc_info=True)

    # Processing Stages: Clean, Validate, Deduplicate per source
    source_stats: dict[str, dict] = {}
    all_final_records: list[dict] = []
    overall_rejection_counts: dict[str, int] = {}
    total_raw = 0
    total_cleaned = 0
    total_rejected = 0
    total_duplicates = 0

    for source_name, raw_list in raw_records_by_source.items():
        total_raw += len(raw_list)

        # Stage 5: Clean records
        cleaned_list = [clean_record(rec) for rec in raw_list]
        total_cleaned += len(cleaned_list)

        # Stage 6: Validate records
        valid_list, rej_counts, rej_details = validate_records(cleaned_list)
        rejected_count = len(rej_details)
        total_rejected += rejected_count
        for reason, count in rej_counts.items():
            overall_rejection_counts[reason] = overall_rejection_counts.get(reason, 0) + 1

        # Stage 7: Deduplicate records
        unique_list, dup_list = deduplicate_records(valid_list)
        dup_count = len(dup_list)
        total_duplicates += dup_count

        source_stats[source_name] = {
            "raw_records": len(raw_list),
            "cleaned_records": len(cleaned_list),
            "valid_records": len(valid_list),
            "rejected_records": rejected_count,
            "rejection_reasons": rej_counts,
            "duplicates_removed": dup_count,
            "final_records": len(unique_list),
        }

        all_final_records.extend(unique_list)

    total_final = len(all_final_records)

    # Stage 8: Output writing
    csv_file_path = output_dir / "final_dataset.csv"
    logger.info("Writing %d final records to CSV: %s", total_final, csv_file_path)
    write_csv_dataset(csv_file_path, all_final_records)

    end_dt = datetime.now(timezone.utc)
    duration_sec = round(time.time() - start_time_sec, 2)

    # Reconciliation check: raw - rejected - duplicates == final
    is_reconciled = (total_raw - total_rejected - total_duplicates) == total_final

    summary_report = {
        "execution": {
            "start_time_utc": start_dt.isoformat(),
            "end_time_utc": end_dt.isoformat(),
            "duration_seconds": duration_sec,
        },
        "sources": source_stats,
        "overall": {
            "total_raw_collected": total_raw,
            "total_cleaned": total_cleaned,
            "total_rejected": total_rejected,
            "rejection_reasons": overall_rejection_counts,
            "total_duplicates_removed": total_duplicates,
            "total_final_records": total_final,
            "reconciliation": {
                "formula": "raw - rejected - duplicates == final",
                "calculated": f"{total_raw} - {total_rejected} - {total_duplicates} = {total_raw - total_rejected - total_duplicates}",
                "expected": total_final,
                "reconciled": is_reconciled,
            },
        },
    }

    report_file_path = output_dir / "summary_report.json"
    logger.info("Writing summary report to JSON: %s", report_file_path)
    write_summary_report(report_file_path, summary_report)

    logger.info("=" * 60)
    logger.info("Pipeline Execution Completed Successfully!")
    logger.info("Total Raw Scraped: %d", total_raw)
    logger.info("Total Rejected:    %d", total_rejected)
    logger.info("Total Duplicates:  %d", total_duplicates)
    logger.info("Total Final Saved: %d", total_final)
    logger.info("Reconciliation:    %s", "PASSED" if is_reconciled else "FAILED")
    logger.info("Execution Time:    %.2f seconds", duration_sec)
    logger.info("Outputs Generated: %s and %s", csv_file_path, report_file_path)
    logger.info("=" * 60)

    return summary_report


def main():
    """Parse command line arguments and execute the pipeline."""
    parser = argparse.ArgumentParser(
        description="Multi-Source Web Scraping & Data Consolidation ETL Pipeline"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save output files (default: output)",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/scraper.log"),
        help="Path to save scraper execution log (default: logs/scraper.log)",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.5,
        help="Delay in seconds between requests to prevent server overload (default: 0.5)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP request timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit per source for debugging/testing (default: None - all pages)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        choices=["both", "books", "quotes"],
        default="both",
        help="Sources to scrape (default: both)",
    )

    args = parser.parse_args()
    run_pipeline(
        output_dir=args.output_dir,
        log_file=args.log_file,
        rate_limit=args.rate_limit,
        timeout=args.timeout,
        max_pages=args.max_pages,
        sources_to_scrape=args.sources,
    )


if __name__ == "__main__":
    main()
