from app.inference.prefilter import prefilter_candidates

op_match = {
    "sport": "football",
    "kickoff_utc": "2026-02-15T18:30:00Z",
}

b365_matches = [
    {
        "match_id": "1",
        "sport": "football",
        "kickoff_utc": "2026-02-15T18:25:00Z",
    },
    {
        "match_id": "2",
        "sport": "football",
        "kickoff_utc": "2026-02-15T19:45:00Z",
    },
    {
        "match_id": "3",
        "sport": "tennis",
        "kickoff_utc": "2026-02-15T18:30:00Z",
    },
]

candidates = prefilter_candidates(op_match, b365_matches, kickoff_window_min=30)

for c in candidates:
    print(c["match_id"], c["time_diff_min"])
