from collections import defaultdict
from typing import TYPE_CHECKING

from rdflib import URIRef

from SPARQLQuery import BindingDict

if TYPE_CHECKING:
    from KnowledgeGraph import KnowledgeGraph
    from Property import Property
    from Relation import Relation


class Entity:
    def __init__(
        self, uri: URIRef, label: str | None, knowledge_graph: "KnowledgeGraph"
    ):
        self.__uri = uri
        self.__label: str | None = label
        self.__knowledge_graph = knowledge_graph
        self.__properties: dict["Relation", list["Property"]] | None = None

    def __repr__(self):
        return str(self.uri)

    def __hash__(self):
        return hash(self.__uri)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.__uri == other.__uri
        return False

    @property
    def uri(self) -> URIRef:
        return self.__uri

    @property
    def properties(self) -> dict["Relation", list["Property"]]:
        if self.__properties is None:
            self.__properties = self.__get_properties()
        return self.__properties

    def __get_properties(self) -> dict["Relation", list["Property"]]:
        properties = self.__knowledge_graph.get_properties(self)
        if properties:
            property_dict = defaultdict(list)
            for _, r, p in properties:
                property_dict[r].append(p)
            return property_dict
        return {}

    @property
    def relations(self) -> list["Relation"]:
        return list(self.properties.keys())

    @property
    def label(self) -> str:
        if self.__label:
            return self.__label
        return self.__get_label(self.__uri)

    def __get_label(self, uri: URIRef) -> str:
        return self.__knowledge_graph.get_label(uri)

    @classmethod
    def from_binding(
        cls, binding: BindingDict, knowledge_graph: "KnowledgeGraph"
    ) -> "Entity":
        if binding["type"] == "uri":
            uri = URIRef(binding.get("value"))
            return cls(uri=uri, label=None, knowledge_graph=knowledge_graph)
        else:
            raise ValueError(
                f"Cannot create Entity from binding type: {binding['type']}"
            )
