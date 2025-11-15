import os

from dotenv import load_dotenv
from speakeasypy import Speakeasy

from Agentv3 import Agent
from KnowledgeGraph import KnowledgeGraph

if __name__ == "__main__":
    load_dotenv()

    SPARQL_ENDPOINT = "http://localhost:3030/atai/sparql"
    DATA_DIR = "/space_mounts/atai-hs25/dataset/embeddings"
    QUERY_TIMEOUT_SECONDS = 10

    speakeasy = Speakeasy(
        host="https://speakeasy.ifi.uzh.ch",
        username=os.getenv("SPEAKEASY_USERNAME", ""),
        password=os.getenv("SPEAKEASY_PASSWORD", ""),
    )

    agent = Agent(speakeasy=speakeasy, sparql_endpoint=SPARQL_ENDPOINT)
    agent.run()
