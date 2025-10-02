import json
import requests
import time

# Base URL of your FastAPI app
BASE_URL = "http://127.0.0.1:8000/search"  # change if deployed elsewhere

# Mapping query types to endpoints
ENDPOINTS = {
    "prefix": "prefix",
    "substring": "substring",
    "fulltext": "fulltext",
    "fuzzy": "fuzzy"
}

def run_query(qtype, q):
    """
    Call the FastAPI endpoint for the given query type and return results.
    """
    url = f"{BASE_URL}/{ENDPOINTS[qtype]}"
    try:
        resp = requests.get(url, params={"q": q})
        if resp.status_code == 200:
            return resp.json().get("results", [])
        else:
            print(f"Error {resp.status_code} for {qtype} query '{q}': {resp.text}")
            return []
    except Exception as e:
        print(f" Request failed for {qtype} query '{q}': {e}")
        return []

def main():
    # Load benchmark queries
    with open("data/DB_Dataset/DB_Dataset/benchmark_queries.json", "r") as f:
        benchmark = json.load(f)

    results = {}
    metrics = {}

    # Run each test
    for test in benchmark["tests"]:
        tid = str(test["id"])
        qtype = test["type"]
        query = test["query"]

        print(f"➡️ Running {qtype} {tid}: {query}")

        start = time.time()
        res = run_query(qtype, query)
        latency = (time.time() - start) * 1000  # ms

        results[tid] = res
        metrics[tid] = {"latency_ms": round(latency, 2), "count": len(res)}

        print(f"⏱️ {qtype} query '{query}' → {len(res)} results, {latency:.2f} ms")

    # Save results + metrics
    with open("submission.json", "w") as f:
        json.dump({"results": results, "metrics": metrics}, f, indent=2)

    print("✅ submission.json created (API version)!")

if __name__ == "__main__":
    main()
