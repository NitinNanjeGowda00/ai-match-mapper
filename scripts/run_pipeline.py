import json
from inference.engine import run_engine


def run():
    with open("data/raw/oddsportal.json", "r", encoding="utf-8") as f:
        oddsportal = json.load(f)

    with open("data/raw/bet365.json", "r", encoding="utf-8") as f:
        bet365 = json.load(f)

    results = run_engine(oddsportal, bet365)

    with open("data/mapping_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("DONE")


if __name__ == "__main__":
    run()