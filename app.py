import os
import streamlit as st
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
import chromadb
from langchain_groq import ChatGroq
import fitz  # PyMuPDF for PDF processing
import re
from dotenv import load_dotenv

# === LOAD ENV VARS ===
load_dotenv()  # Load environment variables from .env file
# === ENV VARS ===

# === Neo4j Tool ===
uri = os.getenv("DB_URL")
user = "neo4j"
password = os.getenv("DB_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password))

# === Initialize LLM ===
llm = ChatGroq(model_name="qwen-qwq-32b", groq_api_key=os.environ["GROQ_API_KEY"])

# === PDF Processing Functions ===
def extract_text_from_pdf(file):
    """Extract text from uploaded PDF file"""
    text = ""
    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def extract_skills_with_llm(text):
    """Extract skills from resume text using Groq LLM"""
    prompt = (
        "You are a skill extraction assistant. Extract ONLY technical skills from the resume text below. "
        "Return ONLY a comma-separated list of skills with NO explanations, NO thinking process, NO additional text.\n"
        "Example response format: Python, JavaScript, React, SQL, Docker\n\n"
        f"Resume text:\n{text}\n\n"
        "Skills (comma-separated only):"
    )
    try:
        response = llm.invoke(prompt)
        # Handle different response formats
        if hasattr(response, 'content'):
            skills_text = response.content
        else:
            skills_text = str(response)
        
        # Clean up the response
        skills_text = skills_text.strip()
        
        # Remove thinking process if it exists (look for <think> tags or similar patterns)
        if '<think>' in skills_text and '</think>' in skills_text:
            # Extract only the part after </think>
            skills_text = skills_text.split('</think>')[-1].strip()
        
        # Remove common prefixes and suffixes
        skills_text = re.sub(r'^(Skills?:?\s*)', '', skills_text, flags=re.IGNORECASE)
        skills_text = re.sub(r'\n.*', '', skills_text)  # Remove everything after first newline
        
        # If the response is too long (likely contains explanations), try to extract just the skills
        if len(skills_text) > 500:
            # Look for the actual skills list pattern
            lines = skills_text.split('\n')
            for line in lines:
                if ',' in line and len(line.split(',')) > 3:  # Likely a skills list
                    skills_text = line.strip()
                    break
        
        return skills_text
    except Exception as e:
        st.error(f"Error extracting skills: {e}")
        return ""

def update_user_skills(user_email, skill_list):
    """Update Neo4j graph with user skills"""
    try:
        with driver.session() as session:
            for skill in skill_list:
                skill = skill.strip().title()
                if skill:  # Only process non-empty skills
                    session.run("""
                        MERGE (u:User {email: $email})
                        MERGE (s:Skill {name: $skill})
                        MERGE (u)-[:HAS_SKILL]->(s)
                    """, email=user_email, skill=skill)
        return True
    except Exception as e:
        st.error(f"Error updating user skills: {e}")
        return False

def recommend_jobs_from_skills(skill_list):
    """Recommend jobs based on extracted skills using Chroma semantic search"""
    try:
        query = "Skills: " + ", ".join(skill_list)
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Use the same persistent directory as fetchdata.py
        client = chromadb.PersistentClient(path="./chroma")
        
        # Make sure the collection exists
        try:
            collection = client.get_collection("job_roles")
        except chromadb.errors.NotFoundError:
            return ["Job‑roles collection is empty. Run fetchdata.py first."]
        
        embedding = model.encode([query]).tolist()
        results = collection.query(query_embeddings=embedding, n_results=5)
        
        if results["documents"] and results["documents"][0]:
            return results["documents"][0]
        else:
            return ["No matching job roles found."]
    except Exception as e:
        st.error(f"Error recommending jobs: {e}")
        return ["Error occurred while searching for jobs."]

# === Original Tools ===
@tool
def get_skills_for_job(job_title: str) -> str:
    """Returns required skills for a job role."""
    with driver.session() as session:
        result = session.run("""
            MATCH (j:JobRole {title: $title})-[:REQUIRES]->(s:Skill)
            RETURN collect(s.name) AS skills
        """, title=job_title)
        record = result.single()
        if record and record["skills"]:
            return f"Skills for {job_title}: {', '.join(record['skills'])}"
        return "No skills found."

@tool
def search_job_by_skills(skill_query: str) -> str:
    """Returns job roles relevant to a skill query using semantic search."""
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Use the SAME persistent directory as fetchdata.py
    client = chromadb.PersistentClient(path="./chroma")

    # Make sure the collection exists
    try:
        collection = client.get_collection("job_roles")
    except chromadb.errors.NotFoundError:
        return "Job‑roles collection is empty. Run fetchdata.py first."

    embedding = model.encode([skill_query]).tolist()
    results = collection.query(query_embeddings=embedding, n_results=3)
    return "\n".join(results["documents"][0])

# === Agent Setup ===
tools = [get_skills_for_job, search_job_by_skills]
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False
)

# === Streamlit UI ===
st.set_page_config(page_title="CareerPath AI", page_icon="🧠")
st.title("🧠 CareerPathAI – Your Career Advisor")

# === Navigation Tabs ===
tab1, tab2 = st.tabs(["💬 Ask Questions", "📄 Resume Analysis"])

# === Tab 1: Original Chat Interface ===
with tab1:
    st.markdown("Ask me career questions like:")
    st.markdown("- _What skills are needed for a Data Scientist?_")
    st.markdown("- _Which job suits someone who knows Python and SQL?_")

    user_query = st.text_input("💬 Your Question")
    submit = st.button("🚀 Ask AI")

    if submit and user_query:
        with st.spinner("Thinking... 🤔"):
            try:
                response = agent.run(user_query)
                st.success(response)
            except Exception as e:
                st.error(f"❌ Error: {e}")

# === Tab 2: Resume Analysis ===
with tab2:
    st.subheader("📄 Upload Your Resume")
    st.markdown("Upload your PDF resume to get personalized job recommendations!")
    
    # User email input
    user_email = st.text_input("📧 Your Email", value="user@example.com", 
                              help="This will be used to save your skills in the database")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload PDF resume", type=["pdf"])
    
    if uploaded_file is not None:
        st.info("📖 Extracting resume text...")
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(uploaded_file)
        
        if resume_text:
            # Show extracted text (optional, for debugging)
            with st.expander("📝 View Extracted Text"):
                st.text_area("Resume Text", resume_text, height=200)
            
            st.info("🧠 Extracting skills using Groq AI...")
            
            # Extract skills using LLM
            raw_skills = extract_skills_with_llm(resume_text)
            
            if raw_skills:
                # Process skills into a list
                skill_list = [s.strip() for s in raw_skills.split(",") if s.strip()]
                
                if skill_list:
                    st.success(f"✅ Extracted Skills: {', '.join(skill_list)}")
                    
                    # Save to Neo4j
                    st.info("💾 Saving skills to database...")
                    if update_user_skills(user_email, skill_list):
                        st.success("✅ Skills saved successfully!")
                        
                        # Recommend Jobs
                        st.info("🔍 Recommending job roles based on your skills...")
                        job_matches = recommend_jobs_from_skills(skill_list)
                        
                        if job_matches:
                            st.success("🎯 Here are job roles that match your resume:")
                            for i, job in enumerate(job_matches, 1):
                                st.write(f"**{i}.** {job}")
                        else:
                            st.warning("No job matches found. Try running fetchdata.py first.")
                    else:
                        st.error("Failed to save skills to database.")
                else:
                    st.warning("No skills could be extracted from the resume.")
            else:
                st.error("Failed to extract skills from the resume.")
        else:
            st.error("Failed to extract text from the PDF.")

# === Footer ===
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit, LangChain, Neo4j, and Groq")