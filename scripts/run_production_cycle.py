import json
from config import BET365_URL, ODDSPORTAL_URL
from app.integration.fetcher import fetch_all
from app.inference.engine import run_engine
from app.inference.output_formatter import format_output

def main():

    print("Fetching Bet365 matches...")
    bet365 = fetch_all(BET365_URL)

    print("Fetching OddsPortal matches...")
    op_matches = fetch_all(ODDSPORTAL_URL)

    results = []

    for op in op_matches:
        candidates, decision = run_engine(op, bet365)

        if candidates:
            output = format_output(op, candidates[0], decision)
            if output:
                results.append(output)

    with open("data/mapping_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Done.")

if __name__ == "__main__":
    main()