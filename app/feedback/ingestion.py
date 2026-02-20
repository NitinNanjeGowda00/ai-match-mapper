# app/feedback/ingestion.py

import json
from pathlib import Path
from typing import Dict, List


FEEDBACK_FILE = Path("data/feedback_log.json")


def save_feedback(feedback: Dict):
    """
    Save one feedback entry to feedback_log.json
    """

    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    if FEEDBACK_FILE.exists():
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(feedback)

    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_feedback() -> List[Dict]:
    """
    Load all feedback entries
    """
    if not FEEDBACK_FILE.exists():
        return []

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
