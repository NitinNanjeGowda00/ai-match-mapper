import re

MIN_SCORE = 0.90
MARGIN = 0.10
TIGHT_TIME_WINDOW = 900  # 15 minutes


def safe_text(value):
    if value is None:
        return ""
    return str(value)


def normalize(text):
    text = safe_text(text).lower()
    return re.sub(r"[^a-z0-9]", "", text)


def category_match(op, b):
    keywords = ["women", "w", "u23", "u21", "reserves", "bteam", "academy"]

    op_text = (
        safe_text(op.get("league")) +
        safe_text(op.get("home_team")) +
        safe_text(op.get("away_team"))
    ).lower()

    b_text = (
        safe_text(b.get("league")) +
        safe_text(b.get("home_team")) +
        safe_text(b.get("away_team"))
    ).lower()

    for k in keywords:
        if (k in op_text) != (k in b_text):
            return False

    return True


def detect_swap(op, b):
    op_home = normalize(op.get("home_team"))
    op_away = normalize(op.get("away_team"))
    b_home = normalize(b.get("home_team"))
    b_away = normalize(b.get("away_team"))

    if op_home == b_home and op_away == b_away:
        return False

    if op_home == b_away and op_away == b_home:
        return True

    return False


def apply_auto_gate(op, top5):
    if not top5:
        return None

    best, score1 = top5[0]

    score2 = top5[1][1] if len(top5) > 1 else 0.0

    if score1 < MIN_SCORE:
        return None

    if (score1 - score2) < MARGIN:
        return None

    if abs(op["commence_time"] - best["commence_time"]) > TIGHT_TIME_WINDOW:
        return None

    if not category_match(op, best):
        return None

    switch = detect_swap(op, best)

    return {
        "bet365_match": best["id"],
        "confidence": round(score1, 4),
        "switch": switch
    }