import random
import time
from collections import Counter, defaultdict

from speakeasypy import Chatroom, EventType, Speakeasy

from Entity import Entity

# from handlers.llm_handler import LLMHandler
from KnowledgeGraph import KnowledgeGraph
from Message import Message
from Property import Property
from Recommendation import Recommendations


class Agent:

    def __init__(self, speakeasy: Speakeasy, sparql_endpoint: str):
        self.speakeasy = speakeasy
        self.sparql_endpoint = sparql_endpoint
        self.__knowledge_graph = KnowledgeGraph(sparql_endpoint)
        # self.llm_handler = LLMHandler()

        self.speakeasy.login()
        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)

        self.thinking_messages = [
            "I'm on it!",
            "Let me check that for you.",
            "Thinking...",
            "Searching for the best recommendations...",
            "Give me a moment to find something great for you.",
        ]

        self.generic_answers = [
            "Based on your input, you might enjoy these movies:",
            "Here are some movies I found for you:",
            "Based on your request, you should check out these recommendations:",
        ]

    def run(self):
        self.speakeasy.start_listening()

    def on_new_message(self, content: str, room: Chatroom):
        room.post_messages(random.choice(self.thinking_messages))

        message = Message(content, self.__knowledge_graph)
        e_start = time.time()
        entities_in_message = message.entities
        e_end = time.time()
        print(f"entities time: {e_end - e_start}")
        start = time.time()
        properties_in_message = message.properties
        end = time.time()
        print(f"time: {end-start}")
        print(entities_in_message, properties_in_message)
        recommendations = self.get_recommendations(
            entities=entities_in_message, properties=properties_in_message
        )

        if recommendations:
            recommendation_labels = [entity.label for entity in recommendations]

            initial_response = (
                f"{random.choice(self.generic_answers)}\n- "
                + "\n- ".join(recommendation_labels)
            )
            room.post_messages(initial_response)

            # prompt = (
            #     f"A user has requested movies with certain properties, and based on this, "
            #     f"I have recommended the following movies: {', '.join(recommendation_labels)}. "
            #     f"Please provide a brief and engaging explanation for why these are good recommendations. "
            #     f"You can highlight shared genres, directors, actors, or themes that match the user's request."
            # )

            # try:
            #     llm_response = self.llm_handler.prompt(prompt)
            #     room.post_messages(llm_response)
            # except Exception as e:
            #     room.post_messages(f"⚠️ Oops, something went wrong while generating the explanation: {e}")
        else:
            room.post_messages(
                "I couldn't find any recommendations based on your input. Please try with different movies or properties."
            )

    def get_recommendations(
        self,
        entities: list[Entity],
        properties: list[Property],
    ) -> list[Entity]:
        from_entities = []
        from_properties = []
        if entities:
            return Recommendations.from_entities(
                entities, knowledge_graph=self.__knowledge_graph
            )
        else:
            return Recommendations.from_properties(
                properties, knowledge_graph=self.__knowledge_graph
            )

        return set(from_entities + from_properties)
