from app.inference.reranker import CrossEncoderReranker

op_match = {
    "sport": "football",
    "league": "Premier League",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "kickoff_utc": "2026-02-15T18:30:00Z",
}

candidates = [
    {
        "match_id": "b1",
        "sport": "football",
        "league": "Premier League",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "kickoff_utc": "2026-02-15T18:28:00Z",
        "sbert_score": 0.99,
        "time_diff_min": 2,
    },
    {
        "match_id": "b2",
        "sport": "football",
        "league": "Premier League",
        "home_team": "Arsenal",
        "away_team": "Tottenham",
        "kickoff_utc": "2026-02-15T18:30:00Z",
        "sbert_score": 0.95,
        "time_diff_min": 0,
    },
]

reranker = CrossEncoderReranker()
results = reranker.rerank(op_match, candidates)

for r in results:
    print(r["match_id"], round(r["final_score"], 3))
