import rdflib
from thefuzz import fuzz, process

WD = rdflib.Namespace('http://www.wikidata.org/entity/')
WDT = rdflib.Namespace('http://www.wikidata.org/prop/direct/')
DDIS = rdflib.Namespace('http://ddis.ch/atai/')
RDFS = rdflib.namespace.RDFS
SCHEMA = rdflib.Namespace('http://schema.org/')

EMBEDDING_REL_MAPPING = {
    "director": ["director", "directed", "directs", "direct"],
    "award": ["award", "oscar", "prize"],
    'publication date': ['release', 'date', 'released', 'releases', 'release date', 'publication', 'launch',
                         'broadcast', 'launched'],
    'executive producer': ['showrunner', 'executive producer'],
    'screenwriter': ['screenwriter', 'scriptwriter', 'writer', 'story'],
    'film editor': ['editor', 'film editor'],
    'box office': ['box', 'office', 'funding', 'box office'],
    'cost': ['budget', 'cost'],
    'nominated for': ['nomination', 'award', 'finalist', 'shortlist', 'selection', 'nominated for'],
    'production company': ['company', 'company of production', "produced", 'production company'],
    'country of origin': ['origin', 'country', 'country of origin'],
    'cast member': ['actor', 'actress', 'cast', 'cast member'],
    'genre': ['type', 'kind', 'genre'],
}


class QueryHandler:
    def __init__(self, data_handler, fuzzy_threshold=70):
        self.data_handler = data_handler
        self.fuzzy_threshold = fuzzy_threshold
        self.relation_labels = self._load_relation_labels_from_graph()
        self.entity_labels = self._load_entity_labels_from_graph()
        self.relation_synonyms = self._build_relation_synonyms()

    def _load_relation_labels_from_graph(self) -> dict[rdflib.URIRef, str]:
        if not self.data_handler.graph:
            print("Warning: Graph not loaded. Cannot extract relation labels.")
            return {}

        print("Loading and filtering relation labels directly from the graph...")
        labels = {}
        for s, p, o in self.data_handler.graph.triples((None, RDFS.label, None)):
            if isinstance(s, rdflib.URIRef) and str(s).startswith(str(WDT)):
                labels[s] = str(o)

        print(f"Found {len(labels)} direct relation labels in the graph.")
        return labels

    def _load_entity_labels_from_graph(self) -> dict[rdflib.URIRef, str]:
        if not self.data_handler.graph:
            print("Warning: Graph not loaded. Cannot extract entity labels.")
            return {}

        print("Loading and filtering entity labels directly from the graph...")
        labels = {}
        for s, p, o in self.data_handler.graph.triples((None, RDFS.label, None)):
            if isinstance(s, rdflib.URIRef) and str(s).startswith(str(WD)):
                labels[s] = str(o)

        print(f"Found {len(labels)} entity labels in the graph.")
        return labels

    def _build_relation_synonyms(self) -> dict[rdflib.URIRef, list[str]]:
        synonym_map = {}
        for rel_uri, rel_label in self.relation_labels.items():
            synonyms = [rel_label.lower()]
            for canonical, syn_list in EMBEDDING_REL_MAPPING.items():
                if fuzz.ratio(rel_label.lower(), canonical) > 90:
                    synonyms.extend([s.lower() for s in syn_list])
            synonym_map[rel_uri] = list(set(synonyms))
        return synonym_map

    def find_relations_in_query(self, query: str) -> list[tuple[rdflib.URIRef, int, str]]:
        if not self.relation_labels:
            print("Error: Relation labels are not loaded. Cannot find relations.")
            return []

        query_lower = query.lower()
        matches = []

        for rel_uri, synonyms in self.relation_synonyms.items():
            best_match, score = process.extractOne(query_lower, synonyms, scorer=fuzz.token_set_ratio)

            if score > self.fuzzy_threshold:
                canonical_label = self.relation_labels.get(rel_uri, "")
                matches.append((rel_uri, int(score), canonical_label))

        matches.sort(key=lambda x: x[1], reverse=True)

        return matches

    def find_entities_in_query(self, query: str) -> list[tuple[rdflib.URIRef, int, str]]:
        if not self.entity_labels:
            print("Error: Entity labels are not loaded. Cannot find entities.")
            return []

        query_lower = query.lower()
        matches = []

        for entity_uri, entity_label in self.entity_labels.items():
            if not entity_label:
                continue

            score = fuzz.WRatio(entity_label.lower(), query_lower)

            if score > self.fuzzy_threshold:
                matches.append((entity_uri, score, entity_label))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
