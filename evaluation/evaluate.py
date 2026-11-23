
import json
import csv
import os
import sys

from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
EVALUATION_DIR = BASE_DIR / "evaluation"

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("API_KEY")

URL = "http://127.0.0.1:8000/search"

if not API_KEY:
    print("ERROR: API_KEY not found in .env")
    sys.exit(1)

HEADERS = {
    "x-api-key": API_KEY
}

QUERY_FILE = EVALUATION_DIR / "queries.json"


# ==========================================
# 2. LOAD EVALUATION QUERIES
# ==========================================

with open(
    QUERY_FILE,
    "r",
    encoding="utf-8"
) as file:

    queries = json.load(file)

print("\n===================================")
print("       RETRIEVAL EVALUATION")
print("===================================")

print("Total evaluation queries:", len(queries))


# ==========================================
# 3. SEARCH AND EVALUATE
# ==========================================

evaluation_results = []

reciprocal_ranks = []

hits_at_1 = 0
hits_at_3 = 0
hits_at_5 = 0


try:

    with httpx.Client(timeout=60) as client:

        for item in queries:

            query = item["query"]

            expected_source = item["expected_source"]

            expected_page = item["expected_page"]

            print(f"\nQuery {item['id']}: {query}")

            response = client.post(
                URL,
                headers=HEADERS,
                json={
                    "query": query,
                    "top_k": 5
                }
            )

            response.raise_for_status()

            results = response.json()["results"]

            # Find the first correct source AND page
            correct_rank = None

            for rank, result in enumerate(results, start=1):

                if (
                    result["source"] == expected_source
                    and result["page"] == expected_page
                ):

                    correct_rank = rank
                    break

            # Calculate reciprocal rank
            if correct_rank is not None:

                reciprocal_rank = 1 / correct_rank

            else:

                reciprocal_rank = 0

            reciprocal_ranks.append(reciprocal_rank)

            # Hit rate
            hit_1 = int(correct_rank is not None and correct_rank <= 1)

            hit_3 = int(correct_rank is not None and correct_rank <= 3)

            hit_5 = int(correct_rank is not None and correct_rank <= 5)

            hits_at_1 += hit_1
            hits_at_3 += hit_3
            hits_at_5 += hit_5

            evaluation_results.append({
                "id": item["id"],
                "query": query,
                "expected_source": expected_source,
                "expected_page": expected_page,
                "correct_rank": correct_rank if correct_rank else "Not Found",
                "reciprocal_rank": round(reciprocal_rank, 4),
                "hit_at_1": hit_1,
                "hit_at_3": hit_3,
                "hit_at_5": hit_5
            })

            print("Expected source:", expected_source)
            print("Expected page:", expected_page)
            print("Correct rank:", correct_rank or "Not Found")
            print("Reciprocal rank:", round(reciprocal_rank, 4))


except httpx.ConnectError:

    print("\nERROR: FastAPI server is not running.")
    print("Start using: python -m uvicorn main:app")
    sys.exit(1)

except httpx.HTTPStatusError as error:

    print("\nAPI ERROR:", error.response.status_code)
    print(error.response.text)
    sys.exit(1)


# ==========================================
# 4. CALCULATE METRICS
# ==========================================

total_queries = len(queries)

if total_queries == 0:
    print("No evaluation queries found.")
    sys.exit(1)

hit_rate_1 = hits_at_1 / total_queries

hit_rate_3 = hits_at_3 / total_queries

hit_rate_5 = hits_at_5 / total_queries

mrr = float(np.mean(reciprocal_ranks))


# ==========================================
# 5. DISPLAY RESULTS
# ==========================================

print("\n===================================")
print("       EVALUATION RESULTS")
print("===================================")

print("Total queries:", total_queries)

print(f"Hit@1: {hit_rate_1:.4f}")
print(f"Hit@3: {hit_rate_3:.4f}")
print(f"Hit@5: {hit_rate_5:.4f}")
print(f"MRR:    {mrr:.4f}")


# ==========================================
# 6. SAVE QUERY RESULTS
# ==========================================

query_results_file = EVALUATION_DIR / "query_results.csv"

with open(
    query_results_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=evaluation_results[0].keys()
    )

    writer.writeheader()
    writer.writerows(evaluation_results)


# ==========================================
# 7. IDENTIFY THREE WORST QUERIES
# ==========================================

worst_queries = sorted(
    evaluation_results,
    key=lambda item: (
        item["reciprocal_rank"],
        item["id"]
    )
)[:3]

worst_file = EVALUATION_DIR / "worst_queries.csv"

with open(
    worst_file,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=worst_queries[0].keys()
    )

    writer.writeheader()
    writer.writerows(worst_queries)


# ==========================================
# 8. SAVE CONFIG A METRICS
# ==========================================

experiment_file = EVALUATION_DIR / "experiment_results.csv"

config_result = {
    "configuration": "Config B",
    "chunk_size": 800,
    "overlap": 150,
    "embedding_model": "all-MiniLM-L6-v2",
    "hit_at_1": round(hit_rate_1, 4),
    "hit_at_3": round(hit_rate_3, 4),
    "hit_at_5": round(hit_rate_5, 4),
    "mrr": round(mrr, 4)
}

fieldnames = list(config_result.keys())

write_header = not experiment_file.exists()

with open(
    experiment_file,
    "a",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    if write_header:
        writer.writeheader()

    writer.writerow(config_result)


# ==========================================
# 9. FINAL REPORT
# ==========================================

print("\n===================================")
print("       FILES GENERATED")
print("===================================")

print("Query results:", query_results_file)
print("Worst queries:", worst_file)
print("Experiment results:", experiment_file)

print("\nThree worst queries:")

for item in worst_queries:

    print(
        f"\nQuery {item['id']}: {item['query']}"
    )

    print("Rank:", item["correct_rank"])

    print("MRR:", item["reciprocal_rank"])


print("\nRETRIEVAL EVALUATION COMPLETED!")
