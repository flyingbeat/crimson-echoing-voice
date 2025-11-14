import os

from dotenv import load_dotenv

from handlers.chatbot_handler import ChatbotHandler
from handlers.data_handler import DataHandler
from handlers.embedding_handler import EmbeddingHandler
from handlers.llm_handler import LLMHandler
from handlers.query_handler import QueryHandler
from handlers.sparql_hanlder import SparqlHandler
from handlers.recommendation_handler import RecommendationHandler

if __name__ == "__main__":
    load_dotenv()

    if os.name == "nt":
        print("Warning: The query timeout feature is not supported on Windows.")

    SPARQL_ENDPOINT = "http://localhost:3030/atai/sparql"
    DATA_DIR = "/space_mounts/atai-hs25/dataset/embeddings"
    QUERY_TIMEOUT_SECONDS = 10

    data_handler = DataHandler(sparql_endpoint=SPARQL_ENDPOINT, data_dir=DATA_DIR)
    sparql_handler = SparqlHandler(
        graph=data_handler.graph, query_timeout_seconds=QUERY_TIMEOUT_SECONDS
    )

    chatbot = ChatbotHandler(
        username=os.getenv("SPEAKEASY_USERNAME", ""),
        password=os.getenv("SPEAKEASY_PASSWORD", ""),
        data_handler=data_handler,
        sparql_handler=sparql_handler,
        embedding_handler=EmbeddingHandler(data_handler=data_handler),
        query_handler=QueryHandler(data_handler=data_handler),
        llm_handler=LLMHandler(),
        recommendation_handler=RecommendationHandler(sparql_handler=sparql_handler),
    )
    chatbot.listen()
