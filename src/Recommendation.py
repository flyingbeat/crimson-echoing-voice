from collections import Counter

from rdflib import RDFS

from Entity import Entity
from KnowledgeGraph import KnowledgeGraph
from Property import Property
from SPARQLQuery import SPARQLQuery
from Util import Util


class Recommendations:

    def __init__(
        self, recommendations: list[Entity], knowledge_graph: "KnowledgeGraph"
    ):
        self.__recommendations = recommendations
        self.__knowledge_graph = knowledge_graph
        self.__relevant_instance_of_entities = [Entity.film(self.__knowledge_graph)]

    def __add__(self, other: "Recommendations") -> list[Entity]:
        combined = self.__recommendations + other.recommendations
        unique_recommendations = list(
            {entity.uri: entity for entity in combined}.values()
        )
        return unique_recommendations

    def __eq__(self, other: "Recommendations") -> bool:
        if not isinstance(other, Recommendations):
            return False
        return set(self.__recommendations) == set(other.recommendations)

    def __iter__(self):
        return iter(self.__recommendations)

    def __str__(self):
        return f"Recommendations({', '.join([str(entity) for entity in self.__recommendations])})"

    def __len__(self):
        return len(self.__recommendations)

    @property
    def recommendations(self) -> list[Entity]:
        return self.__recommendations

    @property
    def relevant_instance_of_entities(self) -> list[Entity]:
        return self.__relevant_instance_of_entities

    @classmethod
    def from_entities(
        cls, entities: list[Entity], knowledge_graph: "KnowledgeGraph"
    ) -> "Recommendations":
        similar = cls.__based_on_entities(entities, knowledge_graph)
        print(similar)
        return Recommendations(
            similar,
            knowledge_graph=knowledge_graph,
        )

    @classmethod
    def from_properties(
        cls, properties: list[str], knowledge_graph: "KnowledgeGraph"
    ) -> "Recommendations":
        recommendations = Recommendations([], knowledge_graph=knowledge_graph)
        recommendations.__recommendations = cls.__based_on_properties(
            properties, knowledge_graph, recommendations.relevant_instance_of_entities
        )
        return recommendations

    @staticmethod
    def __based_on_entities(
        entities: list[Entity], knowledge_graph: "KnowledgeGraph"
    ) -> list[Entity]:
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
                common_properties = Util.get_common_values(all_properties_for_relation)
                if common_properties:
                    common_properties_per_relation[relation] = common_properties

        all_similar_entities = []
        for (
            common_relation,
            common_properties,
        ) in common_properties_per_relation.items():
            for common_property, _ in common_properties:
                entities_with_property = knowledge_graph.get_triplets(
                    None, common_relation, common_property
                )

                if entities_with_property:
                    all_similar_entities.extend(
                        [e for e, _, _ in entities_with_property]
                    )

        movie_counts = Counter(all_similar_entities)

        input_entity_uris = {entity.uri for entity in entities}
        sorted_recommendations = [
            movie
            for movie, _ in movie_counts.most_common(10)
            if str(movie.uri) not in input_entity_uris
        ]
        return sorted_recommendations

    @staticmethod
    def __based_on_properties(
        properties: list[Property],
        knowledge_graph: "KnowledgeGraph",
        relevant_instance_of_entities: list[Entity] = [],
    ) -> list[Entity]:
        all_similar_entities = []
        for prop in properties:
            query = f"""
                SELECT ?uri ?label WHERE {{
                    ?uri <{RDFS.label}> ?label .
                    ?uri ?relation <{prop.uri}> .
                    ?uri <http://www.wikidata.org/prop/direct/P31> <http://www.wikidata.org/entity/Q11424> .
                }}
            """
            query_result = SPARQLQuery(
                knowledge_graph._KnowledgeGraph__graph, query
            ).query_and_convert()
            all_similar_entities.extend(
                [
                    Entity(
                        uri["value"],
                        label["value"],
                        None,
                        knowledge_graph,
                    )
                    for uri, label in zip(
                        query_result["uri"],
                        query_result["label"],
                    )
                ]
            )
            # entities_with_property = knowledge_graph.get_triplets(None, None, prop)
            # if entities_with_property:
            #     all_similar_entities.extend(
            #         [
            #             e
            #             for e, _, _ in entities_with_property
            #             if any(
            #                 instance_of in relevant_instance_of_entities
            #                 for instance_of in e.instance_of
            #             )
            #             or not relevant_instance_of_entities
            #         ]
            #     )

        entity_counts = Counter(all_similar_entities)
        # print(entity_counts)
        sorted_recommendations = [entity for entity, _ in entity_counts.most_common(10)]
        return sorted_recommendations
