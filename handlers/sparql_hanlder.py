import signal
from speakeasypy import Chatroom


class SparqlHandler:
    def __init__(self, graph, query_timeout_seconds):
        self.graph = graph
        self.query_timeout_seconds = query_timeout_seconds

    def run_sparql_for_prompt(self, head_ent, pred_ent, room: Chatroom):
        query = f"""
            SELECT (COALESCE(?objLabel, STR(?obj)) AS ?result) WHERE {{
                <{head_ent}> <{pred_ent}> ?obj .
                OPTIONAL {{
                    ?obj rdfs:label ?objLabel .
                }}
            }}
        """
        room.post_messages(
            f"🔎 Searching the knowledge graph factually...")
        self._execute_sparql_query(query, room)

    def _execute_sparql_query(self, query: str, room: Chatroom):
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(self.query_timeout_seconds)

        try:
            results = self.graph.query(query)
            result_list = [", ".join(str(item) for item in row) for row in results]

            if not result_list:
                room.post_messages("No direct matches found in the knowledge graph.")
                return

            response_text = self._format_results(result_list)
            room.post_messages(response_text)

        except TimeoutException as e:
            room.post_messages(f"Sorry, the query took too long to execute. {e}")
        except Exception as e:
            room.post_messages(f"Oops, I ran into an issue processing that query: {e}")
        finally:
            signal.alarm(0)

    @staticmethod
    def _format_results(results: list[str]) -> str:
        if len(results) == 1:
            return f"Found it! {results[0]}"
        formatted = "\n  • ".join(results)
        return f"Found {len(results)} results:\n  • {formatted}"

    def _timeout_handler(self, signum, frame):
        raise TimeoutException(f"Query execution timed out after {self.query_timeout_seconds} seconds.")


class TimeoutException(Exception):
    pass