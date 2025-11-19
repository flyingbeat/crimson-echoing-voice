from rdflib import RDFS, Namespace, URIRef
from SPARQLWrapper import JSON, SPARQLWrapper

from utils import BindingDict, SPARQLQuery

from .Entity import Entity
from .Property import Property
from .Relation import Relation

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
        self.__relevant_instance_of = Entity.instance_of_movies(
            self
        ) + Entity.instance_of_movie_properties(self)

    def get_uri(self, label: str) -> URIRef:
        triplet = self.get_triplets(None, Relation(RDFS.label, self), label)
        if triplet:  # TODO what if more than one >>> and len(triplet) == 1:
            return triplet[0][0].uri
        return ""

    def get_label(self, uri: URIRef) -> str:
        triplet = self.get_triplets(Entity(uri, self), Relation(RDFS.label, self), None)
        if triplet and isinstance(triplet[0][2], str):
            return triplet[0][2]
        return ""

    def get_description(self, uri: URIRef) -> str:
        triplet = self.get_triplets(
            Entity(uri, self), Relation(SCHEMA.description, self), None
        )
        if triplet and isinstance(triplet[0][2], str):
            return triplet[0][2]
        return ""

    def get_properties(self, entity: Entity) -> list[tuple[Relation, Entity]]:
        return self.get_triplets(
            entity=entity, relation=None, property=None, distinct=True
        )

    def query(self, query_string: str) -> dict[str, list[BindingDict]]:
        return SPARQLQuery(self.__graph, query_string).query_and_convert()

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
            self.__entities = self.__get_relevant_entities_with_labels()
        return self.__entities

    def __get_relevant_entities_with_labels(self) -> list[Entity]:
        condition_triplets = [
            (None, Relation.instance_of(self), e) for e in self.__relevant_instance_of
        ]

        query = f"""
            SELECT ?uri ?label ?instance_of
            WHERE {{
                ?uri <{RDFS.label}> ?label .
                ?uri <http://www.wikidata.org/prop/direct/P31> ?instance_of .
                {{ {SPARQLQuery.union_clauses(condition_triplets, ["uri"])} }}
                FILTER(STRSTARTS(STR(?uri), "{WD}"))
            }}
        """
        query_result = SPARQLQuery(self.__graph, query).query_and_convert()
        return [
            Entity(
                URIRef(uri["value"]),
                self,
                label["value"],
                (
                    URIRef(instance_of["value"])
                    if instance_of["type"] == "uri"
                    else instance_of
                ),
            )
            for uri, label, instance_of in zip(
                query_result["uri"], query_result["label"], query_result["instance_of"]
            )
        ]

    def get_triplets(
        self,
        entity: Entity = None,
        relation: Relation = None,
        property: Property = None,
        distinct: bool = False,
    ) -> list[tuple[Entity, Relation, Property]]:
        entity_value_or_var = f"<{entity.uri}>" if entity else "?entity"
        relation_value_or_var = f"<{relation.uri}>" if relation else "?relation"

        property_value_or_var = "?property"
        if property is not None:
            if isinstance(property, Entity) or hasattr(property, "uri"):
                property_value_or_var = f"<{property.uri}>"
            else:
                clean_property = str(property).replace('"', '\\"')
                property_value_or_var = f'"{clean_property}"'

        query = f"""
            SELECT {"DISTINCT" if distinct else ""} {"?entity" if entity is None else ""} {"?relation" if relation is None else ""} {"?property" if property is None else ""}  WHERE {{
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
                Entity.from_binding(e[i], self) if e else entity,
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
            return graph
        except Exception as e:
            print(f"Failed to load graph: {e}")
        return None
