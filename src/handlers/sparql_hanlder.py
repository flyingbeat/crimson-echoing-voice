import signal
from typing import Optional
from collections import Counter

from SPARQLWrapper import SPARQLWrapper


class SparqlHandler:
    def __init__(self, graph: SPARQLWrapper, query_timeout_seconds: int):
        self.graph = graph
        self.query_timeout_seconds = query_timeout_seconds
        self.relation_whitelist = [
            "P31",  # instance of
            "P57",  # director
            "P162",  # producer
            "P272",  # production company
            "P58",  # screenwriter
            "P166",  # award received
            "P577",  # release date
            "P136",  # genre
        ]

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
            return results[0]
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

        return (
            self._execute_sparql_query(subject_query),
            self._execute_sparql_query(object_query),
        )

    def _execute_sparql_query(self, query: str) -> Optional[list[str]]:
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.query_timeout_seconds)

        try:
            self.graph.setQuery(query)
            results = self.graph.queryAndConvert()

            if results["results"]["bindings"]:
                return [
                    str(res["result"]["value"])
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

    def get_properties_for_entities(self, entity_ids: list[str], relation_ids: list[str]) -> dict[str, dict[str, int]]:
        relation_property_count = {}
        if not entity_ids:
            return []

        for relation_id in relation_ids:
            relation_properties = []
            for entity_id in entity_ids:
                object_query = f"""
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    PREFIX schema: <http://schema.org/>

                    SELECT (COALESCE(?objLabel, STR(?obj)) AS ?result) (COALESCE(?objDesc, "") AS ?description) {{
                        <{entity_id}> <http://www.wikidata.org/prop/direct/{relation_id}> ?obj .
                        OPTIONAL {{
                            ?obj rdfs:label ?objLabel .
                        }}
                        OPTIONAL {{
                            ?obj schema:description ?objDesc .
                        }}
                    }}
                """
                entity_properties = self._execute_sparql_query(object_query)
                if entity_properties:
                    relation_properties.extend(entity_properties)
            if relation_properties:
                relation_property_count[relation_id] = Counter(relation_properties)

        print(relation_property_count)
        return relation_property_count


class TimeoutException(Exception):
    pass
