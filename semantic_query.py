# semantic_query.py

from sentence_transformers import SentenceTransformer
import chromadb

# ── Load embedding model ──
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# ── Load Chroma collection ──
#client = chromadb.Client()
client = chromadb.PersistentClient(path="./chroma") 
collection = client.get_collection(name="job_roles")

# ── Query string ──
query = "What jobs need Python and statistics?"
query_embedding = embedder.encode([query]).tolist()

# ── Search top 3 results ──
results = collection.query(
    query_embeddings=query_embedding,
    n_results=3
)

# ── Print results ──
print("🔍 Top Matches:")
for r in results['documents'][0]:
    print("-", r)
