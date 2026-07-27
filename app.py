from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROCESSED_DIR = Path("data/processed")

REQUIRED_FILES = {
    "daily_weather": "daily_weather.csv",
    "monthly_summary": "monthly_weather_summary.csv",
    "quality_report": "data_quality.csv",
    "extraction_status": "extraction_status.csv",
}

SEASON_ORDER = [
    "Winter",
    "Spring",
    "Summer",
    "Autumn",
]

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

MONTH_ORDER = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December"
]

def configure_page() -> None:
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="Mexico Weather Tourism Dashboard",
        page_icon="☀️",
        layout="wide",
    )


@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    """Load one processed CSV file."""
    file_path = PROCESSED_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Required processed file was not found: {file_path}"
        )

    return pd.read_csv(file_path)


def load_data() -> dict[str, pd.DataFrame]:
    """Load and prepare all processed datasets."""
    data = {
        name: load_csv(filename)
        for name, filename in REQUIRED_FILES.items()
    }

    daily_weather = data["daily_weather"]

    if "date" in daily_weather.columns:
        daily_weather["date"] = pd.to_datetime(
            daily_weather["date"],
            errors="coerce",
        )

    for dataframe_name in [
        "daily_weather",
        "monthly_summary",
    ]:
        dataframe = data[dataframe_name]

        if "year" in dataframe.columns:
            dataframe["year"] = pd.to_numeric(
                dataframe["year"],
                errors="coerce",
            ).astype("Int64")

    return data


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    """Stop the app when a required column is missing."""
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{dataset_name} is missing required columns: "
            f"{', '.join(missing_columns)}"
        )


def create_sidebar_filters(daily_weather: pd.DataFrame,) -> list[str]:
    """Create destination and year filters."""
    validate_required_columns(
        daily_weather,
        ["city", "year"],
        "daily_weather.csv",
    )

    st.sidebar.header("Filters")

    available_cities = sorted(
        daily_weather["city"].dropna().astype(str).unique()
    )

    available_years = sorted(
        daily_weather["year"].dropna().astype(int).unique()
    )

    selected_cities = st.sidebar.multiselect(
        "Select destinations",
        options=available_cities,
        default=available_cities,
    )

    if not selected_cities:
        st.warning("Select at least one destination.")
        st.stop()

    return selected_cities


def filter_data(
    data: dict[str, pd.DataFrame],
    selected_cities: list[str]
) -> dict[str, pd.DataFrame]:
    """Apply the sidebar filters to all analytical datasets."""
    daily_weather = data["daily_weather"]
    monthly_summary = data["monthly_summary"]

    filtered_daily = daily_weather[
        daily_weather["city"].isin(selected_cities)
    ].copy()

    filtered_monthly = monthly_summary[
        monthly_summary["city"].isin(selected_cities)
    ].copy()


    return {
        "daily": filtered_daily,
        "monthly": filtered_monthly,
    }


def render_header() -> None:
    """Render the app title and product description."""
    st.title("Mexico Weather Tourism Dashboard")

    st.write(
        """
        This dashboard analyzes three years of historical weather data
        across selected Mexican destinations to support tourism and
        travel-planning decisions.
        """
    )

    with st.expander("How is the tourism score calculated?"):
        st.write(
            """
            Each day receives one point for each of the following:

            - Maximum temperature between 22°C and 30°C
            - Daily precipitation below 5 mm
            - Maximum wind speed below 30 km/h

            The final score ranges from 0 to 3. This is a custom
            decision-support metric and not an official tourism or
            meteorological index.
            """
        )


def show_data_quality(
    quality_report: pd.DataFrame,
    extraction_status: pd.DataFrame,
) -> None:
    """Render validation and extraction status."""
    st.header("Data Quality and Pipeline Status")

    validate_required_columns(
        quality_report,
        ["check_name", "status", "failed_rows", "description"],
        "data_quality.csv",
    )

    validate_required_columns(
        extraction_status,
        ["city", "status"],
        "extraction_status.csv",
    )

    passed_checks = (
        quality_report["status"].astype(str).str.upper() == "PASS"
    ).sum()

    warning_checks = (
        quality_report["status"].astype(str).str.upper() == "WARNING"
    ).sum()

    failed_checks = (
        quality_report["status"].astype(str).str.upper() == "FAIL"
    ).sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("Passed Checks", int(passed_checks))
    col2.metric("Warnings", int(warning_checks))
    col3.metric("Failed Checks", int(failed_checks))

    if failed_checks > 0:
        st.error(
            "Some data-quality checks failed. Review the table below."
        )
    elif warning_checks > 0:
        st.warning(
            "The data passed critical checks, but some warnings were found."
        )
    else:
        st.success("All data-quality checks passed.")

    st.subheader("Validation Results")

    st.dataframe(
        quality_report,
        use_container_width=True,
        hide_index=True,
    )

    successful_extractions = (
        extraction_status["status"]
        .astype(str)
        .str.upper()
        .eq("SUCCESS")
        .sum()
    )

    failed_extractions = (
        extraction_status["status"]
        .astype(str)
        .str.upper()
        .eq("FAILED")
        .sum()
    )

    st.subheader("API Extraction Status")

    col1, col2 = st.columns(2)

    col1.metric(
        "Successful Extractions",
        int(successful_extractions),
    )
    col2.metric(
        "Failed Extractions",
        int(failed_extractions),
    )

    st.dataframe(
        extraction_status,
        use_container_width=True,
        hide_index=True,
    )

    if failed_extractions > 0:
        failed_cities = extraction_status.loc[
            extraction_status["status"]
            .astype(str)
            .str.upper()
            .eq("FAILED"),
            "city",
        ].astype(str).tolist()

        st.error(
            "API extraction failed for: "
            + ", ".join(failed_cities)
        )

def show_month_and_season(
    filtered_daily: pd.DataFrame,
    filtered_monthly: pd.DataFrame,
    selected_cities: list[str],
) -> None:
    """Show monthly patterns and the driest month/season by destination."""

    st.header("Month and Season Analysis")

    selected_city = st.selectbox(
        "Choose a destination",
        options=selected_cities,
        key="month_season_city",
    )

    city_daily = filtered_daily[
        filtered_daily["city"] == selected_city
    ].copy()

    city_monthly = filtered_monthly[
        filtered_monthly["city"] == selected_city
        ].copy()


    if city_daily.empty or city_monthly.empty:
        st.warning(
            "No data is available for the selected destination."
        )
        return

    # =====================================================
    # 1. Monthly average temperature
    # =====================================================

    historical_monthly_temperature = (
        city_monthly.groupby(
            ["month", "month_name"],
            as_index=False,
        )
        .agg(
            average_temperature=(
                "average_temperature",
                "mean",
            )
        )
        .sort_values("month")
    )

    warmest_month = historical_monthly_temperature.loc[
        historical_monthly_temperature[
            "average_temperature"
        ].idxmax()
    ]

    # Calculate the average tourism score for each month
    monthly_tourism_summary = (
        city_monthly.groupby(
            ["month", "month_name"],
            as_index=False,
        )
        .agg(
            average_tourism_score=(
                "average_tourism_score",
                "mean",
            ),
            average_temperature=(
                "average_temperature",
                "mean",
            ),
            average_rainy_days=(
                "rainy_days",
                "mean",
            ),
            average_max_wind_speed=(
                "average_max_wind_speed",
                "mean",
            ),
        )
        .sort_values("month")
    )


    # Choose the month with the highest average tourism score
    recommended_month = (
        monthly_tourism_summary.sort_values(
            [
                "average_tourism_score",
                "average_rainy_days",
                "average_max_wind_speed",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .iloc[0]
    )

    # =====================================================
    # 2. Monthly precipitation
    # =====================================================

    historical_monthly_precipitation = (
        city_monthly.groupby(
            ["month", "month_name"],
            as_index=False,
        )
        .agg(
            average_monthly_precipitation=(
                "total_precipitation",
                "mean",
            )
        )
        .sort_values("month")
    )

    rainiest_month = historical_monthly_precipitation.loc[
        historical_monthly_precipitation[
            "average_monthly_precipitation"
        ].idxmax()
    ]
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Warmest Month",
            warmest_month["month_name"],
            f"{warmest_month['average_temperature']:.1f}°C",
            delta_color='yellow',
            delta_arrow = "off"
        )

    with col2:
        st.metric(
            "Rainiest Month",
            rainiest_month["month_name"],
            f"{rainiest_month['average_monthly_precipitation']:.1f} mm",
            delta_color='yellow',
            delta_arrow="off"
        )

    with col3:
        st.metric(
            label="Best Month to Visit",
            value=str(recommended_month["month_name"]),
            delta=f"Tourism score: {recommended_month['average_tourism_score']:.2f}/3",
            delta_color='yellow',
            delta_arrow="off"

        )

        st.caption(
            f"🌡 Average temperature: "
            f"{recommended_month['average_temperature']:.1f}°C\n"
            f"\n🌧 Average rainy days: "
            f"{recommended_month['average_rainy_days']:.1f}\n"
            f"\n💨 Average wind speed: "
            f"{recommended_month['average_max_wind_speed']:.1f} km/h"
        )
    st.markdown("---")

    st.subheader("Monthly Average Temperature")

    st.caption(
        "Business goal: Identify how temperature changes throughout "
        "the year so travel planners can recommend months with the "
        "most suitable temperatures."
    )
    monthly_temperature_average = (
        city_monthly.groupby(
            ["month", "month_name"],
            as_index=False,
        )
        .agg(
            average_temperature=(
                "average_temperature",
                "mean",
            )
        )
        .sort_values("month")
    )
    monthly_temperature_chart = px.line(
        monthly_temperature_average,
        x="month_name",
        y="average_temperature",
        markers=True,
        text="average_temperature",
        title=f"Historical Monthly Average Temperature — {selected_city}",
        labels={
            "month_name": "Month",
            "average_temperature": "Temperature (°C)",
        },
        category_orders={
            "month_name": MONTH_ORDER,
        },
    )
    monthly_temperature_chart.update_traces(
        texttemplate="%{text:.1f}°",
        textposition="top center",
        hovertemplate=None,
        hoverinfo="skip",
    )

    monthly_temperature_chart.update_layout(
        hovermode=False,
    )
    st.plotly_chart(
        monthly_temperature_chart,
        use_container_width=True,
    )

    st.markdown("---")


    st.subheader("Monthly Rainy Days")

    st.caption(
        "Business goal: Identify the driest months for travel planning. "
        "A lower number of rainy days indicates more favorable conditions "
        "for outdoor activities."
    )

    # First calculate metrics separately for every year and month
    monthly_rain_summary = (
        city_monthly.groupby(
            [
                "month",
                "month_name",
            ],
            as_index=False,
        )
        .agg(
            average_rainy_days=(
                "rainy_days",
                "mean",
            ),
            average_monthly_precipitation=(
                "total_precipitation",
                "mean",
            ),
            average_tourism_score=(
                "average_tourism_score",
                "mean",
            ),
        )
        .sort_values("month")
    )

    # Identify the driest month according to rainy-day count
    driest_month = monthly_rain_summary.loc[
        monthly_rain_summary[
            "average_rainy_days"
        ].idxmin()
    ]

    st.metric(
        label="Driest Month",
        value=str(driest_month["month_name"]),
        delta=f"{driest_month['average_rainy_days']:.1f} rainy days on average",
        delta_color='yellow',
        delta_arrow="off"
    )

    precipitation_chart = px.bar(
        monthly_rain_summary,
        x="month_name",
        y="average_rainy_days",
        title=(
            f"Average Monthly Rainy Days — {selected_city}"
        ),
        labels={
            "month_name": "Month",
            "average_rainy_days": "Average Rainy Days",
        },
        category_orders={
            "month_name": MONTH_ORDER,
        },
        custom_data=[
            "average_monthly_precipitation",
            "average_tourism_score",

        ],
    )

    # Show a value above each bar
    precipitation_chart.update_traces(
        text=monthly_rain_summary[
            "average_rainy_days"
        ].round(1),
        texttemplate="%{text:.1f}",
        textposition="outside",
        hovertemplate=(
            "Average rainy days: %{y:.1f}<br>"
            "Average precipitation: %{customdata[0]:.1f} mm<br>"
            "Average tourism score: %{customdata[1]:.2f}/3"
            "<extra></extra>"
        ),
    )
    precipitation_chart.update_layout(
        hovermode="x unified"
    )
    precipitation_chart.update_yaxes(
        title="Average Number of Rainy Days",
        rangemode="tozero",
    )

    st.plotly_chart(
        precipitation_chart,
        use_container_width=True,
    )


def main() -> None:
    """Run the Streamlit application."""
    configure_page()
    render_header()

    try:
        data = load_data()

        selected_cities = create_sidebar_filters(
            data["daily_weather"]
        )

        filtered_data = filter_data(
            data=data,
            selected_cities=selected_cities
        )

    except FileNotFoundError as error:
        st.error(str(error))
        st.info(
            "Run `python etl.py` before starting the Streamlit app."
        )
        st.stop()

    except ValueError as error:
        st.error(f"Processed data validation error: {error}")
        st.stop()

    except Exception as error:
        st.error(f"Could not initialize the dashboard: {error}")
        st.stop()

    month_season_tab, quality_tab = st.tabs(
        [
            "Month and Season",
            "Data Quality",
        ]
    )

    with month_season_tab:
        show_month_and_season(
            filtered_daily=filtered_data["daily"],
            filtered_monthly=filtered_data["monthly"],
            selected_cities=selected_cities,
        )

    with quality_tab:
        show_data_quality(
            quality_report=data["quality_report"],
            extraction_status=data["extraction_status"],
        )


if __name__ == "__main__":
    main()