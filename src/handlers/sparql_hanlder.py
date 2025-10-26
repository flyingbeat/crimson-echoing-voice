import signal
from typing import Optional

from speakeasypy import Chatroom


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

        return self._execute_sparql_query(subject_query), self._execute_sparql_query(
            object_query
        )

    def _execute_sparql_query(self, query: str) -> Optional[str]:
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.query_timeout_seconds)

        try:
            results = self.graph.query(query)
            result_list = [", ".join(str(item) for item in row) for row in results]

            if not result_list:
                return None

            return self._format_results(result_list)

        except TimeoutException as e:
            raise TimeoutException(f"Sorry, the query took too long to execute. {e}")
        except Exception as e:
            raise RuntimeError(f"Oops, I ran into an issue processing that query: {e}")
        finally:
            signal.alarm(0)

    @staticmethod
    def _format_results(results: list[str]) -> str:
        if len(results) == 1:
            return f"Found it! {results[0]}"
        formatted = "\n  • ".join(results)
        return f"Found {len(results)} results:\n  • {formatted}"

    def _timeout_handler(self, signum, frame):
        raise TimeoutException(
            f"Query execution timed out after {self.query_timeout_seconds} seconds."
        )


class TimeoutException(Exception):
    pass
