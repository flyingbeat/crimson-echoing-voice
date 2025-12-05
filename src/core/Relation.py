from typing import TYPE_CHECKING

from rdflib import RDFS, URIRef

from utils import BindingDict

from .Namespaces import SCHEMA, WDT

if TYPE_CHECKING:
    from .KnowledgeGraph import KnowledgeGraph


class Relation:
    def __init__(
        self,
        uri: URIRef,
        knowledge_graph: "KnowledgeGraph",
        label: str | None = None,
        alt_labels: list[str] = [],
    ):
        self.__uri = uri
        self.__label = label
        self.__knowledge_graph = knowledge_graph
        self.__alt_labels = alt_labels

    def __repr__(self):
        return f"Relation(uri={self.uri}, label={self.label})"

    def __hash__(self):
        return hash(self.__uri)

    def __eq__(self, other):
        if isinstance(other, Relation):
            return self.__uri == other.__uri
        return False

    @classmethod
    def instance_of(cls, knowledge_graph: "KnowledgeGraph") -> "Relation":
        return cls(
            uri=WDT.P31,
            knowledge_graph=knowledge_graph,
        )

    @classmethod
    def imdb_id(cls, knowledge_graph: "KnowledgeGraph") -> "Relation":
        return cls(
            uri=WDT.P345,
            knowledge_graph=knowledge_graph,
        )

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

    @property
    def alt_labels(self) -> list[str]:
        return sorted(self.__alt_labels, key=lambda label: len(label), reverse=True)

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
