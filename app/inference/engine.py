from app.inference.prefilter import prefilter
from app.inference.text_builder import build_text
from app.inference.sbert_index import SBERTIndex
from app.inference.reranker import Reranker
from app.inference.gates import apply_gates

sbert = SBERTIndex()
reranker = Reranker()

def run_engine(op_match, bet365_matches):

    filtered = prefilter(op_match, bet365_matches)
    if not filtered:
        return None, "NO_MATCH"

    for m in filtered:
        m["text"] = build_text(m)

    sbert.build(filtered)

    op_text = build_text(op_match)
    retrieved = sbert.search(op_text, top_k=10)

    reranked = reranker.rerank(op_text, retrieved)

    decision = apply_gates(reranked)

    return reranked, decision