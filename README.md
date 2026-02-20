# AI Match Mapping Engine

Production-ready AI system for mapping OddsPortal matches to Bet365 matches using:

- SBERT retrieval (Top-10)
- Cross-Encoder reranking (Top-5)
- Strict Auto-Match safety gates
- Configurable kickoff window filtering

## Architecture

GET API → Prefilter → SBERT → CrossEncoder → Gates → mapping_results.json

## Requirements

Python 3.11 recommended

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt