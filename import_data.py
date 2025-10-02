import os
import json
import psycopg2

# Path to the folder containing all JSON files (update if different)
DATA_DIR = "/Users/lakshmik/pharmacy-hackathon/data/DB_Dataset/DB_Dataset/data"




# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="pharmacydb",
    user="lakshmik",   # 👈 use your mac login name
    password="",       # keep empty if no password set
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Step 1: Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS medicines (
    id TEXT PRIMARY KEY,
    sku_id TEXT,
    name TEXT,
    manufacturer_name TEXT,
    marketer_name TEXT,
    type TEXT,
    price NUMERIC,
    pack_size_label TEXT,
    short_composition TEXT,
    is_discontinued BOOLEAN,
    available BOOLEAN
);
""")
conn.commit()

# Step 2: Loop through all JSON files
for filename in sorted(os.listdir(DATA_DIR)):
    if filename.endswith(".json"):
        file_path = os.path.join(DATA_DIR, filename)
        print(f"Importing {file_path} ...")
        with open(file_path, "r") as f:
            medicines = json.load(f)  # Expecting list of dicts
            for med in medicines:
                cur.execute("""
                    INSERT INTO medicines (
                        id, sku_id, name, manufacturer_name, marketer_name,
                        type, price, pack_size_label, short_composition,
                        is_discontinued, available
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                """, (
                    med.get("id"),
                    med.get("sku_id"),
                    med.get("name"),
                    med.get("manufacturer_name"),
                    med.get("marketer_name"),
                    med.get("type"),
                    med.get("price"),
                    med.get("pack_size_label"),
                    med.get("short_composition"),
                    med.get("is_discontinued"),
                    med.get("available"),
                ))
        conn.commit()

print("✅ All data imported successfully!")

cur.close()
conn.close()
