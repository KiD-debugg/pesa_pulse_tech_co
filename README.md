# Customer Market Profile Analysis

This project summarizes customer locations and email top-level domains using records from the JSONPlaceholder users API. It exports a flattened customer table, a city-count table, and a chart to the `output/` directory.

> **Data note:** JSONPlaceholder is a sample API. Its user records are demonstration data, not verified or real customer information.

## Project files

```text
day1-api-analysis/
├── analysis.py
├── output/
│   ├── customers.csv
│   ├── city_counts.csv
│   └── customer_distribution.png
├── requirements.txt
└── README.md
```

## Approach

1. Request the user records from the API, using a timeout and reporting connection, timeout, and HTTP errors.
2. Inspect one record's field names and types, including nested address and company data.
3. Flatten customer, location, company, and email fields into a consistent table. Convert geographic coordinates to numbers where possible.
4. Count customers by city and by the final segment of their email domain (for example, `biz` in `april.biz`).
5. Write the flattened records and city counts to CSV files, and save a labelled chart of customer counts by city.

## Run the analysis

Use Python 3.10 or later. From the project directory, create and activate a virtual environment, install dependencies, and run the script.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python analysis.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python analysis.py
```

The script needs an internet connection to retrieve the API data. On success, it creates or updates these files under `output/`:

- `customers.csv` — one row per API record, with customer, contact, city, coordinate, company, and email TLD fields.
- `city_counts.csv` — customer count by city, sorted by count descending and then city name.
- `customer_distribution.png` — a bar chart of customer counts by city.

## Findings from the included output

- The API returned **10 sample customer records** across **10 distinct cities**.
- Each city appears once in this sample, so there is no single leading city.
- The most frequent email top-level domain is **`biz`**, with **3 of 10** addresses.

These findings describe the API response used to generate the included files; the response may change if the source data changes.

## Assumptions and limitations

- Each API record is treated as one customer; records are not deduplicated.
- A city is counted when its address contains a non-empty city string. Leading and trailing whitespace is removed, but spelling and letter case are otherwise preserved.
- An email top-level domain is taken as the text after the final dot in the email domain and is normalized to lowercase. Malformed or incomplete email values are excluded from domain counts.
- Missing nested address or company fields remain blank in the exported table. Invalid or missing coordinates are exported as blank values.
- The chart represents counts in the current API response; it does not imply a larger population distribution.
