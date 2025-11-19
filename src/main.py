import os

from dotenv import load_dotenv
from speakeasypy import Speakeasy

from agent import Agentv3 as Agent

if __name__ == "__main__":
    load_dotenv()

    SPARQL_ENDPOINT = "http://localhost:3030/atai/sparql"

    speakeasy = Speakeasy(
        host="https://speakeasy.ifi.uzh.ch",
        username=os.getenv("SPEAKEASY_USERNAME", ""),
        password=os.getenv("SPEAKEASY_PASSWORD", ""),
    )

    agent = Agent(speakeasy=speakeasy, sparql_endpoint=SPARQL_ENDPOINT)
    agent.run()
