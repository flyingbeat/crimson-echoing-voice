from core import Entity, KnowledgeGraph, Relation


class FactualAnswers:

    def __init__(
        self,
        entity: Entity | None,
        relation: Relation | None,
        knowledge_graph: KnowledgeGraph,
    ):
        self.__entity = entity
        self.__relation = relation
        self.__knowledge_graph = knowledge_graph

    @property
    def answers(self) -> list[str]:
        if self.__entity is None or self.__relation is None:
            return []

        forward_triplets = self.__knowledge_graph.get_triplets(
            entity=self.__entity, relation=self.__relation
        )
        if forward_triplets:
            return [str(p) for _, _, p in forward_triplets]

        backward_triplets = self.__knowledge_graph.get_triplets(
            relation=self.__relation, property=self.__entity
        )

        if backward_triplets:
            return [str(e) for e, _, _ in backward_triplets]
        return []
