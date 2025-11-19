from typing import TYPE_CHECKING, TypedDict, Union

from SPARQLWrapper import SPARQLWrapper

if TYPE_CHECKING:
    from core import Entity, Property, Relation


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

    @staticmethod
    def union_clauses(
        triplets: list[
            tuple[
                Union["Entity", None], Union["Relation", None], Union["Property", None]
            ]
        ],
        variable_names: list[str] = ["entity", "relation", "property"],
    ) -> str:
        union_clauses = []
        for e, r, p in triplets:
            if e is not None:
                e_clause = f"<{e.uri}>"
            else:
                e_clause = f"?{variable_names[0]}"
            if r is not None:
                r_clause = f"<{r.uri}>"
            else:
                r_clause = f"?{variable_names[1]}"
            if p is not None:
                if isinstance(p, str):
                    p_clause = f'"{p}"'
                else:
                    p_clause = f"<{p.uri}>"
            else:
                p_clause = f"?{variable_names[2]}"
            union_clauses.append(f"{e_clause} {r_clause} {p_clause} .")

        return " UNION ".join(f"{{{clause}}}" for clause in union_clauses)
