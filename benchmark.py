import json
import psycopg2
import time

# --- DB connection ---
def get_conn():
    return psycopg2.connect(
        dbname="pharmacydb",
        user="lakshmik",   # my mac login
        password="",
        host="localhost",
        port="5432"
    )

# --- Query runners ---
def run_prefix_search(cur, q):
    # ✅ uses prefix index
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE lower(name) LIKE lower(%s)
        ORDER BY lower(name)
        LIMIT 20;
    """, (q + '%',))
    return [r[0] for r in cur.fetchall()]

def run_substring_search(cur, q):
    # ✅ switched to trigram search (faster than plain LIKE for substrings)
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE name ILIKE %s
        ORDER BY similarity(name, %s) DESC
        LIMIT 20;
    """, ('%' + q + '%', q))
    return [r[0] for r in cur.fetchall()]

def run_fulltext_search(cur, q):
    # ✅ uses precomputed search_tsv column
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE search_tsv @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank(search_tsv, plainto_tsquery('english', %s)) DESC
        LIMIT 20;
    """, (q, q))
    return [r[0] for r in cur.fetchall()]

def run_fuzzy_search(cur, q):
    # ✅ trigram similarity with threshold filter
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE similarity(lower(name), lower(%s)) > 0.2
        ORDER BY similarity(lower(name), lower(%s)) DESC, lower(name)
        LIMIT 20;
    """, (q, q))
    return [r[0] for r in cur.fetchall()]

# --- Main ---
def main():
    with open("data/DB_Dataset/DB_Dataset/benchmark_queries.json", "r") as f:
        benchmark = json.load(f)

    conn = get_conn()
    cur = conn.cursor()
    # cur.execute("SET pg_trgm.similarity_threshold = 0.2;")

    results = {}
    metrics = {}

    for test in benchmark["tests"]:
        qtype = test["type"]
        query = test["query"]
        tid = str(test["id"])

        start = time.time()

        if qtype == "prefix":
            res = run_prefix_search(cur, query)
        elif qtype == "substring":
            res = run_substring_search(cur, query)
        elif qtype == "fulltext":
            res = run_fulltext_search(cur, query)
        elif qtype == "fuzzy":
            res = run_fuzzy_search(cur, query)
        else:
            res = []

        latency = (time.time() - start) * 1000  # ms
        results[tid] = res
        metrics[tid] = {"latency_ms": round(latency, 2), "count": len(res)}

        print(f"⏱️ {qtype} query '{query}' → {len(res)} results, {latency:.2f} ms")

    cur.close()
    conn.close()

    # Save submission_db.json
    with open("submission_db.json", "w") as f:
        json.dump({"results": results, "metrics": metrics}, f, indent=2)

    print("✅ submission_db.json created successfully!")

if __name__ == "__main__":
    main()
