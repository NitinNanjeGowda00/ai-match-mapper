import math
from config import MIN_SCORE, MIN_MARGIN

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def apply_gates(candidates):

    if not candidates:
        return "NO_MATCH"

    best = candidates[0]
    best_prob = sigmoid(best["final_score"])

    if best_prob < MIN_SCORE:
        return "NEED_REVIEW"

    if len(candidates) > 1:
        second_prob = sigmoid(candidates[1]["final_score"])
        if best_prob - second_prob < MIN_MARGIN:
            return "NEED_REVIEW"

    return "AUTO_MATCH"