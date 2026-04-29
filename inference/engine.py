import uuid
from tqdm import tqdm
from inference.retrieval import Retriever
from inference.rerank import Reranker
from inference.gates import apply_auto_gate


def run_engine(oddsportal, bet365):

    retriever = Retriever()
    reranker = Reranker()

    bet365_embeddings = retriever.encode_matches(bet365)

    used_ids = set()
    results = []

    for op in tqdm(oddsportal):

        filtered = retriever.prefilter(op, bet365)

        if not filtered:
            results.append(no_match(op))
            continue

        filtered_embeddings = retriever.encode_matches(filtered)

        top10 = retriever.retrieve_top10(op, filtered, filtered_embeddings)
        top5 = reranker.rerank(op, top10)

        decision = apply_auto_gate(op, top5)

        if decision and decision["bet365_match"] not in used_ids:
            used_ids.add(decision["bet365_match"])
            results.append({
                "platform": "ODDSPORTAL",
                "bet365_match": decision["bet365_match"],
                "provider_id": op["id"],
                "confidence": decision["confidence"],
                "is_checked": False,
                "is_mapped": True,
                "reason": "auto_match",
                "switch": decision["switch"]
            })
        else:
            results.append(no_match(op))

    return results


def no_match(op):
    return {
        "platform": "ODDSPORTAL",
        "bet365_match": None,
        "provider_id": op["id"],
        "confidence": 0.0,
        "is_checked": False,
        "is_mapped": False,
        "reason": "NEED_REVIEW",
        "switch": False
    }