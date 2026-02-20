from sentence_transformers import CrossEncoder

class Reranker:

    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, op_text, candidates):
        pairs = [(op_text, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)

        for c, score in zip(candidates, scores):
            c["final_score"] = float(score)

        return sorted(candidates, key=lambda x: x["final_score"], reverse=True)[:5]