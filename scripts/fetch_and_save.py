import requests
import json
import os
import time


ODDSPORTAL_URL = "https://sports-bet-api.allinsports.online/api/matches/get-odds-portal-matches-with-odds"
BET365_URL = "https://sports-bet-api.allinsports.online/api/matches/get-bet365-matches-with-odds"

SAVE_DIR = "data/raw"
os.makedirs(SAVE_DIR, exist_ok=True)

PAGE_SIZE = 100  # adjustable


def deep_find_list(obj):
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            result = deep_find_list(value)
            if isinstance(result, list):
                return result
    return None


def normalize_match(match):
    league = match.get("league")

    if isinstance(league, dict):
        league_name = league.get("league_name_en") or league.get("name")
    else:
        league_name = league

    return {
        "id": match.get("id"),
        "sport": match.get("sport"),
        "league": league_name,
        "home_team": match.get("home_team"),
        "away_team": match.get("away_team"),
        "commence_time": match.get("commence_time")
    }


def fetch_all_pages(base_url):
    page = 1
    all_matches = []

    while True:
        print(f"Fetching page {page}...")

        params = {
            "page": page,
            "limit": PAGE_SIZE
        }

        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()
        match_list = deep_find_list(data)

        if not match_list:
            break

        all_matches.extend(match_list)

        if len(match_list) < PAGE_SIZE:
            # last page
            break

        page += 1
        time.sleep(0.5)  # avoid API rate limit

    return all_matches


def fetch_and_save(url, filename):
    print(f"Fetching ALL data from {url}...")

    matches = fetch_all_pages(url)

    normalized = [normalize_match(match) for match in matches]

    path = os.path.join(SAVE_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)

    print(f"Saved {len(normalized)} matches to {path}")


def run():
    fetch_and_save(ODDSPORTAL_URL, "oddsportal.json")
    fetch_and_save(BET365_URL, "bet365.json")
    print("All data fetched and saved successfully.")


if __name__ == "__main__":
    run()