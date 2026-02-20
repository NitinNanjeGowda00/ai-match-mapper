from app.inference.gates import decide_mapping

candidates = [
    {
        "match_id": "b1",
        "final_score": 0.95,
        "time_diff_min": 2,
        "categories": ["WOMEN"],
        "op_match": {
            "categories": ["WOMEN"]
        }
    },
    {
        "match_id": "b2",
        "final_score": 0.91,
        "time_diff_min": 3,
        "categories": ["WOMEN"],
    }
]

result = decide_mapping(candidates)
print(result)
