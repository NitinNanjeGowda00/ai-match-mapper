from datetime import datetime
from typing import Dict, List
from config import KICKOFF_WINDOW_MIN

def parse_time(ts):
    return datetime.fromtimestamp(int(ts))

def minutes_diff(t1, t2):
    return abs((parse_time(t1) - parse_time(t2)).total_seconds()) / 60

def prefilter(op_match: Dict, candidates: List[Dict]) -> List[Dict]:
    results = []
    for m in candidates:
        if m["sport"].lower() != op_match["sport"].lower():
            continue

        diff = minutes_diff(op_match["commence_time"], m["commence_time"])
        if diff > KICKOFF_WINDOW_MIN:
            continue

        m["time_diff_min"] = int(diff)
        results.append(m)

    return results