import re

from thefuzz import fuzz, process

from core import Entity, KnowledgeGraph, Relation

RELATION_LABEL_SYNONYMS = {
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
    "film": ["movie"],
}


class Message:

    def __init__(self, content: str, knowledge_graph: KnowledgeGraph):
        self.__content = content
        self.__entities_with_scores = None
        self.__relations_with_scores = None
        self.__knowledge_graph = knowledge_graph
        self.__relevant_instance_of_entities = Entity.instance_of_movies(
            self.__knowledge_graph
        )
        self.__fuzzy_threshold = 85

    @property
    def content(self) -> str:
        return self.__content

    @content.setter
    def content(self, value: str):
        self.__content = value

    @property
    def relations(self) -> list[Relation]:
        if self.relations_with_scores is not None:
            return [relation for relation, _ in self.relations_with_scores]
        return []

    @property
    def relations_with_scores(self) -> list[tuple[Relation, int]]:
        if self.__relations_with_scores is None:
            self.__relations_with_scores = self.__get_relations_with_scores()
        return self.__relations_with_scores

    def __get_relations_with_scores(self) -> list[tuple[Relation, int]]:
        knowledge_graph_relations = self.__knowledge_graph.relations
        query_lower = self.content.lower()
        normalized_query = self.__normalize_for_relations()
        matches = []

        for relation in knowledge_graph_relations:
            if not relation.label:
                continue

            rel_label_lower = relation.label.lower()
            if rel_label_lower in query_lower:
                score = 100 + len(rel_label_lower)
                matches.append((relation, score))
            elif rel_label_lower in normalized_query:
                score = 98 + len(rel_label_lower)
                matches.append((relation, score))
            else:
                fuzzy_score = fuzz.partial_ratio(rel_label_lower, query_lower)

                if fuzzy_score > self.__fuzzy_threshold:
                    adjusted_score = fuzzy_score + (len(rel_label_lower) * 0.5)
                    matches.append((relation, int(adjusted_score)))
        return matches

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
                        if (
                            fuzz.partial_ratio(synonym_lower, normalized)
                            > self.__fuzzy_threshold
                        ):
                            best_match = process.extractOne(
                                synonym_lower,
                                [
                                    normalized[i : i + len(synonym_lower) + 10]
                                    for i in range(len(normalized))
                                ],
                                scorer=fuzz.partial_ratio,
                            )
                            if best_match and best_match[1] > self.__fuzzy_threshold:
                                normalized = normalized.replace(
                                    synonym_lower, canonical.lower()
                                )
                    else:
                        for word in words:
                            if fuzz.ratio(synonym_lower, word) > self.__fuzzy_threshold:
                                normalized = normalized.replace(word, canonical.lower())
                                break

        return normalized

    @property
    def entities(self) -> list[Entity]:
        return [
            entity
            for entity, _ in self.entities_with_scores
            if any(
                instance in self.__relevant_instance_of_entities
                for instance in entity.instance_of
            )
        ]

    @property
    def properties(self) -> list[Entity]:
        return [
            entity
            for entity, _ in self.entities_with_scores
            if not any(
                instance in self.__relevant_instance_of_entities
                for instance in entity.instance_of
            )
        ]

    @property
    def entities_with_scores(self) -> list[tuple[Entity, int]]:
        if self.__entities_with_scores is None:
            self.__entities_with_scores = self.__get_entities_with_scores()
        return self.__entities_with_scores

    def __get_entities_with_scores(self) -> list[tuple[Entity, int]]:
        knowledge_graph_entities = self.__knowledge_graph.entities

        remaining_query = self.content.lower()
        matches = []

        for entity in knowledge_graph_entities:
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
