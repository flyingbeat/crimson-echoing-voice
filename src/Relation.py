from typing import TYPE_CHECKING

from rdflib import RDFS, Namespace, URIRef

from SPARQLQuery import BindingDict

if TYPE_CHECKING:
    from Entity import Entity
    from KnowledgeGraph import KnowledgeGraph

SCHEMA = Namespace("http://schema.org/")


class Relation:
    def __init__(self, uri: URIRef, knowledge_graph: "KnowledgeGraph"):
        self.__uri = uri
        self.__label: str | None = None
        self.__knowledge_graph = knowledge_graph

    def __repr__(self):
        return str(self.uri)

    def __hash__(self):
        return hash(self.__uri)

    def __eq__(self, other):
        if isinstance(other, Relation):
            return self.__uri == other.__uri
        return False

    @property
    def uri(self) -> URIRef:
        return self.__uri

    @property
    def label(self) -> str:
        if (
            self.__label
            or self.__uri.startswith(RDFS.label)
            or self.__uri.startswith(SCHEMA.description)
        ):
            return self.__label
        return self.__get_label(self.__uri)

    def __get_label(self, uri: URIRef) -> str:
        return self.__knowledge_graph.get_label(uri)

    @classmethod
    def from_binding(
        cls, binding: BindingDict, knowledge_graph: "KnowledgeGraph"
    ) -> "Relation":
        if binding["type"] == "uri":
            uri = URIRef(binding.get("value"))
            return cls(uri=uri, knowledge_graph=knowledge_graph)
        else:
            raise ValueError(
                f"Cannot create Relation from binding type: {binding['type']}"
            )
