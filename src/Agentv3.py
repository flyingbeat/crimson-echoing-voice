from collections import Counter, defaultdict

from speakeasypy import Chatroom, EventType, Speakeasy

from Entity import Entity
from KnowledgeGraph import KnowledgeGraph
from Message import Message
from Property import Property
from Relation import Relation
from Util import Util


class Agent:

    def __init__(self, speakeasy: Speakeasy, sparql_endpoint: str):
        self.speakeasy = speakeasy
        self.sparql_endpoint = sparql_endpoint
        self.__knowledge_graph = KnowledgeGraph(sparql_endpoint)

        self.speakeasy.login()
        self.speakeasy.register_callback(self.on_new_message, EventType.MESSAGE)

    def run(self):
        self.speakeasy.start_listening()

    def on_new_message(self, content: str, room: Chatroom):
        message = Message(content)
        entities_in_message = message.entities
        recommendations = self.get_recommendations(entities_in_message)
        answer = ", ".join(entity.label for entity in recommendations)
        print(answer)
        if recommendations:
            room.post_messages(answer)

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
