import json
from pathlib import Path

from app.inference.pipeline import run_inference
from app.inference.output_formatter import format_mapping_output
from app.inference.adapters import (
    adapt_bet365_match,
    adapt_oddsportal_match,
)

# ------------------------
# Paths
# ------------------------

DATA_DIR = Path("data")
OP_FILE = DATA_DIR / "qsport-26-01-2026.oddsportal_matches.json"
B365_FILE = DATA_DIR / "qsport-26-01-2026.bet365_matches.json"
OUT_FILE = DATA_DIR / "mapping_output.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    oddsportal_raw = load_json(OP_FILE)
    bet365_raw = load_json(B365_FILE)

    # Adapt BET365 matches once
    bet365_matches = [adapt_bet365_match(m) for m in bet365_raw]

    results = []

    for op in oddsportal_raw:
        op_match = adapt_oddsportal_match(op)

        result = run_inference(
            op_match=op_match,
            b365_matches=bet365_matches,
        )

        top_candidate = result["candidates"][0] if result["candidates"] else None

        formatted = format_mapping_output(
            op_match=op_match,
            candidate=top_candidate,
            decision=result["decision"],
            reason=result["reason"],
        )

        results.append(formatted)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Mapping completed: {OUT_FILE}")


if __name__ == "__main__":
    main()
