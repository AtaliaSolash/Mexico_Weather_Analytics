import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from src.api_client import (
    geocode_city,
    get_historical_weather,
)
from src.transform import transform_city_weather, clean_daily_weather, create_monthly_summary

from src.validation import run_quality_checks
from src.metrics import build_analytics

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

CITIES = [
    "Mexico City",
    "Cancun",
    "Tulum",
    "Puerto Vallarta",
    "Cabo San Lucas",
    "Oaxaca",
]

def extract_all_cities() -> tuple[list[dict], pd.DataFrame]:
    extracted_data = []
    extraction_status = []

    for city in CITIES:
        started_at = datetime.now(timezone.utc)

        try:
            print(f"Resolving {city}...")
            location = geocode_city(city)

            print(f"Downloading historical weather for {city}...")
            weather = get_historical_weather(
                latitude=location["latitude"],
                longitude=location["longitude"],
                timezone=location["timezone"],
            )

            daily_data = weather.get("daily", {})
            dates = daily_data.get("time", [])

            if not dates:
                raise ValueError(
                    f"The API returned no daily records for {city}."
                )

            city_result = {
                "location": location,
                "weather": weather,
            }

            extracted_data.append(city_result)

            filename = city.lower().replace(" ", "_")
            raw_path = RAW_DIR / f"{filename}.json"

            with raw_path.open("w", encoding="utf-8") as file:
                json.dump(
                    city_result,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            completed_at = datetime.now(timezone.utc)

            extraction_status.append(
                {
                    "city": city,
                    "status": "SUCCESS",
                    "record_count": len(dates),
                    "error_type": None,
                    "error_message": None,
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "raw_file": str(raw_path),
                }
            )

            print(
                f"Successfully extracted {len(dates)} "
                f"daily records for {city}."
            )

        except Exception as error:
            completed_at = datetime.now(timezone.utc)

            extraction_status.append(
                {
                    "city": city,
                    "status": "FAILED",
                    "record_count": 0,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "raw_file": None,
                }
            )

            print(f"Failed to process {city}: {error}")

    status_df = pd.DataFrame(extraction_status)

    return extracted_data, status_df


def transform_all_cities(
    extracted_data: list[dict],
) -> pd.DataFrame:
    weather_frames = []

    for city_result in extracted_data:
        city_dataframe = transform_city_weather(
            location=city_result["location"],
            weather_payload=city_result["weather"],
        )

        weather_frames.append(city_dataframe)

    if not weather_frames:
        raise RuntimeError(
            "No weather datasets were available for transformation."
        )

    daily_weather = pd.concat(
        weather_frames,
        ignore_index=True,
    )

    return daily_weather

def print_etl_summary(
    extraction_status: pd.DataFrame,
    quality_report: pd.DataFrame,
) -> None:
    """Print a clear ETL execution summary."""

    successful_extractions = int(
        extraction_status["status"]
        .astype(str)
        .str.upper()
        .eq("SUCCESS")
        .sum()
    )

    failed_extractions = int(
        extraction_status["status"]
        .astype(str)
        .str.upper()
        .eq("FAILED")
        .sum()
    )

    passed_checks = int(
        quality_report["status"]
        .astype(str)
        .str.upper()
        .eq("PASS")
        .sum()
    )

    warning_checks = int(
        quality_report["status"]
        .astype(str)
        .str.upper()
        .eq("WARNING")
        .sum()
    )

    failed_checks = int(
        quality_report["status"]
        .astype(str)
        .str.upper()
        .eq("FAIL")
        .sum()
    )

    print()
    print("=" * 60)
    print("ETL EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Successful API extractions: {successful_extractions}")
    print(f"Failed API extractions:     {failed_extractions}")
    print(f"Passed quality checks:      {passed_checks}")
    print(f"Quality warnings:           {warning_checks}")
    print(f"Failed quality checks:      {failed_checks}")

    if failed_extractions > 0:
        failed_cities = extraction_status.loc[
            extraction_status["status"]
            .astype(str)
            .str.upper()
            .eq("FAILED"),
            "city",
        ].astype(str).tolist()

        print()
        print("API failures:")
        for city in failed_cities:
            print(f"  - {city}")

    if failed_checks > 0:
        failed_quality_checks = quality_report.loc[
            quality_report["status"]
            .astype(str)
            .str.upper()
            .eq("FAIL"),
            "check_name",
        ].astype(str).tolist()

        print()
        print("Failed data-quality checks:")
        for check_name in failed_quality_checks:
            print(f"  - {check_name}")

    print("=" * 60)

def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Starting weather ETL pipeline...")

    extracted_data, extraction_status = extract_all_cities()

    extraction_status.to_csv(
        PROCESSED_DIR / "extraction_status.csv",
        index=False,
    )

    print("\nTransforming weather data...")
    daily_weather = transform_all_cities(extracted_data)

    daily_weather = clean_daily_weather(daily_weather)

    monthly_summary = create_monthly_summary(daily_weather)

    daily_weather.to_csv(
        PROCESSED_DIR / "daily_weather.csv",
        index=False,
    )

    monthly_summary.to_csv(
        PROCESSED_DIR / "monthly_weather_summary.csv",
        index=False,
    )

    quality = run_quality_checks(daily_weather)

    quality.to_csv(
        PROCESSED_DIR / "data_quality.csv",
        index=False,
    )
    print()
    print_etl_summary(
        extraction_status=extraction_status,
        quality_report=quality,
    )
    print(f"Cities processed: {daily_weather['city'].nunique()}")
    print(f"Total daily records: {len(daily_weather)}")

    analytics = build_analytics(daily_weather)

    for filename, dataframe in analytics.items():
        output_path = (
                PROCESSED_DIR / f"{filename}.csv"
        )

        dataframe.to_csv(
            output_path,
            index=False,
        )

        print(
            f"Saved {filename}: "
            f"{len(dataframe)} rows"
        )


if __name__ == "__main__":
    main()