import signal
from typing import Optional

from SPARQLWrapper import SPARQLWrapper


class SparqlHandler:
    def __init__(self, graph: SPARQLWrapper, query_timeout_seconds: int):
        self.graph = graph
        self.query_timeout_seconds = query_timeout_seconds

    def run_sparql_for_prompt(
        self, entity_id: str, relation_id: str
    ) -> tuple[Optional[list[str]], Optional[list[str]]]:
        object_query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT (COALESCE(?objLabel, STR(?obj)) AS ?result) WHERE {{
                <{entity_id}> <{relation_id}> ?obj .
                OPTIONAL {{
                    ?obj rdfs:label ?objLabel .
                }}
            }}
        """
        subject_query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT (COALESCE(?subjLabel, STR(?subj)) AS ?result) WHERE {{
                ?subj <{relation_id}> <{entity_id}> .
                OPTIONAL {{
                    ?subj rdfs:label ?subjLabel .
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


class TimeoutException(Exception):
    pass
