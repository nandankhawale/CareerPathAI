# vector_embed_jobs.py

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import chromadb
import os

# ── Load Neo4j connection ──
uri = os.getenv("DB_URL")
user = "neo4j"
password = os.getenv("DB_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password))

# ── Step 1: Fetch data ──
def fetch_job_skill_docs():
    docs = []
    ids = []
    with driver.session() as session:
        result = session.run("""
            MATCH (j:JobRole)-[:REQUIRES]->(s:Skill)
            RETURN j.title AS job, collect(s.name) AS skills
        """)
        for record in result:
            job = record["job"]
            skills = ", ".join(record["skills"])
            text = f"Job: {job} requires skills: {skills}"
            docs.append(text)
            ids.append(job)
    return docs, ids

# ── Step 2: Create embeddings ──
def embed_documents(documents):
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return embedder.encode(documents).tolist()

# ── Step 3: Store in ChromaDB ──
def store_in_chroma(docs, embeddings, ids):
    #client = chromadb.Client()
    client = chromadb.PersistentClient(path="./chroma") 
    collection = client.create_collection(name="job_roles")

    collection.add(
        documents=docs,
        embeddings=embeddings,
        ids=ids
    )
    print(f"✅ Stored {len(docs)} documents in ChromaDB")

# ── Execute Steps ──
docs, ids = fetch_job_skill_docs()
embeddings = embed_documents(docs)
store_in_chroma(docs, embeddings, ids)
