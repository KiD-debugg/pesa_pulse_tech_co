"""
Customer Market Profile Analysis

Summarizes customer locations and email domains from the customer API,
then exports an analysis-ready dataset and a customer distribution chart.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests

# Keep the endpoint and output location in one place so the source can be
# changed without editing the analysis and export steps below.
API_URL = "https://jsonplaceholder.typicode.com/users"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def get_customers(url: str = API_URL) -> list[dict]:
    """Retrieve customer records; return an empty list if the request fails."""
    try:
        # A timeout prevents an unavailable service from leaving the analysis waiting indefinitely.
        response = requests.get(url, timeout=10)
        # Convert unsuccessful HTTP status codes into a handled request error.
        response.raise_for_status()
        customers = response.json()
        # Validate the top-level response shape before later steps treat it as a list.
        if not isinstance(customers, list):
            print("Error: The API response did not contain a customer list.")
            return []
        return customers
    except requests.exceptions.ConnectionError:
        print("Error: Failed to connect to the API server. Check your network connection.")
    except requests.exceptions.Timeout:
        print("Error: The request timed out while waiting for the API server.")
    except requests.exceptions.HTTPError as err:
        print(f"Error: The API returned an HTTP failure status: {err}")
    except requests.exceptions.RequestException as err:
        print(f"Error: An unexpected error occurred while connecting to the API: {err}")
    return []


def explore(record: dict, indent: int = 0) -> None:
    """Print the fields and value types in a customer record, including nested dictionaries."""
    for key, value in record.items():
        # Indentation makes nested fields easier to distinguish in the console output.
        print(f"{' ' * indent}{key}: {type(value).__name__}")
        # Address and company details are nested objects in the API response.
        if isinstance(value, dict):
            explore(value, indent + 4)


def _coordinate(value: object) -> float | None:
    """Convert an API coordinate to a numeric value, leaving invalid values blank."""
    # API coordinates are usually numeric strings; reject other object types before conversion.
    if not isinstance(value, (int, float, str)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_attributes(customers: list[dict]) -> list[dict]:
    """Flatten customer, address, and company fields into analysis-ready records."""
    rows = []
    for customer in customers:
        # Nested objects may be missing or null, so use empty dictionaries for safe field access.
        address = customer.get("address") or {}
        geo = address.get("geo") or {}
        company = customer.get("company") or {}
        email = str(customer.get("email") or "").strip()
        # Capture the email's final domain segment (for example, "biz" in "april.biz").
        domain = email.rpartition("@")[2]
        email_domain = domain.rpartition(".")[2].lower() if "." in domain else ""

        # Use a fixed column schema so every exported row has consistent fields and ordering.
        rows.append(
            {
                "customer_id": customer.get("id"),
                "name": customer.get("name"),
                "username": customer.get("username"),
                "email": email,
                "email_domain": email_domain,
                "phone": customer.get("phone"),
                "city": address.get("city"),
                "zipcode": address.get("zipcode"),
                "latitude": _coordinate(geo.get("lat")),
                "longitude": _coordinate(geo.get("lng")),
                "company": company.get("name"),
                "website": customer.get("website"),
            }
        )
    return rows


def unique_cities(customers: list[dict]) -> set[str]:
    """Return the distinct non-empty customer city names."""
    cities = set()
    for customer in customers:
        city = (customer.get("address") or {}).get("city")
        if isinstance(city, str) and city.strip():
            # Trimming whitespace prevents visually identical city values being counted separately.
            cities.add(city.strip())
    return cities


def city_counts(customers: list[dict]) -> dict[str, int]:
    """Count customers by city without relying on third-party aggregation tools."""
    counts: dict[str, int] = {}
    for customer in customers:
        address = customer.get("address") or {}
        city = address.get("city")
        if isinstance(city, str) and city.strip():
            city = city.strip()
            # Start at zero for a new city, then increment for each matching customer.
            counts[city] = counts.get(city, 0) + 1
    return counts


def email_domain_counts(customers: list[dict]) -> dict[str, int]:
    """Count customer email addresses by their top-level domain."""
    counts: dict[str, int] = {}
    for customer in customers:
        email = customer.get("email")
        if not isinstance(email, str):
            continue
        # Ignore malformed addresses that do not contain a domain and top-level domain.
        domain = email.strip().rpartition("@")[2]
        if "." not in domain:
            continue
        top_level_domain = domain.rpartition(".")[2].lower()
        if top_level_domain:
            counts[top_level_domain] = counts.get(top_level_domain, 0) + 1
    return counts


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Convert flattened customer records to a tabular dataset for export."""
    # Explicit columns keep the CSV structure stable, including when there are no rows.
    columns = [
        "customer_id",
        "name",
        "username",
        "email",
        "email_domain",
        "phone",
        "city",
        "zipcode",
        "latitude",
        "longitude",
        "company",
        "website",
    ]
    return pd.DataFrame(rows, columns=columns)


def plot_distribution(counts: dict[str, int], path: Path) -> None:
    """Save a labelled bar chart of customer counts by category."""
    if not counts:
        raise ValueError("Cannot create a distribution chart without category counts.")

    # Sort largest counts first; alphabetical order breaks ties consistently.
    ordered_counts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    categories, values = zip(*ordered_counts)
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.bar(categories, values, color="#2878B5")
    axis.set_title("Customer Distribution by City")
    axis.set_xlabel("City")
    axis.set_ylabel("Number of Customers")
    axis.tick_params(axis="x", labelrotation=35)
    figure.tight_layout()

    # Create the destination directory when needed, then release the figure after saving.
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=150)
    plt.close(figure)


def main() -> None:
    """Run the customer profiling workflow and write its analysis outputs."""
    print("Customer Market Profile Analysis")
    customers = get_customers()
    if not customers:
        # Stop rather than creating empty reports that could be mistaken for valid results.
        raise SystemExit("Analysis stopped because no customer records were retrieved.")

    # Inspect one representative record so the source structure is visible in the run log.
    print("\nSample customer data structure:")
    explore(customers[0])

    # Prepare the flattened table and calculate independent summaries from source records.
    rows = extract_attributes(customers)
    customer_df = to_dataframe(rows)
    cities = city_counts(customers)
    domains = email_domain_counts(customers)

    # Resolve each deliverable path once so the console report matches the written files.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    customer_path = OUTPUT_DIR / "customers.csv"
    city_path = OUTPUT_DIR / "city_counts.csv"
    chart_path = OUTPUT_DIR / "customer_distribution.png"

    # CSVs are written without pandas' row index because it is not a customer attribute.
    customer_df.to_csv(customer_path, index=False)
    city_df = pd.DataFrame(
        sorted(cities.items(), key=lambda item: (-item[1], item[0])),
        columns=["city", "customer_count"],
    )
    city_df.to_csv(city_path, index=False)
    plot_distribution(cities, chart_path)

    # The same descending-count/alphabetical tie-break used in the city export applies here.
    most_common_city, most_common_count = min(
        cities.items(), key=lambda item: (-item[1], item[0])
    )
    print("\nKey findings")
    print(f"Customers retrieved : {len(customers)}")
    print(f"Unique cities       : {len(unique_cities(customers))}")
    print(f"Most common city    : {most_common_city} ({most_common_count})")
    print(f"Email domains       : {dict(sorted(domains.items()))}")
    print(f"Customer data saved : {customer_path}")
    print(f"City counts saved   : {city_path}")
    print(f"Chart saved to      : {chart_path}")


if __name__ == "__main__":
    # Run the workflow only when this file is executed directly, not when imported.
    main()
