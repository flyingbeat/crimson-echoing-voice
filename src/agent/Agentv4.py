from random import choice

from openapi.models.chat_message_reaction_type import ChatMessageReactionType
from openapi.models.rest_chat_message import RestChatMessage
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
        self.__speakeasy.register_callback(self.on_new_reaction, EventType.REACTION)

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

    def on_new_reaction(
        self, reaction: ChatMessageReactionType, message_ordinal: int, room: Chatroom
    ):
        print(f"Reaction(type={reaction}, message_ordinal={message_ordinal})")
        match reaction:
            case ChatMessageReactionType.THUMBS_DOWN:
                chat_message = self.__get_message_by_ordinal(message_ordinal, room)
                if chat_message is not None:
                    self.__remove_cached_answer(chat_message.message)
            case _:
                pass

    def __remove_cached_answer(self, answer_string: str):
        for question, answer in self.__answers_cache.items():
            if answer_string == answer:
                print(f"Removing cached answer for question: {question}")
                del self.__answers_cache[question]
                break

    def __get_message_by_ordinal(
        self, ordinal: int, room: Chatroom
    ) -> RestChatMessage | None:
        filtered = list(
            filter(
                lambda m: m.ordinal == ordinal,
                room.get_messages(only_new=False, only_partner=False),
            )
        )
        if len(filtered) == 1:
            return filtered[0]
        return None
