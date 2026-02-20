# app/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List

from app.inference.pipeline import run_inference

app = FastAPI(title="AI Match Mapping Engine")


class InferRequest(BaseModel):
    op_match: Dict
    b365_matches: List[Dict]


@app.post("/infer")
def infer_match(req: InferRequest):
    return run_inference(
        op_match=req.op_match,
        b365_matches=req.b365_matches,
    )
