import pandas as pd


def create_result(check_name, status, failed_rows, description):
    """Create a standardized validation result dictionary.

        Args:
            check_name: Human-readable validation check name.
            status: Validation status, typically PASS, WARNING, or FAIL.
            failed_rows: Number of rows or entities that failed the check.
            description: Explanation of the validation outcome.

        Returns:
            A dictionary suitable for conversion into a tabular report.
        """
    return {
        "check_name": check_name,
        "status": status,
        "failed_rows": failed_rows,
        "description": description,
    }

def check_missing_values(df):
    """Check required columns for missing values."""

    required_columns = [
        "city",
        "date",
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
    ]

    results = []

    for column in required_columns:
        missing = df[column].isna().sum()

        results.append(
            create_result(
                f"Missing values in {column}",
                "PASS" if missing == 0 else "FAIL",
                int(missing),
                f"{column} should not contain missing values."
            )
        )

    return results


def check_duplicates(df):
    """Every city should have one row per date."""
    duplicates = df.duplicated(
        subset=["city", "date"]
    ).sum()

    return create_result(
        "Duplicate city-date rows",
        "PASS" if duplicates == 0 else "FAIL",
        int(duplicates),
        "Each city should have only one record per day."
    )

def check_temperature_range(df):
    """ Maximum temperature should never be lower than minimum temperature."""
    invalid = (
        df["temperature_2m_max"]
        < df["temperature_2m_min"]
    ).sum()

    return create_result(
        "Temperature range",
        "PASS" if invalid == 0 else "FAIL",
        int(invalid),
        "Maximum temperature must be greater than minimum temperature."
    )

def check_precipitation(df):
    """Rainfall cannot be negative."""
    invalid = (
        df["precipitation_sum"] < 0
    ).sum()

    return create_result(
        "Negative precipitation",
        "PASS" if invalid == 0 else "FAIL",
        int(invalid),
        "Precipitation cannot be negative."
    )

def check_wind_speed(df):
    """Verify that maximum wind speeds are non-negative."""

    invalid = (
        df["wind_speed_10m_max"] < 0
    ).sum()

    return create_result(
        "Negative wind speed",
        "PASS" if invalid == 0 else "FAIL",
        int(invalid),
        "Wind speed cannot be negative."
    )

def check_expected_cities(df):
    """Verify that all required Mexican cities are represented."""

    EXPECTED_CITIES = {
        "Mexico City",
        "Cancun",
        "Tulum",
        "Puerto Vallarta",
        "Cabo San Lucas",
        "Oaxaca",
    }
    actual = set(df["city"].unique())

    missing = EXPECTED_CITIES - actual

    return create_result(
        "Expected cities",
        "PASS" if len(missing) == 0 else "FAIL",
        len(missing),
        f"Missing cities: {', '.join(sorted(missing))}"
        if missing else "All expected cities found."
    )

def check_record_count(df):
    """Each city should have approximately 1,096 daily records for 2023–2025."""
    EXPECTED_ROWS = 1096
    results = []

    counts = df.groupby("city").size()

    for city, count in counts.items():

        difference = abs(count - EXPECTED_ROWS)

        status = "PASS"

        if difference > 10:
            status = "WARNING"

        results.append(
            create_result(
                f"Record count - {city}",
                status,
                difference,
                f"{count} rows found."
            )
        )

    return results

def run_quality_checks(df):
    """Run all weather-data validation checks."""
    checks = []

    checks.extend(check_missing_values(df))

    checks.append(check_duplicates(df))

    checks.append(check_temperature_range(df))

    checks.append(check_precipitation(df))

    checks.append(check_wind_speed(df))

    checks.append(check_expected_cities(df))

    checks.extend(check_record_count(df))

    return pd.DataFrame(checks)