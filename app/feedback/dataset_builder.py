import json
from pathlib import Path

FEEDBACK_FILE = Path("data/feedback.json")
MAPPING_FILE = Path("data/mapping_output.json")
OUTPUT_FILE = Path("data/training_dataset.json")


def extract_final_decision(feedback_row):
    """
    Determine final human decision from logs.
    Priority:
    Not Correct > Not Sure > Mapping Completed > Team Switched
    """

    logs = feedback_row.get("logs", [])

    decisions = [log.get("what") for log in logs]

    if "Not Correct" in decisions:
        return "NO_MATCH"

    if "Not Sure" in decisions:
        return "SKIP"

    if "Team Switched" in decisions:
        return "SWAPPED"

    if "Mapping Completed" in decisions:
        return "MATCH"

    # fallback
    if feedback_row.get("is_mapped"):
        return "MATCH"

    return "SKIP"


def build_dataset():

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        feedback_data = json.load(f)

    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping_data = json.load(f)

    print(f"Loaded {len(feedback_data)} feedback records")

    # Build lookup from inference output
    mapping_lookup = {
        row["provider_id"]: row
        for row in mapping_data
    }

    training_samples = []

    # Deduplicate by provider_id (keep last)
    feedback_dedup = {}
    for row in feedback_data:
        feedback_dedup[row["provider_id"]] = row

    print(f"After deduplication: {len(feedback_dedup)} unique records")

    for provider_id, fb in feedback_dedup.items():

        decision = extract_final_decision(fb)

        if decision == "SKIP":
            continue

        if provider_id not in mapping_lookup:
            continue

        mapping_row = mapping_lookup[provider_id]
        selected_b365 = fb.get("bet365_match")

        # ---- Positive cases ----
        if decision in ["MATCH", "SWAPPED"]:

            training_samples.append({
                "op_id": provider_id,
                "b365_id": selected_b365,
                "label": 1,
                "swapped": decision == "SWAPPED",
            })

            # ---- Hard negatives from Top-5 ----
            # Only if you have Top-5 in mapping_output
            candidates = mapping_row.get("candidates_top5", [])

            for c in candidates:
                if c["bet365_match"] != selected_b365:
                    training_samples.append({
                        "op_id": provider_id,
                        "b365_id": c["bet365_match"],
                        "label": 0,
                        "swapped": False,
                    })

        # ---- Negative case ----
        if decision == "NO_MATCH":

            candidates = mapping_row.get("candidates_top5", [])

            for c in candidates:
                training_samples.append({
                    "op_id": provider_id,
                    "b365_id": c["bet365_match"],
                    "label": 0,
                    "swapped": False,
                })

    print(f"Generated {len(training_samples)} training samples")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(training_samples, f, indent=2)

    print(f"✅ Training dataset saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    build_dataset()
