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
        for relation in common_relations:
            common_properties_per_relation[relation] = Util.get_common_values(
                [entity.properties.get(relation) for entity in entities]
            )

        for (
            common_relation,
            common_properties,
        ) in common_properties_per_relation.items():
            entities_with_properties: dict[str, dict[str, list[Entity]]] = defaultdict(
                lambda: defaultdict(list)
            )
            for common_property, _ in common_properties:
                entities_with_property = self.__knowledge_graph.get_triplets(
                    None, common_relation[0], common_property
                )
                if entities_with_property:
                    entities_with_properties[common_relation][common_property].extend(
                        [e for e, _, _ in entities_with_property]
                    )

        all_similar_entities = []
        for relation in entities_with_properties.values():
            for entity_list in relation.values():
                all_similar_entities.extend(entity_list)

        # Count how many times each movie was recommended
        movie_counts = Counter(all_similar_entities)

        # Remove the movies that were originally given as input
        for entity in entities:
            if entity in movie_counts:
                del movie_counts[entity]

        # Sort the movies by the frequency of recommendation
        sorted_recommendations = [movie for movie, _ in movie_counts.most_common(5)]

        return sorted_recommendations
