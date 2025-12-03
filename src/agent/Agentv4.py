from random import choice

from speakeasypy import Chatroom, EventType, Speakeasy

from core import KnowledgeGraph

from .Message import Message
from .Response import Response


class Agentv4:

    def __init__(self, speakeasy: Speakeasy, sparql_endpoint: str):
        self.__speakeasy = speakeasy
        self.__knowledge_graph = KnowledgeGraph(sparql_endpoint)

        print("Loading entities...")
        self.__knowledge_graph.entities  # Preload entities
        print("Entities loaded.")

        print("Loading relations...")
        self.__knowledge_graph.relations  # Preload relations
        print("Relations loaded.")

        self.__speakeasy.login()
        self.__speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)

        self.__thinking_messages = [
            "I'm on it!",
            "Let me check that for you.",
            "Thinking...",
            "Consulting the knowledge base...",
            "Let me see what I can find.",
            "I'm looking into it now.",
            "Just a second, processing your request.",
            "Let me think about that for a moment.",
            "Searching for the answer...",
            "Analyzing your question...",
            "Hold on, I'm gathering information for you.",
            "One moment, please.",
            "Let me find that out for you.",
            "I'm working on it right now.",
        ]

        self.__answers_cache = {}

    def run(self):
        self.__speakeasy.start_listening()

    def on_new_message(self, content: str, room: Chatroom):
        if content in self.__answers_cache:
            room.post_messages(self.__answers_cache[content])
            return

        room.post_messages(choice(self.__thinking_messages))

        message = Message(content, self.__knowledge_graph)
        print(repr(message))

        response = Response(message, self.__knowledge_graph)
        print(repr(response))

        room.post_messages(response)
        self.__answers_cache[content] = response
