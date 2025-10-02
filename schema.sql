CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

DROP TABLE IF EXISTS medicines;
CREATE TABLE medicines (
    id TEXT PRIMARY KEY,
    sku_id TEXT,
    name TEXT NOT NULL,
    manufacturer_name TEXT,
    marketer_name TEXT,
    type TEXT,
    price NUMERIC,
    pack_size_label TEXT,
    short_composition TEXT,
    is_discontinued BOOLEAN,
    available BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT now(),

    -- ✅ Precomputed tsvector for full-text search
    search_tsv tsvector GENERATED ALWAYS AS (
        to_tsvector(
            'english',
            coalesce(name,'') || ' ' ||
            coalesce(short_composition,'') || ' ' ||
            coalesce(manufacturer_name,'')
        )
    ) STORED
);

-- Prefix
CREATE INDEX IF NOT EXISTS idx_medicines_name_prefix
ON medicines (lower(name) text_pattern_ops);

-- Substring + fuzzy (GIN + trigram)
CREATE INDEX IF NOT EXISTS idx_medicines_name_trgm
ON medicines USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_medicines_short_comp_trgm
ON medicines USING GIN (short_composition gin_trgm_ops);

-- Full-text
CREATE INDEX IF NOT EXISTS idx_medicines_search_tsv
ON medicines USING GIN (search_tsv);

-- Support
CREATE INDEX IF NOT EXISTS idx_medicines_avail ON medicines (available);
CREATE INDEX IF NOT EXISTS idx_medicines_discontinued ON medicines (is_discontinued);

ANALYZE medicines;
