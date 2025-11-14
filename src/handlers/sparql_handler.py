import signal
from collections import Counter
from typing import Any, Optional

from SPARQLWrapper import SPARQLWrapper

SPARQL_PREFIXES = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <http://schema.org/>
"""


class TimeoutException(Exception):
    pass


class SparqlHandler:
    def __init__(self, graph: SPARQLWrapper, query_timeout_seconds: int):
        self.graph = graph
        self.query_timeout_seconds = query_timeout_seconds

    def count_common_properties_for_entities(
        self, entity_ids: list[str]
    ) -> dict[str, list[tuple[str, int]]]:
        if not entity_ids:
            return {}

        all_relations = []
        for entity_id in entity_ids:
            for relations in self._get_relations_of_entity(entity_id):
                all_relations.append(relations)

        if not all_relations:
            return {}

        common_relations = self._get_common_values(all_relations)

        relation_property_count = {}
        all_properties = []
        for relation_id, _ in common_relations:
            for entity_id in entity_ids:
                all_properties.extend(
                    self._get_property_of_entity(entity_id, relation_id)
                )

            if all_properties:
                common_properties = self._get_common_values(all_properties)
                if common_properties:
                    relation_property_count[relation_id] = common_properties

        return relation_property_count

    def get_entities_with_common_properties(
        self, common_properties_count: dict[str, list[tuple[str, int]]]
    ) -> dict[str, dict[str, list[str]]]:
        movies_by_property = {}

        for relation_id, properties in common_properties_count.items():
            movies_by_property[relation_id] = {}
            for property_id, _ in properties:
                entities_by_property = self._get_entities_by_property(
                    relation_id, property_id
                )
                if entities_by_property:
                    movies_by_property[relation_id][property_id] = entities_by_property

        return movies_by_property

    def get_subjects(self, entity_id: str, relation_id: str) -> list[str]:
        subject_query = f"""
            {SPARQL_PREFIXES}
            SELECT COALESCE(?subjLabel, STR(?subj)) AS ?subject) {{
                ?subj <{relation_id}> <{entity_id}> .
                OPTIONAL {{
                    ?subj rdfs:label ?subjLabel .
                }}
            }}
        """
        subject_results = self._execute_sparql_query(subject_query)
        return [res["subject"] for res in subject_results] if subject_results else None

    def get_objects(self, entity_id: str, relation_id: str) -> list[str]:
        object_query = f"""
            {SPARQL_PREFIXES}
            SELECT COALESCE(?objLabel, STR(?obj)) AS ?object) {{
                <{entity_id}> <{relation_id}> ?obj .
                OPTIONAL {{
                    ?obj rdfs:label ?objLabel .
                }}
            }}
        """
        object_results = self._execute_sparql_query(object_query)
        return [res["object"] for res in object_results] if object_results else None

    def get_instance_of(self, entity_id: str) -> list[str]:
        self._get_property_of_entity(
            entity_id, "http://www.wikidata.org/prop/direct/P31"
        )

    def _get_property_of_entity(self, entity_id: str, relation_id: str) -> list[str]:
        query = f"""
            {SPARQL_PREFIXES}
            SELECT ?property WHERE {{
                <{entity_id}> <{relation_id}> ?property .
            }}
        """
        results = self._execute_sparql_query(query)
        if results:
            return [res["property"] for res in results]
        else:
            return []

    def _get_relations_of_entity(self, entity_id: str) -> list[str]:
        query = f"""
            {SPARQL_PREFIXES}
            SELECT DISTINCT ?relation WHERE {{
              <{entity_id}> ?relation ?value .
            }}
        """
        results = self._execute_sparql_query(query)
        if results:
            return [res["relation"] for res in results]
        else:
            return []

    def _get_common_values(self, values: list[Any], min_count: int = 2) -> list[Any]:
        value_counts = Counter(values)
        return [
            (value, count)
            for value, count in value_counts.most_common()
            if count >= min_count
        ]

    def _get_entities_by_property(
        self, relation_id: str, property_id: str
    ) -> list[str]:
        query = f"""
            {SPARQL_PREFIXES}
            SELECT ?entity WHERE {{
                ?entity <{relation_id}> <{property_id}> .
            }}
        """
        results = self._execute_sparql_query(query)
        if results:
            return [res["entity"] for res in results]
        else:
            return []

    def _execute_sparql_query(self, query: str) -> Optional[list[dict[str, str]]]:
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.query_timeout_seconds)

        try:
            self.graph.setQuery(query)
            results = self.graph.queryAndConvert()

            if results["results"]["bindings"]:
                return [
                    {key: res[key]["value"] for key in res}
                    for res in results["results"]["bindings"]
                ]
            return None

        except TimeoutException as e:
            raise TimeoutException(f"Sorry, the query took too long to execute. {e}")
        except Exception as e:
            raise RuntimeError(f"Oops, I ran into an issue processing that query: {e}")
        finally:
            signal.alarm(0)

    def _timeout_handler(self, signum, frame):
        raise TimeoutException(
            f"Query execution timed out after {self.query_timeout_seconds} seconds."
        )
