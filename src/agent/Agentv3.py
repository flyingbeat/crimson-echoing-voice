import time
from random import choice

from speakeasypy import Chatroom, EventType, Speakeasy

from core import Entity, KnowledgeGraph, Property, Relation
from llm import LargeLanguageModel

from .FactualAnswers import FactualAnswers
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
        print("Loading relations...")
        self.__knowledge_graph.relations  # Preload relations
        print("Relations loaded.")

        self.speakeasy.login()
        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)

        self.thinking_messages = [
            "I'm on it!",
            "Let me check that for you.",
            "Thinking...",
            "Searching for the best recommendations...",
            "Give me a moment to find something great for you.",
            "Let me see what I can find.",
            "I'm looking into it now.",
            "Just a second, I'm gathering some recommendations.",
            "Hold on, I'm fetching some options for you.",
            "Let me think about that for a moment.",
        ]

        self.generic_answers = [
            "Based on your input, you might enjoy these movies:",
            "Here are some movies I found for you:",
            "Based on your request, you should check out these recommendations:",
            "I've found the following movies that you might like:",
            "You might find these movies interesting:",
            "Here are some recommendations based on your input:",
        ]
        self.answers_cache = {}

    def run(self):
        self.speakeasy.start_listening()

    def on_new_message(self, content: str, room: Chatroom):
        if content in self.answers_cache:
            room.post_messages(self.answers_cache[content])
            return
        room.post_messages(choice(self.thinking_messages))

        message = Message(content, self.__knowledge_graph)

        entities_in_message = message.entities
        properties_in_message = message.properties
        relations_in_message = message.relations
        print(entities_in_message, properties_in_message, relations_in_message)

        multimedia_answers = self.get_multimedia_answers(
            entities=entities_in_message, properties=properties_in_message
        )
        uri = str(multimedia_answers.uri)

        formatted = "image:" + "/".join(
            uri.rstrip("/").split("/")[-2:]
        ).rsplit(".", 1)[0]

        room.post_messages(formatted)
        return

        factual_answers = self.get_factual_answers(
            entities=entities_in_message, relations=relations_in_message
        )

        recommendations = self.get_recommendations(
            entities=entities_in_message, properties=properties_in_message
        )

        if factual_answers:
            room.post_messages("and ".join(factual_answers.answers))
        elif recommendations:
            recommendation_labels = [
                entity.label for entity in recommendations if entity.label
            ]
            print(f"Recommendations: {recommendation_labels}")
            response = f"{choice(self.generic_answers)}\n- " + "\n- ".join(
                recommendation_labels
            )
            room.post_messages(response)
            self.answers_cache[content] = response
        else:
            room.post_messages(
                "I couldn't find any recommendations based on your input. Please try with different movies or properties."
            )

    def get_recommendations(
        self,
        entities: list[Entity],
        properties: list[Property],
    ) -> Recommendations | None:
        if entities:
            return Recommendations.from_entities(
                entities, knowledge_graph=self.__knowledge_graph
            )
        elif properties:
            return Recommendations.from_properties(
                properties,
                knowledge_graph=self.__knowledge_graph,
                relevant_instance_of_entities=Entity.instance_of_movies(
                    self.__knowledge_graph
                ),
            )
        else:
            return None

    def get_factual_answers(
        self,
        entities: list[Entity],
        relations: list[Relation],
    ) -> FactualAnswers | None:
        if not entities or not relations:
            return None
        return FactualAnswers(
            entity=entities[0],
            relation=relations[0],
            knowledge_graph=self.__knowledge_graph
        )

    def get_multimedia_answers(
            self,
            entities: list[Entity],
            properties: list[Property],
    ) -> None:
        if properties:
            for key, image_list in properties[0].images.items():
                if image_list:
                    return image_list[0]
        if entities:
            for key, image_list in entities[0].images.items():
                if str(key) == "http://schema.org/Backdrop" and image_list:
                    return image_list[0]
        return None