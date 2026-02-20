import json
import requests
import sched
import time
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------
# CONFIG
# ---------------------------------

POST_URL = "https://sports-bet-api.allinsports.online/api/matches/ai-mapping-suggestion-save_v2"

MAPPING_FILE = Path("data/mapping_output.json")
STATE_FILE = Path("data/push_state.json")

REQUEST_TIMEOUT = 30

# ⏱ Change here (5 mins = 300, 30 mins = 1800)
INTERVAL_SECONDS = 300  

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "AI-Mapping-Engine/1.0"
}

# ---------------------------------
# SCHEDULER
# ---------------------------------

scheduler = sched.scheduler(time.time, time.sleep)

# ---------------------------------
# SESSION WITH RETRY
# ---------------------------------

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

# ---------------------------------
# STATE
# ---------------------------------

def load_state():
    if not STATE_FILE.exists():
        return {"last_pushed_index": -1}

    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(index: int):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"last_pushed_index": index}, f)

# ---------------------------------
# PUSH ONE MATCH
# ---------------------------------

def push_next_mapping():

    if not MAPPING_FILE.exists():
        print("❌ mapping_output.json not found.")
        return

    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mappings = json.load(f)

    total = len(mappings)

    if total == 0:
        print("Nothing to push.")
        return

    state = load_state()
    last_index = state.get("last_pushed_index", -1)
    next_index = last_index + 1

    if next_index >= total:
        print("✅ All mappings pushed. Scheduler stopping.")
        return

    mapping = mappings[next_index]

    print("\n----------------------------------")
    print(f"Pushing index {next_index + 1} / {total}")
    print(json.dumps(mapping, indent=2))
    print("----------------------------------\n")

    session = create_session()

    try:
        response = session.post(
            POST_URL,
            json=mapping,
            timeout=REQUEST_TIMEOUT
        )

        print("Status Code:", response.status_code)
        print("Response:", response.json())

        if response.status_code == 200 and response.json().get("status"):
            print("✅ Push successful.")
            save_state(next_index)

            # Schedule next push
            scheduler.enter(INTERVAL_SECONDS, 1, push_next_mapping)

        else:
            print("❌ Push failed. Will retry after interval.")
            scheduler.enter(INTERVAL_SECONDS, 1, push_next_mapping)

    except Exception as e:
        print("❌ Error pushing:", e)
        scheduler.enter(INTERVAL_SECONDS, 1, push_next_mapping)

# ---------------------------------
# MAIN
# ---------------------------------

if __name__ == "__main__":
    print("🚀 Starting Scheduled Push Engine")
    scheduler.enter(0, 1, push_next_mapping)
    scheduler.run()
