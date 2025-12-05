from collections import Counter
from random import choice

from rdflib import RDFS, URIRef

from core import Entity, KnowledgeGraph, Property, Relation
from utils import SPARQLQuery, get_common_values

from .Answer import Answer
from .Message import Message


class RecommendationAnswer(Answer):

    def __init__(
        self,
        message: Message,
        knowledge_graph: KnowledgeGraph,
        relevant_instance_of_entities: list[Entity] | None = None,
    ):
        super().__init__(message, knowledge_graph)
        if relevant_instance_of_entities is not None:
            self.__relevant_instance_of_entities = relevant_instance_of_entities
        else:
            self.__relevant_instance_of_entities = Entity.instance_of_movies(
                self._knowledge_graph
            )
        self.__recommendations = self.__get_recommendations()

    def __add__(self, other: "RecommendationAnswer") -> list[Entity]:
        combined = self.__recommendations + other.recommendations
        unique_recommendations = list(
            {entity.uri: entity for entity in combined}.values()
        )
        return unique_recommendations

    def __eq__(self, other: "RecommendationAnswer") -> bool:
        if not isinstance(other, RecommendationAnswer):
            return False
        return set(self.__recommendations) == set(other.recommendations)

    def __iter__(self):
        return iter(self.__recommendations)

    def __str__(self):
        return str(self.__recommendations)

    def __len__(self):
        return len(self.__recommendations)

    def answer(self) -> list[str]:
        return [e.label for e in self if e.label]

    def formatted_answer(self) -> str:
        answers = self.answer()
        if not answers:
            return "I couldn't find any recommendations based on your input."
        recommendation_answer_intros = [
            "Based on your input, you might enjoy these movies:",
            "Here are some movies I found for you:",
            "Based on your request, you should check out these recommendations:",
            "I've found the following movies that you might like:",
            "You might find these movies interesting:",
            "Here are some recommendations based on your input:",
        ]
        answer_intro = choice(recommendation_answer_intros)
        return f"{answer_intro}\n- " + "\n- ".join(answers)

    @property
    def recommendations(self) -> list[Entity]:
        return self.__recommendations

    def __get_recommendations(self) -> list[Entity]:
        entities_in_message = self._message.entities
        properties_in_message = self._message.properties
        if entities_in_message:
            return self.__based_on_entities(entities_in_message, self._knowledge_graph)
        if properties_in_message:
            return self.__based_on_properties(
                properties_in_message,
                self._knowledge_graph,
                self.__relevant_instance_of_entities,
            )
        return []

    @staticmethod
    def __based_on_entities(
        entities: list[Entity], knowledge_graph: KnowledgeGraph
    ) -> list[Entity]:
        all_relations = [
            relation for entity in entities for relation in entity.relations
        ]
        common_relations = get_common_values(
            all_relations, min_count=2 if len(entities) > 1 else 1
        )

        common_properties_per_relation = {}
        for relation, _ in common_relations:
            all_properties_for_relation = []
            for entity in entities:
                properties = entity.properties.get(relation)
                if properties:
                    all_properties_for_relation.extend(properties)

            if all_properties_for_relation:
                common_properties = get_common_values(all_properties_for_relation)
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

        input_entity_uris = {str(entity.uri) for entity in entities}
        sorted_recommendations = [
            movie
            for movie, _ in movie_counts.most_common(10)
            if str(movie.uri) not in input_entity_uris
        ]
        return sorted_recommendations

    @staticmethod
    def __based_on_properties(
        properties: list[Property],
        knowledge_graph: KnowledgeGraph,
        relevant_instance_of_entities: list[Entity] = [],
    ) -> list[Entity]:
        condition_triplets = [
            (None, Relation.instance_of(knowledge_graph), e)
            for e in relevant_instance_of_entities
        ]

        all_similar_entities = []
        for prop in properties:
            query = f"""
                SELECT ?uri ?label WHERE {{
                    ?uri <{RDFS.label}> ?label .
                    ?uri ?relation <{prop.uri}> .
                    {{ {SPARQLQuery.union_clauses(condition_triplets, ["uri"])} }}
                }}
            """
            query_result = knowledge_graph.query(query)
            all_similar_entities.extend(
                [
                    Entity(URIRef(uri["value"]), knowledge_graph, label["value"])
                    for uri, label in zip(
                        query_result["uri"],
                        query_result["label"],
                    )
                ]
            )

        entity_counts = Counter(all_similar_entities)
        sorted_recommendations = [entity for entity, _ in entity_counts.most_common(10)]
        return sorted_recommendations
