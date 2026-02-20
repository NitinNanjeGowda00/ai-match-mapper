# app/inference/swapped.py

def is_swapped(op_match: dict, candidate: dict) -> bool:
    """
    Detect if home/away teams are swapped between OP and B365.
    """

    op_home = (op_match.get("home_team") or "").lower()
    op_away = (op_match.get("away_team") or "").lower()

    c_home = (candidate.get("home_team") or "").lower()
    c_away = (candidate.get("away_team") or "").lower()

    if not op_home or not op_away or not c_home or not c_away:
        return False

    return op_home == c_away and op_away == c_home
