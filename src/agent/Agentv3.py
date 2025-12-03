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
            "Consulting the knowledge base...",
            "Let me see what I can find.",
            "I'm looking into it now.",
            "Just a second, processing your request.",
            "Let me think about that for a moment.",
            "Searching for the answer...",
        ]

        self.recommendation_answer_intros = [
            "Based on your input, you might enjoy these movies:",
            "Here are some movies I found for you:",
            "Based on your request, you should check out these recommendations:",
            "I've found the following movies that you might like:",
            "You might find these movies interesting:",
            "Here are some recommendations based on your input:",
        ]

        self.factual_answer_intros = [
            "The answer to your question is:",
            "According to my data:",
            "Here is the information you asked for:",
            "I found this information:",
            "The answer is:",
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

        question_type = message.question_type

        entities_in_message = message.entities
        properties_in_message = message.properties
        relations_in_message = message.relations

        print(f"Type: {question_type}")
        print(f"Entities: {entities_in_message}")
        print(f"Relations: {relations_in_message}")
        print(f"Properties: {properties_in_message}")

        response = None

        if question_type == "multimedia":
            image_uri = self.get_multimedia_answers(
                entities=entities_in_message,
                properties=properties_in_message
            ).uri

            if image_uri:
                uri = str(image_uri)
                formatted = "image:" + "/".join(
                    uri.rstrip("/").split("/")[-2:]
                ).rsplit(".", 1)[0]
                response = formatted
            else:
                response = "Sorry, I couldn't find an image for that."

        elif question_type == "recommendation":
            recommendations = self.get_recommendations(
                entities=entities_in_message,
                properties=properties_in_message
            )

            if recommendations:
                recommendation_labels = [
                    entity.label for entity in recommendations if entity.label
                ]
                response = f"{choice(self.recommendation_answer_intros)}\n- " + "\n- ".join(
                    recommendation_labels
                )
            else:
                response = "I couldn't find any recommendations based on your input."

        elif question_type == "one_hop":
            factual_answers = self.get_factual_answers(
                entities=entities_in_message,
                relations=relations_in_message
            )

            if factual_answers and factual_answers.answers:
                intro = choice(self.factual_answer_intros)
                answer_text = "and ".join(factual_answers.answers)
                response = f"{intro} {answer_text}"
            else:
                response = "I'm not sure about the answer to that specific question."

        if response:
            room.post_messages(response)
            self.answers_cache[content] = response

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
        # TODO: Reintroduce LLM?
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
            # TODO: Decide between backdrop and poster
            for key, image_list in entities[0].images.items():
                if str(key) == "http://schema.org/Backdrop" and image_list:
                    return image_list[0]
        return None