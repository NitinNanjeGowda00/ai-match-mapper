# scripts/run_feedback_loop.py

import json
from pathlib import Path
from typing import Dict, List

# -----------------------------
# FILE PATHS
# -----------------------------

ROOT = Path(__file__).resolve().parent.parent

FEEDBACK_FILE = ROOT / "data" / "feedback.json"
MAPPING_FILE = ROOT / "data" / "mapping_output.json"
OUT_FILE = ROOT / "data" / "training_dataset.json"


# -----------------------------
# LOAD JSON SAFELY
# -----------------------------

def load_json(path: Path):
    if not path.exists():
        print(f"❌ File not found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f"❌ Failed to parse JSON: {e}")
            return []


# -----------------------------
# HARD NEGATIVE MINING BUILDER
# -----------------------------

def build_training_dataset(feedback_list: List[Dict], mapping_list: List[Dict]):

    dataset = []

    # Build lookup by provider_id
    mapping_lookup = {
        m["provider_id"]: m
        for m in mapping_list
    }

    for fb in feedback_list:

        provider_id = fb.get("provider_id")
        bet365_id = fb.get("bet365_match")
        feedback_type = fb.get("feedback")

        if provider_id not in mapping_lookup:
            continue

        mapping = mapping_lookup[provider_id]
        top5 = mapping.get("candidates_top5", [])

        # -------------------------
        # CORRECT
        # -------------------------
        if feedback_type == "correct":

            # Positive
            dataset.append({
                "provider_id": provider_id,
                "bet365_match": bet365_id,
                "label": 1
            })

            # Hard negatives from top5
            for c in top5:
                if c["bet365_match"] != bet365_id:
                    dataset.append({
                        "provider_id": provider_id,
                        "bet365_match": c["bet365_match"],
                        "label": 0
                    })

        # -------------------------
        # NEED SWAP
        # -------------------------
        elif feedback_type == "need_swap":

            dataset.append({
                "provider_id": provider_id,
                "bet365_match": bet365_id,
                "label": 1,
                "swapped": True
            })

            for c in top5:
                if c["bet365_match"] != bet365_id:
                    dataset.append({
                        "provider_id": provider_id,
                        "bet365_match": c["bet365_match"],
                        "label": 0
                    })

        # -------------------------
        # NOT CORRECT
        # -------------------------
        elif feedback_type == "not_correct":

            # Mark chosen match as negative
            dataset.append({
                "provider_id": provider_id,
                "bet365_match": bet365_id,
                "label": 0
            })

            # Also mark ALL top5 as negatives
            for c in top5:
                dataset.append({
                    "provider_id": provider_id,
                    "bet365_match": c["bet365_match"],
                    "label": 0
                })

        # -------------------------
        # NOT SURE → Ignore
        # -------------------------
        elif feedback_type == "not_sure":
            continue

    # Remove duplicates
    unique = {
        (d["provider_id"], d["bet365_match"], d["label"]): d
        for d in dataset
    }

    final_dataset = list(unique.values())

    print("\n----- Dataset Summary -----")
    print(f"Total training rows: {len(final_dataset)}")
    print(f"Unique pairs: {len(final_dataset)}")
    print("----------------------------\n")

    return final_dataset


# -----------------------------
# MAIN
# -----------------------------

def main():

    print("Reading feedback from:", FEEDBACK_FILE.resolve())
    print("Reading mappings from:", MAPPING_FILE.resolve())

    feedback = load_json(FEEDBACK_FILE)
    mappings = load_json(MAPPING_FILE)

    print(f"\nLoaded {len(feedback)} feedback entries.")
    print(f"Loaded {len(mappings)} mapping entries.\n")

    if not feedback:
        print("⚠ No feedback found. Exiting.")
        return

    dataset = build_training_dataset(feedback, mappings)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"✅ Training dataset saved to {OUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
