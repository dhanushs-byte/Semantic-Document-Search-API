
import time
import statistics
import json
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

# Load environment variables from project root
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("API_KEY")

URL = "http://127.0.0.1:8000/search"

if not API_KEY:
    print("ERROR: API_KEY not found in .env")
    sys.exit(1)

HEADERS = {
    "x-api-key": API_KEY
}


# ==========================================
# 2. EVALUATION QUERIES
# ==========================================

QUERIES = [
    "How can I apply for leave?",
    "What is sick leave?",
    "How do I reset my password?",
    "What are the working hours?",
    "How can I work remotely?",
    "What is the annual leave policy?",
    "How do managers approve leave?",
    "How can I access my account?",
    "What are the attendance rules?",
    "How do I protect my account?",
    "How many hours should employees work?",
    "Can employees work from home?",
    "How do I recover my password?",
    "What happens when I apply for sick leave?",
    "Who approves employee leave?",
    "How do I check my leave balance?",
    "What is the company work schedule?",
    "How can I secure my password?",
    "What is the remote work policy?",
    "How do I submit a leave application?"
]


# ==========================================
# 3. LATENCY MEASUREMENT
# ==========================================

latencies = []

print("\n===================================")
print(" SEMANTIC SEARCH LATENCY TEST")
print("===================================")

print("Total searches: 20")
print("API URL:", URL)

try:

    with httpx.Client(timeout=60) as client:

        for i, query in enumerate(QUERIES, start=1):

            payload = {
                "query": query,
                "top_k": 5
            }

            print(f"\nSearch {i}: {query}")

            start_time = time.perf_counter()

            response = client.post(
                URL,
                headers=HEADERS,
                json=payload
            )

            end_time = time.perf_counter()

            # Check API response
            if response.status_code != 200:

                print(
                    "API ERROR:",
                    response.status_code,
                    response.text
                )

                print("\nLatency measurement stopped.")
                sys.exit(1)

            latency = (
                end_time - start_time
            ) * 1000

            latencies.append(latency)

            print(
                f"Response time: {latency:.2f} ms"
            )

except httpx.ConnectError:

    print("\nERROR: Cannot connect to FastAPI.")
    print("Start your server using:")
    print("python -m uvicorn main:app")

    sys.exit(1)

except httpx.TimeoutException:

    print("\nERROR: API request timed out.")
    sys.exit(1)


# ==========================================
# 4. CALCULATE P50 AND P95
# ==========================================

if len(latencies) != 20:

    print("ERROR: Expected 20 successful searches.")
    sys.exit(1)

p50 = statistics.median(latencies)

p95 = float(np.percentile(latencies, 95))

average = statistics.mean(latencies)

minimum = min(latencies)

maximum = max(latencies)


# ==========================================
# 5. DISPLAY RESULTS
# ==========================================

print("\n===================================")
print("       LATENCY REPORT")
print("===================================")

print("Total searches:", len(latencies))

print(f"Average latency: {average:.2f} ms")

print(f"P50 latency: {p50:.2f} ms")

print(f"P95 latency: {p95:.2f} ms")

print(f"Minimum latency: {minimum:.2f} ms")

print(f"Maximum latency: {maximum:.2f} ms")

print("===================================")


# ==========================================
# 6. SAVE RESULTS TO JSON
# ==========================================

report = {
    "total_searches": len(latencies),
    "average_latency_ms": round(average, 2),
    "p50_ms": round(p50, 2),
    "p95_ms": round(p95, 2),
    "minimum_latency_ms": round(minimum, 2),
    "maximum_latency_ms": round(maximum, 2),
    "all_latencies_ms": [
        round(value, 2)
        for value in latencies
    ]
}

output_path = BASE_DIR / "latency_results.json"

with open(
    output_path,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        report,
        file,
        indent=4
    )

print("\nLatency report saved successfully!")

print("File location:", output_path)

print("\nTASK 2 LATENCY MEASUREMENT COMPLETED!")
