import pandas as pd


def transform_city_weather(location: dict,weather_payload: dict,) -> pd.DataFrame:
    """Transform one city's raw weather payload into a structured DataFrame.
    Returns:
        A DataFrame containing daily weather records enriched with location and
        date-related fields.

    Raises:
        ValueError: If the payload does not contain a valid ``daily`` object,
            the daily data cannot be converted to a DataFrame
        """
    daily = weather_payload.get("daily")

    if not isinstance(daily, dict):
        raise ValueError(
            f"Missing daily weather data for {location['city']}."
        )

    dataframe = pd.DataFrame(daily)

    dataframe["date"] = pd.to_datetime(
        dataframe["time"],
        errors="coerce",
    )

    dataframe = dataframe.drop(columns=["time"])

    dataframe["city"] = location["city"]
    dataframe["region"] = location["admin1"]
    dataframe["latitude"] = location["latitude"]
    dataframe["longitude"] = location["longitude"]
    dataframe["timezone"] = location["timezone"]

    dataframe["year"] = dataframe["date"].dt.year
    dataframe["month"] = dataframe["date"].dt.month
    dataframe["month_name"] = dataframe["date"].dt.month_name()
    dataframe["day_of_year"] = dataframe["date"].dt.dayofyear

    return dataframe

def create_monthly_summary(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Create monthly weather summaries for every city and year.

    Args:
        daily_weather: Cleaned daily weather DataFrame.

    Returns:
        Monthly summary DataFrame grouped by city, year, month, month name, and
        season."""
    return (
        daily_weather.groupby(
            ["city", "year", "month", "month_name", "season"],
            as_index=False,
        )
        .agg(
            average_temperature=("temperature_2m_mean", "mean"),
            average_high_temperature=("temperature_2m_max", "mean"),
            average_low_temperature=("temperature_2m_min", "mean"),
            total_precipitation=("precipitation_sum", "sum"),
            rainy_days=(
                "precipitation_sum",
                lambda values: (values > 1).sum(),
            ),
            average_max_wind_speed=("wind_speed_10m_max", "mean"),
            number_of_days=("date", "count"),
        )
    )

def create_city_summary(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Create overall weather statistics for each city.

    Args:
        daily_weather: Cleaned daily weather DataFrame.

    Returns:
        A city-level summary DataFrame covering the full extraction period."""
    return (
        daily_weather.groupby("city", as_index=False)
        .agg(
            average_temperature=("temperature_2m_mean", "mean"),
            average_high_temperature=("temperature_2m_max", "mean"),
            average_low_temperature=("temperature_2m_min", "mean"),
            total_precipitation=("precipitation_sum", "sum"),
            average_annual_precipitation=(
                "precipitation_sum",
                lambda values: values.sum() / 3,
            ),
            rainy_days=(
                "precipitation_sum",
                lambda values: (values > 1).sum(),
            ),
            average_max_wind_speed=("wind_speed_10m_max", "mean"),
            hottest_temperature=("temperature_2m_max", "max"),
            coldest_temperature=("temperature_2m_min", "min"),
            first_date=("date", "min"),
            last_date=("date", "max"),
            record_count=("date", "count"),
        )
    )

def clean_daily_weather(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Clean daily weather records and add analytical indicators.

    Args:
        daily_weather: Transformed daily weather DataFrame.

    Returns:
        A cleaned DataFrame sorted by city and date."""
    result = daily_weather.copy()

    result["date"] = pd.to_datetime(
        result["date"],
        errors="coerce",
    )

    numeric_columns = [
        "temperature_2m_mean",
        "temperature_2m_max",
        "temperature_2m_min",
        "precipitation_sum",
        "precipitation_hours",
        "wind_speed_10m_max",
    ]

    for column in numeric_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result["city"] = result["city"].str.strip()

    result = result.drop_duplicates(
        subset=["city", "date"],
        keep="first",
    )

    result["year"] = result["date"].dt.year
    result["month"] = result["date"].dt.month
    result["month_name"] = result["date"].dt.month_name()

    SEASON_MAP = {
        12: "Winter",
        1: "Winter",
        2: "Winter",

        3: "Spring",
        4: "Spring",
        5: "Spring",

        6: "Summer",
        7: "Summer",
        8: "Summer",

        9: "Autumn",
        10: "Autumn",
        11: "Autumn",
    }
    result["season"] = (
        result["month"]
        .map(SEASON_MAP)
    )

    result["is_rainy_day"] = (
        result["precipitation_sum"] > 1
    )

    result["daily_temperature_range"] = (
        result["temperature_2m_max"]
        - result["temperature_2m_min"]
    )

    result = result.sort_values(
        ["city", "date"]
    ).reset_index(drop=True)

    return result