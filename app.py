from fastapi import FastAPI, Query
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Pharmacy Hackathon Search API")

def get_conn():
    return psycopg2.connect(
        dbname="pharmacydb",
        user="lakshmik",
        password="",
        host="localhost",
        port="5432"
    )

@app.get("/")
def home():
    return {"message": "Pharmacy Hackathon Search API is running!"}

# -------------------
# Search Endpoints
# -------------------

@app.get("/search/prefix")
def prefix_search(q: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE lower(name) LIKE lower(%s)
        ORDER BY lower(name)
        LIMIT 20;
    """, (q + "%",))
    results = [row["name"] for row in cur.fetchall()]
    cur.close(); conn.close()
    return {"results": results}

@app.get("/search/substring")
def substring_search(q: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE name ILIKE %s
        ORDER BY similarity(name, %s) DESC
        LIMIT 20;
    """, ("%" + q + "%", q))
    results = [row["name"] for row in cur.fetchall()]
    cur.close(); conn.close()
    return {"results": results}

@app.get("/search/fulltext")
def fulltext_search(q: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE search_tsv @@ plainto_tsquery('english', %s)
        ORDER BY ts_rank(search_tsv, plainto_tsquery('english', %s)) DESC
        LIMIT 20;
    """, (q, q))
    results = [row["name"] for row in cur.fetchall()]
    cur.close(); conn.close()
    return {"results": results}

@app.get("/search/fuzzy")
def fuzzy_search(q: str = Query(...)):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT name
        FROM medicines
        WHERE similarity(lower(name), lower(%s)) > 0.2
        ORDER BY similarity(lower(name), lower(%s)) DESC, lower(name)
        LIMIT 20;
    """, (q, q))
    results = [row["name"] for row in cur.fetchall()]
    cur.close(); conn.close()
    return {"results": results}
