# career_agent.py
"""
Builds a LangChain agent with:
• Neo4j tool  -> look up skills for a job
• Chroma tool -> semantic job search by skills
• Groq LLM    -> reasoning / response
"""
import re
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from neo4j import GraphDatabase
from langchain.tools import tool
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType

from sentence_transformers import SentenceTransformer
import chromadb
load_dotenv()
GROQ_API_KEY=os.getenv("GROQ_API_KEY")

# ── ENVIRONMENT ───────────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("DB_URL")
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = os.getenv("DB_PASSWORD")
CHROMA_PATH    = "./chroma"                     # same path used earlier

# ── Neo4j driver ──────────────────────────────────────────────────────────────
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

@tool
def get_skills_for_job(job_title: str) -> str:
    """Returns required skills for a job role (case-insensitive, ignores extra spaces)."""
    # Normalize input: remove extra spaces and lowercase
    normalized_title = re.sub(r'\s+', ' ', job_title).strip().lower()

    with driver.session() as session:
        result = session.run(
            """
            MATCH (j:JobRole)
            WHERE toLower(replace(j.title, "  ", " ")) = $normalized_title
            OPTIONAL MATCH (j)-[:REQUIRES]->(s:Skill)
            RETURN j.title AS actualTitle, collect(s.name) AS skills
            """,
            normalized_title=normalized_title
        ).single()

    if result and result["skills"]:
        return f"Skills for {result['actualTitle']}: {', '.join(result['skills'])}"
    else:
        return f"No skills found for {job_title}."

# ── ChromaDB semantic search tool ─────────────────────────────────────────────
@tool
def search_job_by_skills(skill_query: str) -> str:
    """Return job roles relevant to a skill query (semantic search)."""
    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_collection("job_roles")   # created earlier

    embedding = model.encode([skill_query]).tolist()
    res = collection.query(query_embeddings=embedding, n_results=3)

    return "\n".join(res["documents"][0])

# ── Groq LLM ──────────────────────────────────────────────────────────────────
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY")
    
    model_name="qwen-qwq-32b"
)
# ── Assemble agent ────────────────────────────────────────────────────────────
def build_agent(verbose: bool = True):
    tools = [get_skills_for_job, search_job_by_skills]
    return initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
    )

# Allow quick CLI use
if __name__ == "__main__":
    agent = build_agent()
    while True:
        q = input("Ask me anything about careers → ")
        if not q:
            break
        print(agent.run(q), "\n")
