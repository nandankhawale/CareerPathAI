# ── Load local file into Python list[dict] ────────────────────────────────────
from neo4j import GraphDatabase
import os
import json      # ← add this
# Replace with your Aura DB info
uri = os.getenv("DB_URL")
user = "neo4j"
password = os.getenv("DB_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))



def load_local_data(path: str, fmt: str = "jsonl"):
    """Return list of {'job_title': str, 'skills': list[str]}"""
    records = []

    if fmt == "jsonl":
        with open(path, "r", encoding="utf‑8") as f:
            for line in f:
                obj = json.loads(line)
                records.append(obj)

    else:
        raise ValueError("fmt must be 'jsonl' or 'csv'")

    return records

# ── Insert into Neo4j in efficient batches ───────────────────────────────────
QUERY = """
UNWIND $batch AS row
MERGE (j:JobRole {title: row.job})
WITH j, row.skills AS skills
UNWIND skills AS skill_name
MERGE (s:Skill {name: skill_name})
MERGE (j)-[:REQUIRES]->(s);
"""

def insert_data_from_file(path: str, fmt: str = "jsonl", batch_size: int = 500):
    data = load_local_data(path, fmt)
    total = len(data)

    with driver.session() as session:
        for i in range(0, total, batch_size):
            batch = [
                {"job": rec["job_title"], "skills": rec["skills"]}
                for rec in data[i : i + batch_size]
                if rec["job_title"] and rec["skills"]
            ]
            session.run(QUERY, batch=batch)

    print(f"✅ Inserted {total:,} job‑role rows into Neo4j")

# ── Run it ────────────────────────────────────────────────────────────────────
# Example: JSONL
insert_data_from_file("processed_job_skills.jsonl", fmt="jsonl")

