import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

TIME_WINDOW_SECONDS = 1800  # ±30 min


class Retriever:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def encode_matches(self, matches):
        texts = [
            f"{m['sport']} | {m['league']} | {m['home_team']} vs {m['away_team']}"
            for m in matches
        ]
        return self.model.encode(texts, show_progress_bar=True)

    def prefilter(self, op_match, bet365_matches):
        candidates = []
        for b in bet365_matches:
            if op_match["sport"].lower() != b["sport"].lower():
                continue

            if abs(op_match["commence_time"] - b["commence_time"]) > TIME_WINDOW_SECONDS:
                continue

            candidates.append(b)

        return candidates

    def retrieve_top10(self, op_match, bet365_matches, bet365_embeddings):
        op_text = f"{op_match['sport']} | {op_match['league']} | {op_match['home_team']} vs {op_match['away_team']}"
        op_emb = self.model.encode([op_text])

        sims = cosine_similarity(op_emb, bet365_embeddings)[0]
        top_idx = np.argsort(-sims)[:10]

        return [(bet365_matches[i], float(sims[i])) for i in top_idx]