from collections import Counter, defaultdict

from speakeasypy import Chatroom, EventType, Speakeasy

from Entity import Entity
from KnowledgeGraph import KnowledgeGraph
from Message import Message
from Property import Property
from Relation import Relation


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
        answer = " ".join(entity.label for entity in recommendations)
        print(answer)
        if recommendations:
            room.post_messages(answer)

    def get_recommendations(self, entities: list[Entity]) -> list[Entity]:
        properties_per_entity = [entity.properties for entity in entities]
        entity_relations = [
            list(properties.keys()) for properties in properties_per_entity
        ]
        common_relations = {
            relation
            for relation, count in Counter(sum(entity_relations, [])).most_common()
            if count > 1
        }

        common_properties_per_relation: dict[Relation, list[Property]] = {}
        properties_of_common_relations: list[Property] = []
        for relation in common_relations:
            for entity_properties in properties_per_entity:
                if relation in entity_properties:
                    properties_of_common_relations.extend(entity_properties[relation])
            if properties_of_common_relations:
                common_properties = [
                    common_property
                    for common_property, count in Counter(
                        properties_of_common_relations
                    ).most_common()
                    if count > 1
                ]
                if common_properties:
                    common_properties_per_relation[relation] = common_properties

        entities_with_common_property_by_relation: dict[
            Relation, dict[Property, list[Entity]]
        ] = defaultdict(dict)

        for relation, common_properties in common_properties_per_relation.items():
            for common_property in common_properties:
                entities_with_common_property = self.__knowledge_graph.get_triplets(
                    None, relation, common_property
                )
                if entities_with_common_property:
                    entities_with_common_property_by_relation[relation][
                        common_property
                    ] = entities_with_common_property[0]

        all_recommended_entities = []
        for relation in entities_with_common_property_by_relation.values():
            for entity_list in relation.values():
                all_recommended_entities.extend(entity_list)

        entity_counts = Counter(all_recommended_entities)

        for entitiy in entities:
            if entitiy in entity_counts:
                del entity_counts[entitiy]

        sorted_recommendations = [entity for entity, _ in entity_counts.most_common()]
        return sorted_recommendations
