# scripts/fetch_all_data.py

import requests
import json
import time
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

BET365_URL = "https://sports-bet-api.allinsports.online/api/matches/get-bet365-matches-with-odds/"
ODDSPORTAL_URL = "https://sports-bet-api.allinsports.online/api/matches/get-odds-portal-matches-with-odds/"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

BET365_OUT = DATA_DIR / "bet365_full_dump.json"
OP_OUT = DATA_DIR / "op_full_dump.json"

REQUEST_TIMEOUT = 30
SLEEP_BETWEEN_PAGES = 1.0

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Connection": "keep-alive",
}


# --------------------------------------------------
# SESSION WITH RETRIES
# --------------------------------------------------

def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)

    return session


# --------------------------------------------------
# FETCH ALL PAGES
# --------------------------------------------------

def fetch_all_pages(session, base_url):

    all_rows = []
    page = 1

    while True:

        url = f"{base_url}?page={page}"

        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()

            if not data.get("status"):
                break

            rows = data.get("data", {}).get("rows", [])
            total_pages = data.get("data", {}).get("totalPages", 1)

            print(f"Fetched page {page}/{total_pages}")

            if not rows:
                break

            all_rows.extend(rows)

            if page >= total_pages:
                break

            page += 1
            time.sleep(SLEEP_BETWEEN_PAGES)

        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return all_rows


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    session = create_session()

    print("Fetching ALL Bet365 pages...")
    bet365_data = fetch_all_pages(session, BET365_URL)

    print("Fetching ALL OddsPortal pages...")
    op_data = fetch_all_pages(session, ODDSPORTAL_URL)

    print(f"\nBet365 total: {len(bet365_data)}")
    print(f"OddsPortal total: {len(op_data)}")

    with open(BET365_OUT, "w", encoding="utf-8") as f:
        json.dump(bet365_data, f)

    with open(OP_OUT, "w", encoding="utf-8") as f:
        json.dump(op_data, f)

    print("\n✅ Full datasets saved.")
    print(f"Saved: {BET365_OUT}")
    print(f"Saved: {OP_OUT}")


if __name__ == "__main__":
    main()
