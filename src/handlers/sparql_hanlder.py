import signal
from typing import Optional

class SparqlHandler:
    def __init__(self, graph, query_timeout_seconds):
        self.graph = graph
        self.query_timeout_seconds = query_timeout_seconds

    def run_sparql_for_prompt(
        self, entity_id: str, relation_id: str
    ) -> tuple[Optional[str], Optional[str]]:
        object_query = f"""
            SELECT (COALESCE(?objLabel, STR(?obj)) AS ?result) WHERE {{
                <{entity_id}> <{relation_id}> ?obj .
                OPTIONAL {{
                    ?obj rdfs:label ?objLabel .
                }}
            }}
        """
        subject_query = f"""
            SELECT (COALESCE(?subjLabel, STR(?subj)) AS ?result) WHERE {{
                ?subj <{relation_id}> <{entity_id}> .
                OPTIONAL {{
                    ?subj rdfs:label ?subjLabel .
                }}
            }}
        """

        return (
            self._execute_sparql_query(subject_query),
            self._execute_sparql_query(object_query)
        )

    def _execute_sparql_query(self, query: str) -> Optional[str]:
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.query_timeout_seconds)

        try:
            results = self.graph.query(query)
            for row in results:
                return str(row[0])
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
