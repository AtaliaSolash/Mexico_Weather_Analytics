import pandas as pd

def add_daily_metrics(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Add daily business and weather indicators.

    Args:
        daily_weather: Cleaned daily weather DataFrame.

    Returns:
        A copy of the input DataFrame enriched with derived daily metrics."""
    result = daily_weather.copy()

    result["daily_temperature_range"] = (
        result["temperature_2m_max"]
        - result["temperature_2m_min"]
    )

    result["is_rainy_day"] = (
        result["precipitation_sum"] > 1
    )

    result["is_heavy_rain_day"] = (
        result["precipitation_sum"] >= 20
    )

    result["is_hot_day"] = (
        result["temperature_2m_max"] >= 32
    )

    result["is_comfortable_day"] = (
        result["temperature_2m_max"].between(22, 30)
    )

    result["is_low_wind_day"] = (
        result["wind_speed_10m_max"] < 30
    )

    return result

def add_tourism_score(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Calculate the custom Tourism Score.

    The score ranges from 0 to 3 and awards one point for each condition:
    comfortable maximum temperature, low precipitation, and moderate wind.

    Returns:
        A copy enriched with component scores and the total tourism score."""
    result = daily_weather.copy()

    result["comfortable_temperature_score"] = (
        result["temperature_2m_max"]
        .between(22, 30)
        .astype(int)
    )

    result["low_rain_score"] = (
        result["precipitation_sum"] < 5
    ).astype(int)

    result["moderate_wind_score"] = (
        result["wind_speed_10m_max"] < 30
    ).astype(int)

    result["tourism_weather_score"] = (
        result["comfortable_temperature_score"]
        + result["low_rain_score"]
        + result["moderate_wind_score"]
    )

    return result

def add_tourism_segments(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Categorize Tourism Scores into categories.

        Args:
            daily_weather: Daily weather DataFrame containing
                ``tourism_weather_score``.

        Returns:
            A copy with a categorical ``tourism_weather_segment`` column.
        """
    result = daily_weather.copy()

    result["tourism_weather_category"] = pd.cut(
        result["tourism_weather_score"],
        bins=[-1, 0, 1, 2, 3],
        labels=[
            "Poor",
            "Limited",
            "Good",
            "Excellent",
        ],
    )

    return result

def create_monthly_summary(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """Create historical monthly analytical summaries by city, year and month.

    Args:
        daily_weather: Daily analytics DataFrame containing derived metrics and
            tourism scores.

    Returns:
        Monthly weather summary grouped by city, year, and month.
    """
    monthly_summary = (
        daily_weather.groupby(
            [
                "city",
                "year",
                "month",
                "month_name",
            ],
            as_index=False,
        )
        .agg(
            average_temperature=(
                "temperature_2m_mean",
                "mean",
            ),
            average_high_temperature=(
                "temperature_2m_max",
                "mean",
            ),
            average_low_temperature=(
                "temperature_2m_min",
                "mean",
            ),
            average_temperature_range=(
                "daily_temperature_range",
                "mean",
            ),
            total_precipitation=(
                "precipitation_sum",
                "sum",
            ),
            rainy_days=(
                "is_rainy_day",
                "sum",
            ),
            heavy_rain_days=(
                "is_heavy_rain_day",
                "sum",
            ),
            hot_days=(
                "is_hot_day",
                "sum",
            ),
            comfortable_days=(
                "is_comfortable_day",
                "sum",
            ),
            average_max_wind_speed=(
                "wind_speed_10m_max",
                "mean",
            ),
            average_tourism_score=(
                "tourism_weather_score",
                "mean",
            ),
            number_of_days=(
                "date",
                "count",
            ),
        )
    )

    percentage_columns = {
        "rainy_day_percentage": "rainy_days",
        "hot_day_percentage": "hot_days",
        "comfortable_day_percentage": "comfortable_days",
    }

    for output_column, source_column in percentage_columns.items():
        monthly_summary[output_column] = (
            monthly_summary[source_column]
            / monthly_summary["number_of_days"]
            * 100
        )

    return monthly_summary

def create_tourism_monthly_summary(daily_weather: pd.DataFrame,) -> pd.DataFrame:
    """returns a summary across all available years for every city and month."""
    summary = (
        daily_weather.groupby(
            [
                "city",
                "month",
                "month_name",
            ],
            as_index=False,
        )
        .agg(
            average_temperature=(
                "temperature_2m_mean",
                "mean",
            ),
            average_high_temperature=(
                "temperature_2m_max",
                "mean",
            ),
            average_low_temperature=(
                "temperature_2m_min",
                "mean",
            ),
            average_daily_precipitation=(
                "precipitation_sum",
                "mean",
            ),
            average_max_wind_speed=(
                "wind_speed_10m_max",
                "mean",
            ),
            rainy_days=(
                "is_rainy_day",
                "sum",
            ),
            comfortable_days=(
                "is_comfortable_day",
                "sum",
            ),
            excellent_weather_days=(
                "tourism_weather_score",
                lambda values: (values == 3).sum(),
            ),
            average_tourism_score=(
                "tourism_weather_score",
                "mean",
            ),
            total_observed_days=(
                "date",
                "count",
            ),
        )
    )

    summary["rainy_day_percentage"] = (
        summary["rainy_days"]
        / summary["total_observed_days"]
        * 100
    )

    summary["comfortable_day_percentage"] = (
        summary["comfortable_days"]
        / summary["total_observed_days"]
        * 100
    )

    summary["excellent_weather_percentage"] = (
        summary["excellent_weather_days"]
        / summary["total_observed_days"]
        * 100
    )

    return summary.sort_values(
        ["city", "month"]
    ).reset_index(drop=True)


def build_analytics(daily_weather: pd.DataFrame,) -> dict[str, pd.DataFrame]:
    """Run the complete analytical pipeline.

       Args:
           daily_weather: Cleaned daily weather DataFrame.

       Returns:
           Dictionary containing enriched daily data, historical monthly weather
           summaries, and multi-year tourism monthly summaries."""
    daily_analytics = add_daily_metrics(daily_weather)
    daily_analytics = add_tourism_score(daily_analytics)
    daily_analytics = add_tourism_segments(daily_analytics)

    monthly_summary = create_monthly_summary(
        daily_analytics
    )

    tourism_monthly_summary = (
        create_tourism_monthly_summary(
            daily_analytics
        )
    )

    return {
        "daily_weather": daily_analytics,
        "monthly_weather_summary": monthly_summary,
        "tourism_monthly_summary":
            tourism_monthly_summary,
    }