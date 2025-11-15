from rdflib import RDFS, Namespace, URIRef
from SPARQLWrapper import JSON, SPARQLWrapper

from Entity import Entity
from Property import Property
from Relation import Relation
from SPARQLQuery import SPARQLQuery

WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
DDIS = Namespace("http://ddis.ch/atai/")
SCHEMA = Namespace("http://schema.org/")


class KnowledgeGraph:
    def __init__(self, endpoint_url: str = "http://localhost:3030/atai/sparql"):
        self.__endpoint_url = endpoint_url
        self.__graph = self.__load_graph(self.__endpoint_url)
        self.__entities = None
        self.__relations = None

    def get_uri(self, label: str) -> URIRef:
        triplet = self.get_triplets(None, Relation(RDFS.label, self), label)
        if triplet:  # TODO what if more than one >>> and len(triplet) == 1:
            return triplet[0][0].uri
        return ""

    def get_label(self, uri: URIRef) -> str:
        triplet = self.get_triplets(
            Entity(uri, None, self), Relation(RDFS.label, self), None
        )
        if triplet and isinstance(triplet[0][2], str):
            return triplet[0][2]
        return ""

    def get_description(self, uri: URIRef) -> str:
        triplet = self.get_triplets(
            Entity(uri, None, self), Relation(SCHEMA.description, self), None
        )
        if triplet and isinstance(triplet[0][2], str):
            return triplet[0][2]
        return ""

    def get_properties(self, entity: Entity) -> list[tuple[Relation, Entity]]:
        return self.get_triplets(entity=entity, relation=None, property=None)

    @property
    def relations(self) -> list[URIRef]:
        if self.__relations is None:
            self.__relations = self.__get_relations()
        return self.__relations

    def __get_relations(self) -> list[URIRef]:
        query = f"""
            SELECT ?uri WHERE {{
                ?uri <{RDFS.label}> ?label .
                FILTER(STRSTARTS(STR(?uri), "{WDT}"))
            }}
        """
        query_result = SPARQLQuery(self.__graph, query).query_and_convert()
        return [
            Relation.from_binding(relation, self) for relation in query_result["uri"]
        ]

    @property
    def entities(self) -> list[Entity]:
        if self.__entities is None:
            self.__entities = self.__get_entities_with_labels()
        return self.__entities

    def __get_entities_with_labels(self) -> list[Entity]:
        query = f"""
            SELECT ?uri ?label
            WHERE {{
                ?uri <{RDFS.label}> ?label .
                ?uri <http://www.wikidata.org/prop/direct/P31> <http://www.wikidata.org/entity/Q11424> .
                FILTER(STRSTARTS(STR(?uri), "{WD}"))
            }}
        """
        query_result = SPARQLQuery(self.__graph, query).query_and_convert()
        return [
            Entity(uri["value"], label["value"], self)
            for uri, label in zip(query_result["uri"], query_result["label"])
        ]

    def get_triplets(
        self,
        entity: Entity = None,
        relation: Relation = None,
        property: Property = None,
    ) -> list[tuple[Entity, Relation, Property]]:
        entity_value_or_var = f"<{entity}>" if entity else "?entity"
        relation_value_or_var = f"<{relation}>" if relation else "?relation"
        property_value_or_var = f"<{property}>" if property else "?property"

        query = f"""
            SELECT {"?entity" if entity is None else ""} {"?relation" if relation is None else ""} {"?property" if property is None else ""}  WHERE {{
                {entity_value_or_var} {relation_value_or_var} {property_value_or_var} .
            }}
        """
        results = SPARQLQuery(self.__graph, query).query_and_convert()
        e, r, p = (
            results.get("entity"),
            results.get("relation"),
            results.get("property"),
        )
        num_results = len(e) if e else len(r) if r else len(p) if p else 0
        return [
            (
                Entity.from_binding(e[i], self) if e else entity_value_or_var,
                Relation.from_binding(r[i], self) if r else relation,
                (
                    (
                        Entity.from_binding(p[i], self)
                        if p[i]["type"] == "uri"
                        else p[i]["value"]
                    )
                    if p
                    else property
                ),
            )
            for i in range(num_results)
        ]

    @staticmethod
    def __load_graph(endpoint_url: str) -> SPARQLWrapper:
        try:
            graph = SPARQLWrapper(endpoint_url)
            graph.setReturnFormat(JSON)
            print("Knowledge graph loaded successfully.")
            return graph
        except Exception as e:
            print(f"Failed to load graph: {e}")
        return None
