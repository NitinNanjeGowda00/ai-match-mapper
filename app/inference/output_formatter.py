import uuid
import math

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def format_output(op, candidate, decision):

    if not candidate:
        return None

    confidence = round(sigmoid(candidate["final_score"]), 2)

    return {
        "platform": "ODDSPORTAL",
        "bet365_match": candidate["id"],
        "provider_id": op["id"],
        "confidence": confidence,
        "is_checked": False,
        "is_mapped": decision == "AUTO_MATCH",
        "reason": decision,
        "switch": False
    }