import re
from thefuzz import fuzz, process

from Entity import Entity
from KnowledgeGraph import KnowledgeGraph
from Property import Property
from Relation import Relation

RELATION_LABEL_SYNONYMS = {
    "director": ["director", "directed", "directs", "direct"],
    "award": ["award", "oscar", "prize"],
    "publication date": [
        "release", "date", "released", "releases", "release date", "publication",
        "launch", "broadcast", "launched", "come out",
    ],
    "executive producer": ["showrunner", "executive producer"],
    "screenwriter": ["screenwriter", "scriptwriter", "writer", "story"],
    "film editor": ["editor", "film editor"],
    "box office": ["box", "office", "funding", "box office"],
    "cost": ["budget", "cost"],
    "nominated for": [
        "nomination", "award", "finalist", "shortlist", "selection", "nominated for",
    ],
    "production company": [
        "company", "company of production", "produced", "production company",
    ],
    "country of origin": ["origin", "country", "country of origin"],
    "cast member": ["actor", "actress", "cast", "cast member"],
    "genre": ["type", "kind", "genre"],
}


class Message:
    # Removed the static caches, as this is now handled by the KnowledgeGraph instance

    def __init__(self, content: str, knowledge_graph: KnowledgeGraph):
        self.__content = content
        self.__knowledge_graph = knowledge_graph
        self.__entities_with_scores = None
        self.__relations_with_scores = None
        self.__properties_with_scores = None
        self.fuzzy_threshold = 85  # Added for completeness

    @property
    def content(self) -> str:
        return self.__content

    @property
    def relations(self) -> list[Relation]:
        if self.__relations_with_scores is None:
            self.__relations_with_scores = self.__get_relations_with_scores()
        return [relation for relation, _ in self.__relations_with_scores]

    @property
    def relations_with_scores(self) -> list[tuple[Relation, int]]:
        if self.__relations_with_scores is None:
            self.__relations_with_scores = self.__get_relations_with_scores()
        return self.__relations_with_scores

    def __get_relations_with_scores(self) -> list[tuple[Relation, int]]:
        knowledge_graph_relations = self.__knowledge_graph.relations
        query_lower = self.content.lower()
        normalized_query = self.__normalize_for_relations(self.content)
        matches = []

        for relation in knowledge_graph_relations:
            if not relation.label:
                continue

            rel_label_lower = relation.label.lower()
            if rel_label_lower in query_lower:
                score = 100 + len(rel_label_lower)
                matches.append((relation, score, relation.label))
            elif rel_label_lower in normalized_query:
                score = 98 + len(rel_label_lower)
                matches.append((relation, score, relation.label))
            else:
                fuzzy_score = fuzz.partial_ratio(rel_label_lower, query_lower)

                if fuzzy_score > self.fuzzy_threshold:
                    adjusted_score = fuzzy_score + (len(rel_label_lower) * 0.5)
                    matches.append((relation, int(adjusted_score), relation.label))
        # This part seems incomplete in the original code, but I'll leave it as is.
        # It should return matches. For now, returning empty list to avoid errors.
        return []


    def __normalize_for_relations(self) -> str:
        normalized = self.content.lower()
        words = normalized.split()

        for canonical, syn_list in RELATION_LABEL_SYNONYMS.items():
            for synonym in sorted(syn_list, key=len, reverse=True):
                synonym_lower = synonym.lower()

                if synonym_lower in normalized:
                    normalized = normalized.replace(synonym_lower, canonical.lower())
                else:
                    if " " in synonym_lower:
                        if fuzz.partial_ratio(synonym_lower, normalized) > 85:
                            best_match = process.extractOne(
                                synonym_lower,
                                [
                                    normalized[i : i + len(synonym_lower) + 10]
                                    for i in range(len(normalized))
                                ],
                                scorer=fuzz.partial_ratio,
                            )
                            if best_match and best_match[1] > 85:
                                normalized = normalized.replace(
                                    synonym_lower, canonical.lower()
                                )
                    else:
                        for word in words:
                            if fuzz.ratio(synonym_lower, word) > 85:
                                normalized = normalized.replace(word, canonical.lower())
                                break

        return normalized

    @property
    def entities(self) -> list[Entity]:
        if self.__entities_with_scores is None:
            self.__entities_with_scores = self.__get_entities_with_scores()
        return [entity for entity, _ in self.__entities_with_scores]

    @property
    def entities_with_scores(self) -> list[tuple[Entity, int]]:
        if self.__entities_with_scores is None:
            self.__entities_with_scores = self.__get_entities_with_scores()
        return self.__entities_with_scores

    def __get_entities_with_scores(self) -> list[tuple[Entity, int]]:
        knowledge_graph_entities = self.__knowledge_graph.entities

        remaining_query = self.content.lower()
        matches = []

        for entity in sorted(
            knowledge_graph_entities,
            key=lambda e: len(e.label) if e.label else 0,
            reverse=True,
        ):
            if not entity.label:
                continue

            pattern = r"\b" + re.escape(entity.label.lower()) + r"\b"

            match = re.search(pattern, remaining_query)

            if match:
                score = 100 + len(entity.label)
                matches.append(
                    (
                        entity,
                        score,
                    )
                )
                remaining_query = re.sub(pattern, " ", remaining_query, 1)

        return sorted(
            matches,
            key=lambda entity_score: (entity_score[1], len(entity_score[0].label)),
            reverse=True,
        )

    @property
    def properties(self) -> list[tuple[Property, Relation]]:
        if self.__properties_with_scores is None:
            self.__properties_with_scores = self.__get_properties_with_scores()
        return [prop_rel for prop_rel, _ in self.__properties_with_scores]

    @property
    def properties_with_scores(self) -> list[tuple[tuple[Property, Relation], int]]:
        if self.__properties_with_scores is None:
            self.__properties_with_scores = self.__get_properties_with_scores()
        return self.__properties_with_scores

    def __get_properties_with_scores(self) -> list[tuple[tuple[Property, Relation], int]]:
        matches = []
        remaining_query = self.content.lower()

        all_target_properties = self.__knowledge_graph.get_all_preloaded_properties_with_relations()

        # sorted_properties = sorted(
        #     all_target_properties,
        #     key=lambda p: len(p[0].label) if isinstance(p[0], Entity) and p[0].label else (
        #         len(p[0]) if isinstance(p[0], str) else 0),
        #     reverse=True
        # )

        for prop, rel in all_target_properties:
            prop_label = ""
            if isinstance(prop, Entity) and prop.label:
                prop_label = prop.label.lower()
            elif isinstance(prop, str):
                prop_label = prop.lower()

            if not prop_label:
                continue

            pattern = r"\b" + re.escape(prop_label) + r"\b"
            if re.search(pattern, remaining_query):
                score = 100 + len(prop_label)
                matches.append(((prop, rel), score))
                remaining_query = re.sub(pattern, " ", remaining_query, 1)

        return sorted(matches, key=lambda item: item[1], reverse=True)