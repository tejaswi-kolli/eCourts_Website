import requests
import json
import argparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

def get_date(day_option):
    """Return date string based on option"""
    if day_option == "today":
        return datetime.now().strftime("%d-%m-%Y")
    elif day_option == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    else:
        return day_option  # custom date if provided


def get_case_status(cnr=None, case_type=None, case_number=None, case_year=None, day_option="today"):
    """Fetch case status using CNR or case details"""
    query_date = get_date(day_option)
    if cnr:
        url = f"{BASE_URL}?p=cnr_status"
        data = {"cnr": cnr}
    else:
        url = f"{BASE_URL}?p=case_status"
        data = {
            "case_type": case_type,
            "case_number": case_number,
            "case_year": case_year
        }

    print(f"🔍 Checking case status for {query_date} ...")

    try:
        res = requests.post(url, data=data, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print("❌ Error fetching case status:", e)
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    table = soup.find("table")

    if not table:
        print("⚠️ No case details found. Please check your inputs.")
        return None

    case_info = {"checked_on": query_date, "listings": []}
    rows = table.find_all("tr")[1:]  # skip header

    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if len(cols) >= 4:
            hearing_date, court_name, serial_no = cols[1], cols[2], cols[3]
            case_info["listings"].append({
                "hearing_date": hearing_date,
                "court_name": court_name,
                "serial_no": serial_no
            })

    found = False
    for listing in case_info["listings"]:
        if listing["hearing_date"] == query_date:
            print(f"\n✅ Case listed on {listing['hearing_date']}")
            print(f"   • Court: {listing['court_name']}")
            print(f"   • Serial No: {listing['serial_no']}")
            found = True

    if not found:
        print("❌ Case not listed on the selected date.")

    # Save to file
    filename = f"case_status_{query_date.replace('-', '')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(case_info, f, indent=4)
        print(f"\n📁 Results saved to {filename}")

    return case_info


def download_cause_list(day_option="today"):
    """Download the cause list PDF for given date"""
    query_date = get_date(day_option)
    print(f"📥 Downloading cause list for {query_date}...")
    try:
        url = f"{BASE_URL}?p=causelist&date={query_date}"
        res = requests.get(url, timeout=20)
        res.raise_for_status()
        filename = f"cause_list_{query_date.replace('-', '')}.pdf"
        with open(filename, "wb") as f:
            f.write(res.content)
        print(f"✅ Cause list saved as {filename}")
    except Exception as e:
        print("❌ Failed to download cause list:", e)


def main():
    parser = argparse.ArgumentParser(description="eCourts Scraper Tool")
    parser.add_argument("--cnr", help="CNR number of the case")
    parser.add_argument("--type", help="Case type (if no CNR)")
    parser.add_argument("--number", help="Case number (if no CNR)")
    parser.add_argument("--year", help="Case year (if no CNR)")
    parser.add_argument("--today", action="store_true", help="Check listings for today")
    parser.add_argument("--tomorrow", action="store_true", help="Check listings for tomorrow")
    parser.add_argument("--causelist", action="store_true", help="Download cause list (today or tomorrow)")

    args = parser.parse_args()

    # Determine which date to check
    day_option = "today"
    if args.tomorrow:
        day_option = "tomorrow"

    if args.causelist:
        download_cause_list(day_option)
    else:
        if args.cnr:
            get_case_status(cnr=args.cnr, day_option=day_option)
        elif args.type and args.number and args.year:
            get_case_status(case_type=args.type, case_number=args.number, case_year=args.year, day_option=day_option)
        else:
            print("⚠️ Please provide CNR or (type, number, year). Use --help for usage.")


if __name__ == "__main__":
    main()
