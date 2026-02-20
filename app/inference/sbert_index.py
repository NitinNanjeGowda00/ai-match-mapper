from sentence_transformers import SentenceTransformer, util
import torch

class SBERTIndex:

    def __init__(self):
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.embeddings = None
        self.matches = None

    def build(self, matches):
        self.matches = matches
        texts = [m["text"] for m in matches]
        self.embeddings = self.model.encode(texts, convert_to_tensor=True)

    def search(self, query_text, top_k=10):
        query_emb = self.model.encode(query_text, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, self.embeddings)[0]
        top_scores, top_idx = torch.topk(scores, k=min(top_k, len(scores)))

        results = []
        for score, idx in zip(top_scores.tolist(), top_idx.tolist()):
            item = dict(self.matches[idx])
            item["sbert_score"] = float(score)
            results.append(item)

        return results