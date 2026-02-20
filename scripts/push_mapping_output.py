# scripts/push_mapping_output.py

import json
import time
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

POST_URL = "https://sports-bet-api.allinsports.online/api/matches/ai-mapping-suggestion-save"
INPUT_FILE = Path("data/mapping_output.json")

REQUEST_TIMEOUT = 30
SLEEP_BETWEEN_REQUESTS = 0.3   # safe throttle

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# --------------------------------------------------
# CREATE SESSION WITH RETRIES
# --------------------------------------------------

def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)

    return session


# --------------------------------------------------
# MAIN PUSH LOGIC
# --------------------------------------------------

def main():

    if not INPUT_FILE.exists():
        print("❌ mapping_output.json not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    print(f"Loaded mappings: {len(mappings)}")

    if not mappings:
        print("Nothing to push.")
        return

    session = create_session()

    success = 0
    failed = 0

    for idx, row in enumerate(mappings, start=1):

        try:
            response = session.post(
                POST_URL,
                json=row,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code in (200, 201):
                success += 1
                print(f"[{idx}] ✅ Success → provider_id: {row.get('provider_id')}")
            else:
                failed += 1
                print(f"[{idx}] ❌ Failed ({response.status_code}) → {response.text}")

        except Exception as e:
            failed += 1
            print(f"[{idx}] ❌ Error → {e}")

        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print("\n----------------------------------")
    print(f"Total Success: {success}")
    print(f"Total Failed : {failed}")
    print("✅ Push process completed.")


if __name__ == "__main__":
    main()
