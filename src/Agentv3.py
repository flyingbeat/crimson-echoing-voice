from collections import Counter, defaultdict
import random

from speakeasypy import Chatroom, EventType, Speakeasy

from Entity import Entity
from KnowledgeGraph import KnowledgeGraph
from Message import Message
from Property import Property
from Relation import Relation
from Util import Util
from handlers.llm_handler import LLMHandler


class Agent:

    def __init__(self, speakeasy: Speakeasy, sparql_endpoint: str):
        self.speakeasy = speakeasy
        self.sparql_endpoint = sparql_endpoint
        self.__knowledge_graph = KnowledgeGraph(sparql_endpoint)
        self.llm_handler = LLMHandler()

        self.speakeasy.login()
        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)

        self.thinking_messages = [
            "I'm on it!",
            "Let me check that for you.",
            "Thinking...",
            "Searching for the best recommendations...",
            "Give me a moment to find something great for you."
        ]

    def run(self):
        self.speakeasy.start_listening()

    def on_new_message(self, content: str, room: Chatroom):
        room.post_messages(random.choice(self.thinking_messages))

        message = Message(content)
        entities_in_message = message.entities

        if len(entities_in_message) <= 1:
            room.post_messages("Please provide me with a few more movies so I can give you a good recommendation.")
            return

        recommendations = self.get_recommendations(entities_in_message)

        if recommendations:
            recommendation_labels = [entity.label for entity in recommendations]

            context = f"Given the inputted movies, these are the most similar movies: {', '.join(recommendation_labels)}"

            try:
                llm_response = self.llm_handler.prompt(content, context=context)
                room.post_messages(llm_response)
            except Exception as e:
                room.post_messages(f"⚠️ Oops, something went wrong during the LLM generation: {e}")
        else:
            room.post_messages(
                "I couldn't find any recommendations based on your input. Please try with different movies.")

    def get_recommendations(self, entities: list[Entity]) -> list[Entity]:
        all_relations = [
            relation for entity in entities for relation in entity.relations
        ]
        common_relations = Util.get_common_values(all_relations)

        common_properties_per_relation = {}
        for relation, _ in common_relations:
            all_properties_for_relation = []
            for entity in entities:
                properties = entity.properties.get(relation)
                if properties:
                    all_properties_for_relation.extend(properties)

            if all_properties_for_relation:
                common_properties = Util.get_common_values(
                    all_properties_for_relation
                )
                if common_properties:
                    common_properties_per_relation[relation] = common_properties

        all_similar_entities = []
        for (
            common_relation,
            common_properties,
        ) in common_properties_per_relation.items():
            for common_property, _ in common_properties:
                entities_with_property = self.__knowledge_graph.get_triplets(
                    None, common_relation, common_property
                )

                if entities_with_property:
                    all_similar_entities.extend([e for e, _, _ in entities_with_property])

        movie_counts = Counter(all_similar_entities)

        input_entity_uris = {entity.uri for entity in entities}
        sorted_recommendations = [
            movie
            for movie, _ in movie_counts.most_common(10)
            if str(movie.uri) not in input_entity_uris
        ]
        return sorted_recommendations
