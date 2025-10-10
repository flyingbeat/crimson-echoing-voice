import time
from dotenv import load_dotenv
import os
from rdflib import Graph

from speakeasypy import Chatroom, EventType, Speakeasy

DEFAULT_HOST_URL = "https://speakeasy.ifi.uzh.ch"
GRAPH_PATH = "/space_mounts/atai-hs25/dataset/graph.nt"


class Agent:
    def __init__(self, username, password):
        self.username = username
        self.speakeasy = Speakeasy(
            host=DEFAULT_HOST_URL, username=username, password=password
        )
        self.speakeasy.login()

        self.graph = Graph()
        try:
            self.graph.parse(GRAPH_PATH, format="nt")
            print("Graph loaded successfully.")
        except FileNotFoundError:
            print(f"Error: Graph file not found at {GRAPH_PATH}")
            self.graph = None

        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)
        self.speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)

    def listen(self):
        self.speakeasy.start_listening()

    def on_new_message(self, message: str, room: Chatroom):
        print(f"New query in room {room.room_id}: {message}")

        if not self.graph:
            room.post_messages("Graph is not loaded. Cannot process SPARQL query.")
            return

        try:
            results = self.graph.query(message)

            if not results:
                room.post_messages("Query executed successfully, but returned no results.")
                return

            response_lines = []

            for row in results:
                response_lines.append(", ".join(str(item) for item in row))

            response_text = "\n".join(response_lines)
            room.post_messages(f"{response_text}")

        except Exception as e:
            room.post_messages(f"Sorry, I couldn't process that query. Error: {e}")

    def on_new_reaction(self, reaction: str, message_ordinal: int, room: Chatroom):
        print(
            f"New reaction '{reaction}' on message #{message_ordinal} in room {room.room_id}"
        )
        room.post_messages(f"Thanks for your reaction: '{reaction}'")

    @staticmethod
    def get_time():
        return time.strftime("%H:%M:%S, %d-%m-%Y", time.localtime())


if __name__ == "__main__":
    load_dotenv()
    username = os.getenv("SPEAKEASY_USERNAME", "")
    password = os.getenv("SPEAKEASY_PASSWORD", "")
    demo_bot = Agent(username, password)
    demo_bot.listen()
