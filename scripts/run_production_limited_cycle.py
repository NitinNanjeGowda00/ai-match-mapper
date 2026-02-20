# scripts/run_production_limited_cycle.py

import requests
import json
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.inference.pipeline import run_inference

# -----------------------------
# CONFIG
# -----------------------------

BET365_URL = "https://sports-bet-api.allinsports.online/api/matches/get-bet365-matches-with-odds/"
ODDSPORTAL_URL = "https://sports-bet-api.allinsports.online/api/matches/get-odds-portal-matches-with-odds/"

OUT_FILE = Path("data/production_limited_output.json")

REQUEST_TIMEOUT = 30
MAX_PAGES_PER_RUN = 10   # 👈 CLIENT REQUIREMENT
SLEEP_BETWEEN_REQUESTS = 1.5  # 👈 Throttle protection


# -----------------------------
# SESSION WITH RETRY
# -----------------------------

def create_session():

    session = requests.Session()

    retry = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
    })

    return session


# -----------------------------
# UTIL
# -----------------------------

def unix_to_iso(ts: int):
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_match(raw: Dict) -> Dict:
    return {
        "id": raw.get("id"),
        "sport": (raw.get("sport") or "").lower(),
        "league": raw.get("league", {}).get("league_name_en"),
        "home_team": raw.get("home_team"),
        "away_team": raw.get("away_team"),
        "kickoff_utc": unix_to_iso(raw.get("commence_time")),
        "categories": [],
    }


# -----------------------------
# FETCH LIMITED PAGES
# -----------------------------

def fetch_limited_pages(session, base_url: str) -> List[Dict]:

    all_rows = []

    for page in range(1, MAX_PAGES_PER_RUN + 1):

        url = f"{base_url}?page={page}"

        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

        if not data.get("status"):
            break

        rows = data.get("data", {}).get("rows", [])

        if not rows:
            break

        print(f"Fetched page {page}")

        all_rows.extend(rows)

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    return all_rows


# -----------------------------
# MAIN
# -----------------------------

def main():

    session = create_session()

    print("Fetching Bet365 matches (limited)...")
    bet365_raw = fetch_limited_pages(session, BET365_URL)

    print("Fetching OddsPortal matches (limited)...")
    op_raw = fetch_limited_pages(session, ODDSPORTAL_URL)

    print(f"Bet365 matches fetched: {len(bet365_raw)}")
    print(f"OddsPortal matches fetched: {len(op_raw)}")

    # Only unmapped
    op_unmapped = [m for m in op_raw if not m.get("isMapped")]

    print(f"Unmapped matches: {len(op_unmapped)}")

    bet365_matches = [normalize_match(m) for m in bet365_raw]
    results = []

    for raw_op in op_unmapped:

        op_match = normalize_match(raw_op)

        result = run_inference(
            op_match=op_match,
            b365_matches=bet365_matches,
        )

        candidates = result.get("candidates", [])

        if not candidates:
            continue

        best = candidates[0]

        output_row = {
            "platform": "ODDSPORTAL",
            "bet365_match": best.get("id"),
            "provider_id": op_match.get("id"),
            "confidence": round(best.get("confidence", 0.0), 4),
            "is_checked": False,
            "is_mapped": result.get("decision") == "AUTO_MATCH",
            "reason": result.get("reason"),
            "switch": best.get("swapped", False),
        }

        results.append(output_row)

    print(f"Generated {len(results)} suggestions")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("✅ Limited Production Output Generated")
    print(f"Saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()
