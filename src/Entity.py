from collections import defaultdict
from typing import TYPE_CHECKING

from rdflib import URIRef

from Relation import Relation
from SPARQLQuery import BindingDict

if TYPE_CHECKING:
    from KnowledgeGraph import KnowledgeGraph
    from Property import Property


class Entity:
    def __init__(
        self,
        uri: URIRef,
        label: str | None,
        instance_of: URIRef | None,
        knowledge_graph: "KnowledgeGraph",
    ):
        self.__uri = uri
        self.__label: str | None = label
        self.__knowledge_graph = knowledge_graph
        self.__properties: dict["Relation", list["Property"]] = {}
        if instance_of:
            self.__properties[Relation.instance_of(knowledge_graph)] = [
                Entity(instance_of, None, None, knowledge_graph)
            ]

    def __repr__(self):
        return str(self.uri)

    def __hash__(self):
        return hash(self.__uri)

    def __eq__(self, other):
        if isinstance(other, Entity):
            return str(self.__uri) == str(other.__uri)
        return False

    @classmethod
    def movies(cls, knowledge_graph: "KnowledgeGraph") -> list["Entity"]:
        movie_instance_of_uris = [
            URIRef("http://www.wikidata.org/entity/Q11424"),  #'film'
            URIRef("http://www.wikidata.org/entity/Q17123180"),  #'sequel film'
            URIRef("http://www.wikidata.org/entity/Q202866"),  #'animated film'
            URIRef("http://www.wikidata.org/entity/Q622548"),  #'parody film'
            URIRef("http://www.wikidata.org/entity/Q622548"),  #'parody film'
            URIRef("http://www.wikidata.org/entity/Q10590726"),  #'video album'
            URIRef("http://www.wikidata.org/entity/Q917641"),  #'open-source film'
            URIRef(
                "http://www.wikidata.org/entity/Q52207399"
            ),  #'film based on a novel'
            URIRef("http://www.wikidata.org/entity/Q31235"),  #'remake'
            URIRef("http://www.wikidata.org/entity/Q24862"),  #'short film'
            URIRef("http://www.wikidata.org/entity/Q104840802"),  #'film remake'
            URIRef("http://www.wikidata.org/entity/Q112158242"),  #'Tom and Jerry film'
            URIRef("http://www.wikidata.org/entity/Q24856"),  #'film series'
            URIRef(
                "http://www.wikidata.org/entity/Q117467246"
            ),  #'animated television series'
            URIRef("http://www.wikidata.org/entity/Q2484376"),  #'thriller film',
            URIRef("http://www.wikidata.org/entity/Q20650540"),  #'anime film',
            URIRef("http://www.wikidata.org/entity/Q13593818"),  #'film trilogy'
            URIRef("http://www.wikidata.org/entity/Q17517379"),  #'animated short film'
            URIRef("http://www.wikidata.org/entity/Q678345"),  #'prequel'
            URIRef("http://www.wikidata.org/entity/Q1257444"),  #'film adaptation'
            URIRef(
                "http://www.wikidata.org/entity/Q52162262"
            ),  #'film based on literature'
            URIRef(
                "http://www.wikidata.org/entity/Q118189123"
            ),  #'animated film reboot'
            URIRef("http://www.wikidata.org/entity/Q1259759"),  #'miniseries'
            URIRef("http://www.wikidata.org/entity/Q506240"),  #'television film'
        ]
        return [
            cls(uri=uri, label=None, instance_of=None, knowledge_graph=knowledge_graph)
            for uri in movie_instance_of_uris
        ]

    @property
    def instance_of(self) -> list["Entity"]:
        P31 = Relation.instance_of(self.__knowledge_graph)
        if self.__properties and (instance_of := self.__properties.get(P31)):
            return instance_of
        triplets = self.__knowledge_graph.get_triplets(entity=self, relation=P31)
        instance_of = [p for _, _, p in triplets]
        self.__properties[P31] = instance_of
        return instance_of

    @property
    def uri(self) -> URIRef:
        return self.__uri

    @property
    def properties(self) -> dict["Relation", list["Property"]]:
        if not self.__properties:
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
    def film(cls, knowledge_graph: "KnowledgeGraph") -> "Entity":
        return cls(
            uri=URIRef("http://www.wikidata.org/entity/Q11424"),
            label="film",
            instance_of=None,
            knowledge_graph=knowledge_graph,
        )

    @classmethod
    def from_binding(
        cls, binding: BindingDict, knowledge_graph: "KnowledgeGraph"
    ) -> "Entity":
        if binding["type"] == "uri":
            uri = URIRef(binding.get("value"))
            return cls(
                uri=uri, label=None, instance_of=None, knowledge_graph=knowledge_graph
            )
        else:
            raise ValueError(
                f"Cannot create Entity from binding type: {binding['type']}"
            )
