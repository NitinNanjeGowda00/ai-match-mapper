import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import DEFAULT_LIMIT, REQUEST_TIMEOUT

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Match-Mapper/1.0",
    "Accept": "application/json"
}


def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def fetch_all(url):
    session = create_session()

    page = 1
    results = []

    while True:
        try:
            response = session.get(
                url,
                params={"page": page, "limit": DEFAULT_LIMIT},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()
            data = response.json()["data"]

            results.extend(data["rows"])

            if data["nextPage"] is None:
                break

            page = data["nextPage"]

            # small delay to avoid rate-limit
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Error fetching page {page}: {e}")
            print("⏳ Retrying in 5 seconds...")
            time.sleep(5)

    return results