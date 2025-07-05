from neo4j import GraphDatabase
import os

# Replace with your Aura DB info
uri = os.getenv("DB_URL")
user = "neo4j"
password = os.getenv("DB_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))

def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Connected to Aura!' AS message")
        print(result.single()["message"])

#test_connection()



def create_constraints():
    queries = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (j:JobRole) REQUIRE j.title IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Course) REQUIRE c.title IS UNIQUE",
    ]
    with driver.session() as session:
        for q in queries:
            session.run(q)
    print("Constraints created.")

#create_constraints()


def add_sample_graph():
    with driver.session() as session:
        session.run("""
            MERGE (user:User {name: 'Nandan', email: 'nandan@example.com'})
            MERGE (job:JobRole {title: 'Data Scientist'})
            MERGE (skill1:Skill {name: 'Python'})
            MERGE (skill2:Skill {name: 'Machine Learning'})
            MERGE (course1:Course {title: 'Python Basics', url: 'https://example.com/python'})
            MERGE (course2:Course {title: 'Intro to ML', url: 'https://example.com/ml'})
            MERGE (user)-[:AIM_FOR]->(job)
            MERGE (job)-[:REQUIRES]->(skill1)
            MERGE (job)-[:REQUIRES]->(skill2)
            MERGE (skill1)-[:LEARNED_BY]->(course1)
            MERGE (skill2)-[:LEARNED_BY]->(course2)
            MERGE (user)-[:HAS_SKILL]->(skill1)
        """)
    print("Sample data added.")

add_sample_graph()
