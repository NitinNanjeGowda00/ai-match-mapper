# scripts/run_full_batch_mapping.py

import math
import json
import traceback
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timezone

import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from app.inference.pipeline import run_inference
from app.inference.sbert import SBERTIndex


OP_FILE = Path("data/qsport-26-01-2026.oddsportal_matches.json")
B365_FILE = Path("data/qsport-26-01-2026.bet365_matches.json")
OUT_FILE = Path("data/mapping_output.json")


def unix_to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_team_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    for token in [" fc", " cf", " women", " w", ".", ","]:
        name = name.replace(token, "")
    return name.strip()


def normalize_op_match(raw: Dict) -> Dict:
    return {
        "id": raw.get("id"),
        "sport": (raw.get("sport") or "").lower(),
        "league": raw.get("league", {}).get("league_name_en") if raw.get("league") else "",
        "home_team": normalize_team_name(raw.get("home_team")),
        "away_team": normalize_team_name(raw.get("away_team")),
        "kickoff_utc": unix_to_iso(raw.get("commence_time")),
    }


def normalize_b365_match(raw: Dict) -> Dict:
    return {
        "id": raw.get("id"),
        "sport": (raw.get("sport") or "").lower(),
        "league": raw.get("league", {}).get("league_name_en") if raw.get("league") else "",
        "home_team": normalize_team_name(raw.get("home_team")),
        "away_team": normalize_team_name(raw.get("away_team")),
        "kickoff_utc": unix_to_iso(raw.get("commence_time")),
    }


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def format_output(
    op_match: Dict,
    best_candidate: Dict | None,
    decision: str,
    reason: str,
) -> Dict:

    if best_candidate:
        raw_score = float(best_candidate.get("final_score", 0.0))
        confidence = round(sigmoid(raw_score), 4)
        bet365_id = best_candidate.get("id")
        switch_flag = best_candidate.get("swapped", False)
    else:
        confidence = 0.0
        bet365_id = None
        switch_flag = False

    return {
        "platform": "ODDSPORTAL",
        "bet365_match": bet365_id,
        "provider_id": op_match.get("id"),
        "confidence": confidence,
        "is_checked": False,
        "is_mapped": True if decision == "AUTO_MATCH" else False,
        "reason": reason if reason else decision,
        "switch": switch_flag,
    }


def main():

    print("Loading JSON files...")

    with open(OP_FILE, "r", encoding="utf-8") as f:
        op_data = json.load(f)

    with open(B365_FILE, "r", encoding="utf-8") as f:
        b365_data = json.load(f)

    print(f"OddsPortal matches: {len(op_data)}")
    print(f"Bet365 matches: {len(b365_data)}")

    normalized_b365 = [normalize_b365_match(m) for m in b365_data]

    print("Building SBERT index...")
    sbert_index = SBERTIndex()
    sbert_index.build_or_load_embeddings(normalized_b365)

    used_b365_ids = set()
    output_rows = []

    print("Running batch mapping...")

    for idx, raw_op in enumerate(op_data):

        try:

            op_match = normalize_op_match(raw_op)

            result = run_inference(
                op_match=op_match,
                b365_matches=normalized_b365,
            )

            candidates = result.get("candidates", [])
            decision = result.get("decision", "NO_MATCH")
            reason = result.get("reason", decision)

            # Fallback
            if not candidates:
                decision = "NO_MATCH"
                reason = "no_match"

            best_candidate = None

            for c in candidates:
                if c.get("id") not in used_b365_ids:
                    best_candidate = c
                    used_b365_ids.add(c.get("id"))
                    break

            formatted = format_output(
                op_match,
                best_candidate,
                decision,
                reason,
            )

        except Exception as e:

            print(f"Error processing match {idx}: {e}")
            traceback.print_exc()

            formatted = {
                "platform": "ODDSPORTAL",
                "bet365_match": None,
                "provider_id": raw_op.get("id"),
                "confidence": 0.0,
                "is_checked": False,
                "is_mapped": False,
                "reason": "processing_error",
                "switch": False,
            }

        output_rows.append(formatted)

    print(f"\nGenerated {len(output_rows)} mappings.")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_rows, f, indent=2)

    print("✅ Batch mapping export complete.")
    print(f"Saved to {OUT_FILE}")


if __name__ == "__main__":
    main()
