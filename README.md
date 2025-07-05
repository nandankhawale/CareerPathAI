# 🧠 CareerPath AI – Your Personalized Career Guide

Welcome to **CareerPath AI**, an intelligent, LLM-powered career advisor that helps users identify suitable job roles based on their current skills or uploaded resumes — and recommends what to learn next.

🚀 Built with:
- **Groq (LLM)** for skill and job-related reasoning
- **Neo4j Aura** as a knowledge graph for job-skill relationships
- **ChromaDB** for semantic job recommendation using embeddings
- **LangChain** to orchestrate tools + LLM agents
- **Streamlit** for an intuitive, chat-based user interface

---

## 🔍 What Can You Do with CareerPath AI?

✅ Upload your resume and extract skills  
✅ Ask: *“What job suits me if I know Python and SQL?”*  
✅ Get recommended job roles that match your skills  
✅ Discover missing skills for your dream job  
✅ Learn what to study using AI-powered suggestions

---

## 🧠 How It Works

1. **Resume Parsing**: Upload your PDF resume, and the system extracts tech skills using an LLM (`qwen-qwq-32b` via Groq).
2. **Graph Update**: Your skills are added to the Neo4j graph and linked to matching job roles.
3. **Semantic Search**: Your skills are converted into vector embeddings and used to query relevant job roles via ChromaDB.
4. **LangChain Agent**: A powerful LangChain agent decides when to use the knowledge graph or vector search depending on your question.

---

## ✨ Example Questions

> 🧠 _“What skills are required to become a Machine Learning Engineer?”_

> 💡 _“What job roles match someone who knows Python, SQL, and Excel?”_

> 📄 _Upload your resume and get a personalized answer._

---

## 🗂️ Tech Stack

| Layer | Tool |
|-------|------|
| LLM | [Groq API](https://console.groq.com) – `qwen-qwq-32b` |
| Embeddings | `all-MiniLM-L6-v2` (via sentence-transformers) |
| Vector DB | [ChromaDB](https://docs.trychroma.com/) |
| Graph DB | [Neo4j AuraDB Free](https://neo4j.com/cloud/aura/) |
| Framework | [LangChain](https://www.langchain.com/) |
| Frontend | [Streamlit](https://streamlit.io/) |


---

## 🔐 API Keys & Configuration

To run this app, you'll need:

| Secret | Use |
|--------|-----|
| `GROQ_API_KEY` | Required to call Groq LLMs |
| `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` | For Neo4j connection |

Add these in **Hugging Face Spaces → Settings → Secrets**.

---

