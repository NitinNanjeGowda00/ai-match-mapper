from app.inference.sbert import SBERTIndex

# Fake OP match
op_match = {
    "match_id": "op_1",
    "sport": "football",
    "league": "Premier League",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "kickoff_utc": "2026-02-15T18:30:00Z",
}

# Fake B365 pool (already prefiltered)
b365_matches = [
    {
        "match_id": "b1",
        "sport": "football",
        "league": "Premier League",
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "kickoff_utc": "2026-02-15T18:28:00Z",
    },
    {
        "match_id": "b2",
        "sport": "football",
        "league": "Premier League",
        "home_team": "Arsenal",
        "away_team": "Tottenham",
        "kickoff_utc": "2026-02-15T18:30:00Z",
    },
]

index = SBERTIndex()
index.build_or_load_embeddings(
    b365_matches,
    cache_path="data/embeddings/b365_test.pt",
)

results = index.retrieve_top_k(op_match, top_k=2)

for r in results:
    print(r["match_id"], round(r["sbert_score"], 3))
