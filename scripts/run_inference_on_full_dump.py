# scripts/run_inference_on_full_dump.py

import json
import math
from pathlib import Path
from collections import defaultdict

from app.inference.pipeline import run_inference

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

DATA_DIR = Path("data")

BET365_FILE = DATA_DIR / "bet365_full_dump.json"
OP_FILE = DATA_DIR / "op_full_dump.json"
OUTPUT_FILE = DATA_DIR / "mapping_output.json"


# --------------------------------------------------
# NORMALIZATION
# --------------------------------------------------

def normalize_match(raw):

    return {
        "id": raw.get("id"),
        "sport": (raw.get("sport") or "").lower(),
        "league": raw.get("league", {}).get("league_name_en") if isinstance(raw.get("league"), dict) else "",
        "home_team": raw.get("home_team"),
        "away_team": raw.get("away_team"),
        "kickoff_utc": raw.get("commence_time"),
        "categories": [],
    }


# --------------------------------------------------
# GROUP BY SPORT
# --------------------------------------------------

def group_by_sport(matches):
    grouped = defaultdict(list)
    for m in matches:
        sport = (m.get("sport") or "").lower()
        grouped[sport].append(m)
    return grouped


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    if not BET365_FILE.exists() or not OP_FILE.exists():
        print("❌ Full dump files not found. Run fetch_all_data first.")
        return

    with open(BET365_FILE, "r", encoding="utf-8") as f:
        bet365_raw = json.load(f)

    with open(OP_FILE, "r", encoding="utf-8") as f:
        op_raw = json.load(f)

    print(f"Loaded Bet365: {len(bet365_raw)}")
    print(f"Loaded OddsPortal: {len(op_raw)}")

    bet365_norm = [normalize_match(m) for m in bet365_raw]
    op_norm = [normalize_match(m) for m in op_raw if not m.get("isMapped")]

    bet365_grouped = group_by_sport(bet365_norm)
    op_grouped = group_by_sport(op_norm)

    results = []
    total_runs = 0
    auto_count = 0

    for sport in op_grouped:

        if sport not in bet365_grouped:
            continue

        print("\n----------------------------------")
        print(f"Running inference for sport: {sport}")
        print(f"OP matches: {len(op_grouped[sport])}")
        print(f"B365 matches: {len(bet365_grouped[sport])}")

        for op_match in op_grouped[sport]:

            total_runs += 1

            result = run_inference(
                op_match=op_match,
                b365_matches=bet365_grouped[sport],
            )

            if not result.get("candidates"):
                continue

            best = result["candidates"][0]

            if result["decision"] == "AUTO_MATCH":

                prob = 1 / (1 + math.exp(-best.get("final_score", 0.0)))

                results.append({
                    "platform": "ODDSPORTAL",
                    "bet365_match": best.get("id"),
                    "provider_id": op_match.get("id"),
                    "confidence": round(prob, 4),
                    "is_checked": False,
                    "is_mapped": True,
                    "reason": result["reason"],
                    "switch": best.get("swapped", False),
                })

                auto_count += 1

    print("\n----------------------------------")
    print(f"Total inference runs: {total_runs}")
    print(f"AUTO MATCHES: {auto_count}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("✅ Mapping output saved.")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
