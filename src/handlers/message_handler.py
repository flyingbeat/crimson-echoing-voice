import rdflib
from SPARQLWrapper import JSON, SPARQLWrapper
from thefuzz import fuzz, process
import re

WD = rdflib.Namespace("http://www.wikidata.org/entity/")
WDT = rdflib.Namespace("http://www.wikidata.org/prop/direct/")
DDIS = rdflib.Namespace("http://ddis.ch/atai/")
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace("http://schema.org/")

EMBEDDING_REL_MAPPING = {
    "director": ["director", "directed", "directs", "direct"],
    "award": ["award", "oscar", "prize"],
    "publication date": [
        "release",
        "date",
        "released",
        "releases",
        "release date",
        "publication",
        "launch",
        "broadcast",
        "launched",
        "come out",
    ],
    "executive producer": ["showrunner", "executive producer"],
    "screenwriter": ["screenwriter", "scriptwriter", "writer", "story"],
    "film editor": ["editor", "film editor"],
    "box office": ["box", "office", "funding", "box office"],
    "cost": ["budget", "cost"],
    "nominated for": [
        "nomination",
        "award",
        "finalist",
        "shortlist",
        "selection",
        "nominated for",
    ],
    "production company": [
        "company",
        "company of production",
        "produced",
        "production company",
    ],
    "country of origin": ["origin", "country", "country of origin"],
    "cast member": ["actor", "actress", "cast", "cast member"],
    "genre": ["type", "kind", "genre"],
}


class MessageHandler:
    def __init__(self, data_handler, fuzzy_threshold=70):
        self.data_handler = data_handler
        self.fuzzy_threshold = fuzzy_threshold
        self.relation_labels = self._load_relation_labels_from_graph()
        self.entity_labels = self._load_entity_labels_from_graph()
        self.entity_descriptions = self._load_entity_descriptions_from_graph()

    def _load_relation_labels_from_graph(self) -> dict[rdflib.URIRef, str]:
        if not self.data_handler.graph:
            print("Warning: Graph not loaded. Cannot extract relation labels.")
            return {}

        print("Loading and filtering relation labels directly from the graph...")
        labels = {}

        try:
            query = f"""
            SELECT ?relation ?label
            WHERE {{
                ?relation <http://www.w3.org/2000/01/rdf-schema#label> ?label .
                FILTER(STRSTARTS(STR(?relation), "{str(WDT)}"))
            }}
            """
            self.data_handler.graph.setQuery(query)
            results = self.data_handler.graph.queryAndConvert()

            for result in results["results"]["bindings"]:
                relation_uri = rdflib.URIRef(result["relation"]["value"])
                label = str(result["label"]["value"])
                labels[relation_uri] = label

        except Exception as e:
            print(f"Error loading relation labels: {e}")

        print(f"Found {len(labels)} direct relation labels in the graph.")
        return labels

    def _load_entity_labels_from_graph(self) -> dict[rdflib.URIRef, str]:
        if not self.data_handler.graph:
            print("Warning: Graph not loaded. Cannot extract entity labels.")
            return {}

        print("Loading and filtering entity labels for movies only from the graph...")
        labels = {}

        try:
            query = f"""
            SELECT ?entity ?label
            WHERE {{
                ?entity <http://www.wikidata.org/prop/direct/P31> <http://www.wikidata.org/entity/Q11424> .
                ?entity <http://www.w3.org/2000/01/rdf-schema#label> ?label .
                FILTER(STRSTARTS(STR(?entity), "{str(WD)}"))
            }}
            """
            self.data_handler.graph.setQuery(query)
            results = self.data_handler.graph.queryAndConvert()

            for result in results["results"]["bindings"]:
                entity_uri = rdflib.URIRef(result["entity"]["value"])
                label = str(result["label"]["value"])
                labels[entity_uri] = label

        except Exception as e:
            print(f"Error loading entity labels: {e}")

        print(f"Found {len(labels)} movie entity labels in the graph.")
        return labels

    def _load_entity_descriptions_from_graph(self) -> dict[rdflib.URIRef, str]:
        if not self.data_handler.graph:
            print("Warning: Graph not loaded. Cannot extract entity descriptions.")
            return {}

        print("Loading and filtering entity descriptions directly from the graph...")
        descriptions = {}

        try:
            query = f"""
            SELECT ?entity ?description
            WHERE {{
                ?entity <http://schema.org/description> ?description .
                FILTER(STRSTARTS(STR(?entity), "{str(WD)}"))
            }}
            """
            self.data_handler.graph.setQuery(query)
            results = self.data_handler.graph.queryAndConvert()

            for result in results["results"]["bindings"]:
                entity_uri = rdflib.URIRef(result["entity"]["value"])
                description = str(result["description"]["value"])
                descriptions[entity_uri] = description

        except Exception as e:
            print(f"Error loading entity descriptions: {e}")

        print(f"Found {len(descriptions)} entity descriptions in the graph.")
        return descriptions

    def _normalize_query_for_relations(self, query: str) -> str:
        normalized = query.lower()
        words = normalized.split()

        for canonical, syn_list in EMBEDDING_REL_MAPPING.items():
            for synonym in sorted(syn_list, key=len, reverse=True):
                synonym_lower = synonym.lower()

                if synonym_lower in normalized:
                    normalized = normalized.replace(synonym_lower, canonical.lower())
                else:
                    if " " in synonym_lower:
                        if fuzz.partial_ratio(synonym_lower, normalized) > 85:
                            best_match = process.extractOne(
                                synonym_lower,
                                [normalized[i : i + len(synonym_lower) + 10] for i in range(len(normalized))],
                                scorer=fuzz.partial_ratio,
                            )
                            if best_match and best_match[1] > 85:
                                normalized = normalized.replace(synonym_lower, canonical.lower())
                    else:
                        for word in words:
                            if fuzz.ratio(synonym_lower, word) > 85:
                                normalized = normalized.replace(word, canonical.lower())
                                break

        return normalized

    def find_relations_in_query(
        self, query: str
    ) -> list[tuple[rdflib.URIRef, int, str]]:
        if not self.relation_labels:
            print("Error: Relation labels are not loaded. Cannot find relations.")
            return []

        query_lower = query.lower()
        normalized_query = self._normalize_query_for_relations(query)
        matches = []

        for rel_uri, rel_label in self.relation_labels.items():
            if not rel_label:
                continue

            rel_label_lower = rel_label.lower()

            if rel_label_lower in query_lower:
                score = 100 + len(rel_label_lower)
                matches.append((rel_uri, score, rel_label))
            elif rel_label_lower in normalized_query:
                score = 98 + len(rel_label_lower)
                matches.append((rel_uri, score, rel_label))
            else:
                fuzzy_score = fuzz.partial_ratio(rel_label_lower, query_lower)

                if fuzzy_score > self.fuzzy_threshold:
                    adjusted_score = fuzzy_score + (len(rel_label_lower) * 0.5)
                    matches.append((rel_uri, int(adjusted_score), rel_label))

        matches.sort(key=lambda x: (x[1], len(x[2])), reverse=True)
        return matches

    def find_entities_in_query(
            self, query: str
    ) -> list[tuple[rdflib.URIRef, int, str, str]]:
        if not self.entity_labels:
            print("Error: Entity labels are not loaded. Cannot find entities.")
            return []

        remaining_query = query.lower()
        matches = []

        # Sort entity labels by length (longest first) to match longer titles first
        sorted_entities = sorted(
            self.entity_labels.items(),
            key=lambda x: len(x[1]) if x[1] else 0,
            reverse=True
        )

        for entity_uri, entity_label in sorted_entities:
            if not entity_label:
                continue

            # Use regex to match full words only
            # \b asserts a word boundary
            # re.escape handles special characters in the label
            pattern = r'\b' + re.escape(entity_label.lower()) + r'\b'

            # Search for the pattern in the remaining query
            match = re.search(pattern, remaining_query)

            if match:
                # A score above 100 for exact (case-insensitive) matches
                score = 100 + len(entity_label)
                matches.append(
                    (
                        entity_uri,
                        score,
                        entity_label,
                        self.entity_descriptions.get(entity_uri, ""),
                    )
                )
                # Remove the matched entity from the query to avoid re-matching
                # The '1' ensures only the first occurrence is replaced
                remaining_query = re.sub(pattern, ' ', remaining_query, 1)

        # Sort matches by score (and then by label length as a tie-breaker)
        matches.sort(key=lambda x: (x[1], len(x[2])), reverse=True)
        return matches
