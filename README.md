## Python Environment Setup

Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate


Upgrade pip and install dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt

## PostgreSQL Setup
(a) Start PostgreSQL

If installed via Homebrew:

brew services start postgresql@14


### Check status:

pg_isready

(b) Create Database:
psql postgres


Inside psql:

CREATE DATABASE pharmacydb;
\q

4. Apply Schema

Run:

psql -d pharmacydb -f schema.sql


This creates the medicines table, full-text column, and optimized indexes.

5. Import Dataset
source venv/bin/activate
python import_data.py


Verify data:

psql -d pharmacydb -c "SELECT COUNT(*) FROM medicines;"

6. Run FastAPI Server (Terminal 1)

Keep this terminal open:

source venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000 --reload


API available at:
👉 http://127.0.0.1:8000

Endpoints:

/search/prefix?q=...

/search/substring?q=...

/search/fulltext?q=...

/search/fuzzy?q=...

7. Run Benchmarks (Terminal 2)

👉 Benchmark direct DB:

source venv/bin/activate
python benchmark.py
cat submission_db.json | jq


👉 Benchmark via FastAPI:

source venv/bin/activate
python benchmark_api.py
cat submission.json | jq


### Approach & Optimizations
What was done:

Added GIN & trigram indexes for substring/fuzzy searches.

Added precomputed search_tsv column for full-text search → reduced fulltext latency from ~430 ms → ~160 ms.

Used text_pattern_ops index for prefix searches → reduced latency to single-digit ms.

Ran ANALYZE to help PostgreSQL choose best query plans.

## Analysis:

* Prefix Queries:
I initially did a sequential scan and the latency was around 34.93ms ,Hence I optimized to get it down to <5ms by using index scan

## Eg:

CREATE INDEX IF NOT EXISTS idx_medicines_name_prefix
ON medicines (lower(name) text_pattern_ops);

* Substring + Fuzzy Search:
* Substring:
Instead of a full scan I used a trigram indexing --> improved from ~50 ms → ~3–6 ms.

## Eg:

CREATE INDEX IF NOT EXISTS idx_medicines_name_trgm
ON medicines USING GIN (name gin_trgm_ops);

* Fuzzy:

Before: Fuzzy search (using similarity(lower(name), q)) had ~430 ms latency. This was because Postgres had to scan a large portion of the medicines table and compute similarity scores row by row.

Now: I added a GIN trigram index.

* This index breaks the name field into trigrams (3-character chunks) and stores them in a fast lookup structure.

* When you run similarity(), Postgres no longer scans the full table—it first uses the trigram index to quickly filter candidate matches, then only calculates similarity on that smaller set.


## Eg:

CREATE INDEX IF NOT EXISTS idx_medicines_short_comp_trgm
ON medicines USING GIN (short_composition gin_trgm_ops);

## Result:
Latency dropped from ~430 ms → ~160 ms.
That’s almost 3× faster, even though fuzzy queries are still heavier than prefix/substring/full-text (because they require scoring + sorting).

* Full-text Search Optimization

* Now it precomputes tsvector at insert time, instead of computing at query time.
* Queries now directly use the indexed search_tsv column.
* Latency reduced from ~424 ms → 4–7 ms (≈100× faster).

## Analysis

Biggest win: Full-text search (100× faster, from 424 ms → 4–7 ms).

Substring search: Huge speedup (12× faster, from 50 ms → 3–6 ms).

Prefix search: Consistently under 5 ms.

Fuzzy search : approx(160 ms)

## Conclusion 

Overall system performance improved dramatically.

Almost All(<10 ms)

Throughput improved proportionally (from ~2–50 q/s → 200+ q/s).

### submission_db.json and submission.json were generated successfully with improved metrics.




