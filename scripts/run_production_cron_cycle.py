# scripts/run_production_cron_cycle.py

import requests
import json
import time
import math
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.inference.pipeline import run_inference


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

BET365_URL = "https://sports-bet-api.allinsports.online/api/matches/get-bet365-matches-with-odds/"
ODDSPORTAL_URL = "https://sports-bet-api.allinsports.online/api/matches/get-odds-portal-matches-with-odds/"

OUT_FILE = Path("data/production_cron_output.json")

MAX_PAGES_PER_RUN = 10
REQUEST_TIMEOUT = 30
SLEEP_BETWEEN_PAGES = 1.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
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
# TIME CONVERSION
# --------------------------------------------------

def unix_to_iso(ts):
    if not ts:
        return None

    if isinstance(ts, int):
        return (
            datetime.fromtimestamp(ts, tz=timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    if isinstance(ts, str):
        return ts

    return None


# --------------------------------------------------
# FETCH LIMITED PAGES
# --------------------------------------------------

def fetch_limited_pages(session, base_url: str) -> List[Dict]:

    all_rows = []

    for page in range(1, MAX_PAGES_PER_RUN + 1):

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

            time.sleep(SLEEP_BETWEEN_PAGES)

        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break

    return all_rows


# --------------------------------------------------
# PRODUCTION SAFE NORMALIZATION
# --------------------------------------------------

def normalize_match(raw: Dict) -> Dict:

    sport = (
        raw.get("sport")
        or raw.get("sportName")
        or raw.get("sport_name")
        or ""
    )

    sport = str(sport).lower()

    league = ""
    if isinstance(raw.get("league"), dict):
        league = raw["league"].get("league_name_en") or raw["league"].get("name") or ""
    else:
        league = raw.get("league") or raw.get("leagueName") or ""

    return {
        "id": raw.get("id") or raw.get("_id") or raw.get("provider_id"),
        "sport": sport,
        "league": league,
        "home_team": raw.get("home_team") or raw.get("homeTeam"),
        "away_team": raw.get("away_team") or raw.get("awayTeam"),
        "kickoff_utc": unix_to_iso(raw.get("commence_time") or raw.get("startTime")),
        "categories": [],
    }


# --------------------------------------------------
# MAIN CRON EXECUTION
# --------------------------------------------------

def main():

    session = create_session()

    print("Fetching Bet365 matches (limited)...")
    bet365_raw = fetch_limited_pages(session, BET365_URL)

    print("Fetching OddsPortal matches (limited)...")
    op_raw = fetch_limited_pages(session, ODDSPORTAL_URL)

    print(f"Bet365 matches fetched: {len(bet365_raw)}")
    print(f"OddsPortal matches fetched: {len(op_raw)}")


    # Filter only unmapped
    unmapped_op = [m for m in op_raw if not m.get("isMapped")]

    print(f"Unmapped OP matches: {len(unmapped_op)}")

    bet365_matches = [normalize_match(m) for m in bet365_raw]
    op_matches = [normalize_match(m) for m in unmapped_op]

    results = []

    for op_match in op_matches:

        try:

            result = run_inference(
                op_match=op_match,
                b365_matches=bet365_matches,
            )

            decision = result.get("decision")
            reason = result.get("reason")
            candidates = result.get("candidates", [])

            if not candidates:
                continue

            best = candidates[0]

            if decision == "AUTO_MATCH":

                prob = 1 / (1 + math.exp(-best.get("final_score", 0.0)))

                output_row = {
                    "platform": "ODDSPORTAL",
                    "bet365_match": best.get("id"),
                    "provider_id": op_match.get("id"),
                    "confidence": round(prob, 4),
                    "is_checked": False,
                    "is_mapped": True,
                    "reason": reason,
                    "switch": best.get("swapped", False),
                }

                results.append(output_row)

        except Exception as e:
            print(f"Inference error: {e}")
            continue

    print(f"\nAUTO_MATCH approved: {len(results)}")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("✅ Production Cron Output Generated")
    print(f"Saved to: {OUT_FILE}")


if __name__ == "__main__":
    main()
