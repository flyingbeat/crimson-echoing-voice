import os
import time
from dotenv import load_dotenv
from rdflib import Graph
from speakeasypy import Chatroom, EventType, Speakeasy

DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
GRAPH_PATH = "/space_mounts/atai-hs25/dataset/graph.nt"


class Agent:
    def __init__(self, username: str, password: str):
        self.username = username
        self.speakeasy = Speakeasy(host=DEFAULT_HOST_URL, username=username, password=password)
        self.graph = self._load_graph(GRAPH_PATH)

        self.speakeasy.login()

        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)
        self.speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)


    def listen(self):
        self.speakeasy.start_listening()


    def on_new_reaction(self, reaction: str, message_ordinal: int, room: Chatroom):
        print(f"[{self.get_time()}] Reaction '{reaction}' on message #{message_ordinal} in room {room.room_id}")
        room.post_messages(f"👍 Thanks for your reaction: '{reaction}'")


    def on_new_message(self, message: str, room: Chatroom):
        print(f"[{self.get_time()}] New query in room {room.room_id}: {message}")

        if not self.graph:
            room.post_messages("⚠️ Graph is not loaded. Cannot process SPARQL query.")
            return

        cleaned_query = self._clean_query(message)
        if not cleaned_query:
            room.post_messages("⚠️ The query is empty or invalid after cleaning.")
            return

        self._execute_query(cleaned_query, room)


    def _execute_query(self, query: str, room: Chatroom):
        try:
            results = self.graph.query(query)
            result_list = [", ".join(str(item) for item in row) for row in results]

            if not result_list:
                room.post_messages("⚠️ I ran the query, but there are no results.")
                return

            response_text = self._format_results(result_list)
            room.post_messages(response_text)

        except Exception as e:
            room.post_messages(f"⚠️ Sorry, I couldn't process that query. Error: {e}")


    @staticmethod
    def _load_graph(path: str) -> Graph | None:
        graph = Graph()
        try:
            graph.parse(path, format="nt")
            print("Graph loaded successfully.")
            return graph
        except FileNotFoundError:
            print(f"Error: Graph file not found at {path}")
        except Exception as e:
            print(f"Failed to load graph: {e}")
        return None


    @staticmethod
    def _clean_query(raw_message: str) -> str:
        lines = [
            line for line in raw_message.splitlines()
            if not line.strip().startswith("#")
        ]
        query = "\n".join(lines).strip()

        if query.startswith("'''") and query.endswith("'''"):
            query = query[3:-3].strip()

        return query


    @staticmethod
    def _format_results(results: list[str]) -> str:
        if len(results) == 1:
            return f"Here is the result I found: {results[0]}"
        formatted = "\n- ".join(results)
        return f"I found multiple results for your query:\n- {formatted}"


    @staticmethod
    def get_time() -> str:
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == "__main__":
    load_dotenv()

    agent = Agent(os.getenv("SPEAKEASY_USERNAME", ""), os.getenv("SPEAKEASY_PASSWORD", ""))
    agent.listen()