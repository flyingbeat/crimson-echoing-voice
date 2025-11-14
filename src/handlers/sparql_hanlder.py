import signal
from collections import Counter
from typing import Optional

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

    def get_instance_of(self, entity_id: str) -> str:
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>

            SELECT (STR(?obj) AS ?result) WHERE {{
                <{entity_id}> <http://www.wikidata.org/prop/direct/P31> ?obj .
            }}
        """
        results = self._execute_sparql_query(query)
        if results:
            return [res['result'] for res in results]
        else:
            return ""

    def run_sparql_for_prompt(
            self, entity_id: str, relation_id: str
    ) -> tuple[Optional[list[str]], Optional[list[str]]]:
        object_query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>


            SELECT (COALESCE(?objLabel, STR(?obj)) AS ?result) (COALESCE(?objDesc, "") AS ?description) {{
                <{entity_id}> <{relation_id}> ?obj .
                OPTIONAL {{
                    ?obj rdfs:label ?objLabel .
                }}
                OPTIONAL {{
                    ?obj schema:description ?objDesc .
                }}
            }}
        """
        subject_query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>

            SELECT (COALESCE(?subjLabel, STR(?subj)) AS ?result) (COALESCE(?subjDesc, "") AS ?description) WHERE {{
                ?subj <{relation_id}> <{entity_id}> .
                OPTIONAL {{
                    ?subj rdfs:label ?subjLabel .
                }}
                OPTIONAL {{
                    ?subj schema:description ?subjDesc .
                }}
            }}
        """

        subject_results = self._execute_sparql_query(subject_query)
        object_results = self._execute_sparql_query(object_query)

        return (
            [res['result'] for res in subject_results] if subject_results else None,
            [res['result'] for res in object_results] if object_results else None,
        )

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

    def get_properties_for_entities(
            self, entity_ids: list[str]
    ) -> dict[str, list[tuple[str, int]]]:
        if not entity_ids:
            return {}

        # First, get all unique relations for the given entities
        all_relations = []
        for entity_id in entity_ids:
            query = f"""
                {SPARQL_PREFIXES}
                SELECT DISTINCT ?relation WHERE {{
                  <{entity_id}> ?relation ?value .
                }}
            """
            relations = self._execute_sparql_query(query)
            if relations:
                all_relations.extend([res["relation"] for res in relations])

        if not all_relations:
            return {}

        relation_counts = Counter(all_relations)

        # Filter for relations that are common to more than one of the input movies
        common_relations = [
            relation for relation, count in relation_counts.items() if count > 1
        ]

        # Now, for each common relation, get all the property values
        relation_property_count = {}
        for relation in common_relations:
            all_properties = []
            for entity_id in entity_ids:
                query = f"""
                    {SPARQL_PREFIXES}
                    SELECT DISTINCT (STR(?value) as ?prop) WHERE {{
                      <{entity_id}> <{relation}> ?value .
                    }}
                """
                properties = self._execute_sparql_query(query)
                if properties:
                    all_properties.extend([res["prop"] for res in properties])

            if all_properties:
                # Count the occurrences of each property for this relation
                property_counts = Counter(all_properties)
                # We are interested in properties that are shared among the input entities
                shared_properties = [
                    (prop, count)
                    for prop, count in property_counts.items()
                    if count > 1
                ]
                if shared_properties:
                    relation_property_count[relation] = shared_properties

        return relation_property_count

    def get_movies_with_properties(
            self, properties_by_relation: dict[str, list[tuple[str, int]]]
    ) -> dict[str, dict[str, list[str]]]:
        movies_by_property = {}

        for relation_id, properties in properties_by_relation.items():
            movies_by_property[relation_id] = {}
            for prop, count in properties:
                query = f"""
                    {SPARQL_PREFIXES}
                    SELECT (STR(?movie) AS ?result) WHERE {{
                        ?movie <{relation_id}> <{prop}> .
                    }}
                """

                results = self._execute_sparql_query(query)
                if results:
                    movies_by_property[relation_id][prop] = [res['result'] for res in results]

        return movies_by_property