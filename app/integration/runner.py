# app/integration/runner.py

import math
from typing import Dict, List

from app.integration.fetcher import (
    fetch_unmapped_bet365,
    fetch_unmapped_oddsportal,
)
from app.integration.storage import save_json
from app.inference.adapters import (
    adapt_bet365_match,
    adapt_oddsportal_match,
)
from app.inference.pipeline import run_inference


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def format_output(op_match: Dict, result: Dict) -> Dict:

    if not result["candidates_top5"]:
        return {
            "platform": "ODDSPORTAL",
            "bet365_match": None,
            "provider_id": op_match["id"],
            "confidence": 0.0,
            "is_checked": False,
            "is_mapped": False,
            "reason": result["reason"],
            "switch": False,
        }

    best = result["candidates_top5"][0]

    confidence = round(sigmoid(best.get("final_score", 0.0)), 4)

    return {
        "platform": "ODDSPORTAL",
        "bet365_match": best.get("id"),
        "provider_id": op_match["id"],
        "confidence": confidence,
        "is_checked": False,
        "is_mapped": result["decision"] == "AUTO_MATCH",
        "reason": result["reason"],
        "switch": bool(best.get("swapped", False)),
    }


def run_full_pipeline():

    print("Fetching unmapped OddsPortal matches...")
    raw_op = fetch_unmapped_oddsportal()

    print("Fetching unmapped Bet365 matches...")
    raw_b365 = fetch_unmapped_bet365()

    print("Adapting matches...")
    op_matches = [adapt_oddsportal_match(m) for m in raw_op]
    b365_matches = [adapt_bet365_match(m) for m in raw_b365]

    save_json("unmapped_oddsportal.json", op_matches)
    save_json("unmapped_bet365.json", b365_matches)

    print(f"Running inference on {len(op_matches)} OP matches...")

    outputs = []

    for op in op_matches:

        result = run_inference(
            op_match=op,
            b365_matches=b365_matches,
        )

        formatted = format_output(op, result)
        outputs.append(formatted)

    save_json("mapping_results.json", outputs)

    print("Pipeline completed.")
    print(f"Total mappings processed: {len(outputs)}")

    return outputs
