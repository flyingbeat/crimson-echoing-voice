import time
from random import choice

from speakeasypy import Chatroom, EventType, Speakeasy

from core import Entity, KnowledgeGraph, Property
from llm import LargeLanguageModel

from .Message import Message
from .Recommendations import Recommendations


class Agentv3:

    def __init__(self, speakeasy: Speakeasy, sparql_endpoint: str):
        self.speakeasy = speakeasy
        self.sparql_endpoint = sparql_endpoint
        self.__knowledge_graph = KnowledgeGraph(sparql_endpoint)
        print("Loading entities...")
        self.__knowledge_graph.entities  # Preload entities
        print("Entities loaded.")
        self.__llm = LargeLanguageModel()

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
        room.post_messages(choice(self.thinking_messages))

        message = Message(content, self.__knowledge_graph)

        e_start = time.time()
        entities_in_message = message.entities
        e_end = time.time()
        print(f"entities time: {e_end - e_start}")

        p_start = time.time()
        properties_in_message = message.properties
        p_end = time.time()
        print(f"properties time: {p_end - p_start}")

        print(entities_in_message, properties_in_message)

        recommendations = self.get_recommendations(
            entities=entities_in_message, properties=properties_in_message
        )

        if recommendations:
            recommendation_labels = [entity.label for entity in recommendations]

            prompt = (
                "A user has requested movies with certain properties, and based on this, "
                "Please provide a very short and engaging explanation for why these are good recommendations. "
                "Filter out any movies you think are not relevant only include relevant answers"
            )
            context = (
                f"The user requested movies related to: {', '.join([entity.label for entity in entities_in_message]) or ', '.join([p.label for p in properties_in_message])}. "
                f"The recommended movies are: {', '.join(recommendation_labels)}."
            )

            try:
                print(context)
                llm_response = self.__llm.prompt(
                    prompt, context=context, max_tokens=200
                )
                print(llm_response)
                room.post_messages(llm_response)
            except Exception as e:
                print(e)
                room.post_messages(
                    f"⚠️ Oops, something went wrong while generating the explanation"
                )
                initial_response = f"{choice(self.generic_answers)}\n- " + "\n- ".join(
                    recommendation_labels
                )
                room.post_messages(initial_response)
        else:
            room.post_messages(
                "I couldn't find any recommendations based on your input. Please try with different movies or properties."
            )

    def get_recommendations(
        self,
        entities: list[Entity],
        properties: list[Property],
    ) -> list[Entity]:
        if entities:
            return Recommendations.from_entities(
                entities, knowledge_graph=self.__knowledge_graph
            )
        else:
            return Recommendations.from_properties(
                properties,
                knowledge_graph=self.__knowledge_graph,
                relevant_instance_of_entities=Entity.instance_of_movies(
                    self.__knowledge_graph
                ),
            )
