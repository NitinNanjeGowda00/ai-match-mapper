# app/integration/storage.py

import json
import os
from typing import List, Dict


DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def save_json(filename: str, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
