# try_agent.py
from career_agent import build_agent

agent = build_agent(verbose=True)

print("\n--- Query 1 ---")
print(agent.run("What skills are needed for   DATA     scientist?"))

print("\n--- Query 2 ---")
print(agent.run("Which job suits someone who knows Python and SQL?"))
