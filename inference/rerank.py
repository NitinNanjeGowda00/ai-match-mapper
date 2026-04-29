from sentence_transformers import CrossEncoder


class Reranker:
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, op_match, candidates):
        pairs = [
            (
                f"{op_match['sport']} | {op_match['league']} | {op_match['home_team']} vs {op_match['away_team']}",
                f"{c[0]['sport']} | {c[0]['league']} | {c[0]['home_team']} vs {c[0]['away_team']}"
            )
            for c in candidates
        ]

        scores = self.model.predict(pairs)

        reranked = []
        for i, (match, _) in enumerate(candidates):
            reranked.append((match, float(scores[i])))

        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked[:5]