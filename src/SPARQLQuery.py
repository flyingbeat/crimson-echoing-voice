from typing import TypedDict

from SPARQLWrapper import SPARQLWrapper

BindingDict = TypedDict("BindingDict", {"type": str, "value": str})
HeadDict = TypedDict("HeadDict", {"vars": list[str]})

SPARQLResults = TypedDict("SPARQLResults", {"bindings": list[dict[str, BindingDict]]})

SPARQLResponse = TypedDict(
    "SPARQLResponse",
    {
        "head": HeadDict,
        "results": SPARQLResults,
    },
)


class SPARQLQuery:
    def __init__(self, graph: SPARQLWrapper, query: str):
        self.graph = graph
        self.query = query

    def query_and_convert(self) -> dict[str, list[BindingDict]]:
        """
        Executes the SPARQL query and converts the result to a dictionary
        with the variable name as keys and lists of corresponding values.
        """
        self.graph.setQuery(self.query)
        response = SPARQLResponse(self.graph.query().convert())
        return {
            var: [binding[var] for binding in response["results"]["bindings"]]
            for var in response["head"]["vars"]
        }
