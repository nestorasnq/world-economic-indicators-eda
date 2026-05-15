# =============================================================================
# FILE: download_data.py
# PURPOSE: Fetch macroeconomic data from the World Bank API and save it
#          as a clean CSV file that we will use in our analysis notebook.
# HOW TO RUN: In your terminal, type:  python download_data.py
# =============================================================================
 
 
# --- IMPORTS -----------------------------------------------------------------
# These are Python libraries (pre-built toolboxes) we need to borrow.
# We installed them earlier with: pip install pandas requests
 
import requests   # "requests" lets Python talk to websites and APIs.
                  # We use it to download data from the World Bank.
 
import pandas as pd  # "pandas" is the main library for working with data tables.
                     # The alias "pd" is just a shortcut everyone uses by convention.
 
import os         # "os" lets Python interact with your operating system —
                  # in this case, we use it to create folders.
 
 
# --- CREATE OUTPUT FOLDER ----------------------------------------------------
# os.makedirs() creates a folder called "data" inside your project folder.
# exist_ok=True means: "don't crash if the folder already exists, just skip."
os.makedirs("data", exist_ok=True)
 
 
# --- DEFINE WHICH INDICATORS TO DOWNLOAD ------------------------------------
# A Python dictionary maps a "key" to a "value".
# Here each key is the World Bank's internal indicator code (a string ID
# their API uses), and each value is the friendly column name we want to use.
#
# World Bank indicator codes:
#   NY.GDP.PCAP.KD.ZG  = GDP per capita growth (annual %)
#   FP.CPI.TOTL.ZG     = Inflation based on Consumer Price Index (annual %)
#   SL.UEM.TOTL.ZS     = Unemployment rate (% of total labor force)
#   FR.INR.LEND        = Lending interest rate (%)
 
indicators = {
    "NY.GDP.PCAP.KD.ZG": "gdp_growth",
    "FP.CPI.TOTL.ZG":    "inflation",
    "SL.UEM.TOTL.ZS":    "unemployment",
    "FR.INR.LEND":        "interest_rate",
}
 
 
# --- DEFINE WHICH COUNTRIES TO DOWNLOAD -------------------------------------
# These are ISO 2-letter country codes the World Bank API understands.
# We chose 45 countries that represent a good mix of:
#   - G7 / developed economies (US, GB, DE, FR, IT, JP, CA)
#   - Emerging markets (BR, IN, CN, ZA, TR, NG, EG, SA, etc.)
#   - European economies (ES, GR, PT, PL, SE, NL, etc.)
 
countries = [
    "US","GB","DE","FR","IT","ES","GR","PT","JP","CN",
    "IN","BR","ZA","AU","CA","MX","KR","TR","RU","NG",
    "EG","SA","AR","ID","PL","SE","NL","BE","CH","NO",
    "DK","FI","IE","AT","NZ","SG","TH","MY","PH","CL",
    "CO","PE","HU","CZ","RO"
]
 
# The World Bank API accepts multiple countries in one request if we
# join them with semicolons: "US;GB;DE;FR;..." etc.
# ";".join(countries) does exactly that — it takes the list and glues
# each item together with a ";" separator between them.
country_str = ";".join(countries)
 
 
# --- DOWNLOAD LOOP -----------------------------------------------------------
# We will loop through each indicator, call the API once per indicator,
# and collect all the results into one big list called all_data.
 
all_data = []  # Start with an empty list. We'll append rows to this.
 
for code, name in indicators.items():
    # .items() lets us loop through a dictionary getting both the key (code)
    # and the value (name) at the same time.
    # Example first iteration: code = "NY.GDP.PCAP.KD.ZG", name = "gdp_growth"
 
    print(f"Downloading {name}...")
    # f"..." is an "f-string" — it lets you embed variables directly in text
    # using curly braces {}. So this prints e.g. "Downloading gdp_growth..."
 
    # Build the URL for the World Bank API request.
    # We use an f-string again to insert country_str and code dynamically.
    # Breakdown of URL parameters:
    #   format=json   → return data as JSON (a structured text format)
    #   per_page=2000 → return up to 2000 rows per request (enough for all country-years)
    #   mrv=23        → "most recent values" — get the last 23 years (2000-2022)
    url = (
        f"https://api.worldbank.org/v2/country/{country_str}/indicator/{code}"
        f"?format=json&per_page=2000&mrv=23"
    )
 
    # requests.get(url) sends an HTTP GET request to that URL,
    # exactly like your browser visiting a webpage — but Python does it.
    r = requests.get(url)
 
    # .json() parses the raw response text into a Python object.
    # The World Bank returns a list of 2 items:
    #   data[0] = metadata (page info, total count, etc.) — we don't need this
    #   data[1] = the actual list of data records — this is what we want
    data = r.json()
 
    # Safety check: if the API returned nothing useful, skip this indicator.
    if len(data) < 2:
        print(f"  Warning: no data returned for {name}")
        continue  # "continue" jumps to the next iteration of the for loop
 
    # Loop through each record in data[1].
    # Each record is a dictionary with info about one country in one year.
    for entry in data[1]:
 
        # Some entries have no value (the country didn't report that year).
        # We skip those using "is not None" — None means "empty/missing" in Python.
        if entry["value"] is not None:
 
            # Append a new dictionary (one row of data) to our all_data list.
            # We extract the fields we care about from the entry dictionary.
            all_data.append({
                "country":      entry["country"]["value"],   # Full country name e.g. "Germany"
                "country_code": entry["countryiso3code"],    # 3-letter code e.g. "DEU"
                "year":         int(entry["date"]),          # Year as integer e.g. 2015
                                                             # int() converts "2015" string → 2015 number
                "indicator":    name,                        # e.g. "gdp_growth"
                "value":        float(entry["value"])        # The actual number e.g. 1.8
                                                             # float() ensures it's a decimal number
            })
 
 
# --- BUILD A DATAFRAME -------------------------------------------------------
# pd.DataFrame(all_data) converts our list of dictionaries into a pandas
# DataFrame — which is like an Excel spreadsheet inside Python.
# Each dictionary in the list becomes one row.
df_long = pd.DataFrame(all_data)
 
# Right now our data is in "long format":
#   country | country_code | year | indicator    | value
#   Germany |     DEU      | 2015 | gdp_growth   | 1.53
#   Germany |     DEU      | 2015 | inflation    | 0.71
#   Germany |     DEU      | 2015 | unemployment | 4.62
#   ...
#
# We want "wide format" instead — one row per country per year,
# with separate columns for each indicator:
#   country | country_code | year | gdp_growth | inflation | unemployment | interest_rate
#   Germany |     DEU      | 2015 |    1.53    |   0.71    |     4.62     |    ...
#
# pivot_table() does this transformation:
#   index   = the columns that identify each unique row (country + year)
#   columns = the column whose values become new column headers (the indicator names)
#   values  = the numbers to fill into those new columns
 
df_wide = df_long.pivot_table(
    index=["country", "country_code", "year"],
    columns="indicator",
    values="value"
).reset_index()
# .reset_index() moves the index back into regular columns so country/year
# are just normal columns again, not special index labels.
 
# After pivot_table, pandas adds a "name" label to the column axis.
# This line removes that label so it doesn't interfere with anything later.
df_wide.columns.name = None
 
 
# --- SAVE TO CSV -------------------------------------------------------------
# .to_csv() saves the DataFrame as a comma-separated values file.
# index=False means: don't write the row numbers (0,1,2,...) as a column.
df_wide.to_csv("data/macro_indicators.csv", index=False)
 
# Print a confirmation message so we know it worked.
print(f"\nDone. Dataset saved to data/macro_indicators.csv")
print(f"Shape: {df_wide.shape}")
# .shape returns (number_of_rows, number_of_columns) as a tuple.
# e.g. (850, 7) means 850 rows and 7 columns.
 
# .head() shows the first 5 rows of the DataFrame — a quick sanity check.
print(df_wide.head())