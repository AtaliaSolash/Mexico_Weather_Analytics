# Mexico_Weather_Analytics
This project is an end-to-end AI-assisted data product built with **Python**, **Streamlit**, and the **Open-Meteo Weather API**.

The application analyzes historical weather data for multiple destinations in Mexico and provides business-oriented travel insights. Instead of presenting raw weather statistics, the dashboard helps users identify the best destinations and months to visit based on historical weather patterns.

The project demonstrates a complete data engineer workflow, including data extraction, transformation, validation, analytics, and interactive visualization.

### Selected API

**Open-Meteo Historical Weather API**

https://open-meteo.com/

Reasons for selecting this API:

- Completely free
- No API key required
- Historical weather data
- Reliable and well-documented

---

# Repository Structure

```
README.md
requirements.txt
app.py
etl.py

data/
    raw/
    processed/

ai_transcript/

src/
  api_client.py
  metrics.py
  transform.py
  validation.py        
```

# How to Run the Project

```bash
git clone https://github.com/AtaliaSolash/Mexico_Weather_Analytics.git
cd Mexico_Weather_Analytics
```
```bash
python -m venv .venv
```

### Windows
```bash
.venv\Scripts\activate
```
### macOS / Linux
```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```
```bash
python etl.py
```
```bash
streamlit run app.py
```

If activating the virtual environment fails in your computer, try instead:
```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe etl.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

---

# Data Model and ETL Pipeline

The ETL process follows the standard **Extract → Transform → Load** architecture.

## Extract
Historical daily weather data is retrieved from the Open-Meteo API for each selected destination.

The pipeline handles:
- API requests
- API failures
- Missing responses
- Raw data persistence

Raw API responses are stored under:
```
data/raw/
```
---

## Transform
The transformation layer performs:

- Data cleaning
- Type conversion
- Date parsing
- Monthly aggregation
- Seasonal categorization
- Tourism Weather Score calculation
- Analytical feature creation

The following processed datasets are generated:
### daily_weather.csv
Contains one row per destination and day including:
- temperatures
- precipitation
- wind speed
- tourism score

### monthly_weather_summary.csv
Monthly analytical summaries including:
- average temperatures
- precipitation
- rainy days
- tourism metrics

### data_quality.csv
Summary of all validation checks.

### extraction_status.csv
Execution status of every API request.

---

## Load
Processed datasets are stored locally in
```
data/processed/
```

---

# Dashboard Overview

## Month & Season Analysis

Provides high-level KPIs including:
- warmest month in destination
- rainest month in destination
- best month to travel in destination based on Tourism Score

The recommendation is based on a custom Tourism Score.
Each day receives one point for each of the following:
- Maximum temperature between **22°C and 30°C**
- Daily precipitation below **5 mm**
- Maximum wind speed below **30 km/h**

The daily score ranges from **0 to 3**.

Monthly recommendations are based on the average daily score across the latest available historical years.
This is a custom decision-support metric and **not an official tourism or meteorological metric**.
  
Visualizations:
- Monthly Average Temperature - Identify how temperature changes throughout the year so travel planners can recommend months with the most suitable temperatures.
- Monthly Rainy Days - Identify the driest months for travel planning. A lower number of rainy days indicates more favorable conditions for outdoor activities.

---

# Data Quality

The ETL pipeline performs several validation steps before creating the analytical datasets.

Implemented checks include:

- Missing values
- Duplicate records
- Invalid temperature ranges
- Invalid precipitation values
- Invalid wind speed values
- Missing destination names
- API extraction failures

Any detected issues are reported in:

```
data_quality.csv
```

and

```
extraction_status.csv
```

The dashboard also includes a dedicated **Data Quality** page that allows users to inspect these results.

---

# Assumptions and Known Limitations

## Assumptions

- A **rainy day** is defined as a day with **at least 1 mm** of precipitation.
- The **Tourism Weather Score** is a custom decision-support metric designed for this project. Each day receives one point for:
  - Maximum temperature between **22°C and 30°C**
  - Daily precipitation below **5 mm**
  - Maximum wind speed below **30 km/h**
- Travel recommendations are based solely on historical weather conditions and do not account for non-weather factors.
- Historical weather patterns from the selected period are assumed to be representative of typical seasonal conditions.


## Known Limitations

- The dashboard analyzes historical weather data only and does not provide weather forecasts.
- The Tourism Score is a custom heuristic rather than a validated scientific index.
- Recommendations do not consider additional travel factors such as accommodation prices, flight costs, holidays, local events, or traveler preferences.
- Results depend on the availability and completeness of the Open-Meteo historical dataset.
- The current implementation focuses exclusively on destinations in Mexico.

---

# AI Usage

AI was used throughout the assignment as a development assistant.

It assisted with:

- understanding and breaking down the assignment
- selecting the API
- designing the ETL pipeline
- improving the data model
- designing business-oriented analytics
- debugging Python and Streamlit issues
- reviewing dashboard usability
- refining business metrics

All AI-generated suggestions were manually reviewed, tested, and adapted before being incorporated into the final solution.

A transcript of the AI interaction is included in the repository under:

```
ai_transcript/
```

---

# Future Improvements

Given additional development time, several enhancements could be added:

- **Automated monitoring and alerting:** Send email notifications (or integrate with messaging services) when API requests fail or critical data quality issues are detected.
- **Automated ETL scheduling:** Schedule the ETL pipeline to run periodically (e.g., daily or weekly) using a scheduler.
- **Comprehensive unit testing:** Add automated tests for the ETL pipeline, data validation logic, and business metric calculations.
- **Additional weather indicators:** Incorporate humidity, UV index, sunshine duration, and other weather variables to improve travel recommendations.
  
---
