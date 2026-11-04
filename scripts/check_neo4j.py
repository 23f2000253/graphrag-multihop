import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

if not (uri and user and password):
    raise SystemExit("Missing NEO4J_URI, NEO4J_USER or NEO4J_PASSWORD in .env")

with GraphDatabase.driver(uri, auth=(user, password)) as driver:
    driver.verify_connectivity()
    records, summary, keys = driver.execute_query(
        "RETURN 'hello from python' AS message"
    )
    print(records[0]["message"])
