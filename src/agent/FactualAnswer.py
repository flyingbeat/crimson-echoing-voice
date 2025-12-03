from core import Entity, Relation
from llm import LargeLanguageModel

from .Answer import Answer


class FactualAnswer(Answer):

    def answer(self) -> list[str]:
        entity, relation = self.__get_entity_relation()
        if entity is None or relation is None:
            return []

        forward_triplets = self._knowledge_graph.get_triplets(
            entity=entity, relation=relation
        )
        if forward_triplets:
            return [str(p) for _, _, p in forward_triplets]

        backward_triplets = self._knowledge_graph.get_triplets(
            relation=relation, property=entity
        )

        if backward_triplets:
            return [str(e) for e, _, _ in backward_triplets]
        return []

    def formatted_answer(self) -> str:
        answers = self.answer()
        if not answers:
            return "I'm not sure about the answer to that specific question."
        llm = LargeLanguageModel()
        answer = llm.prompt(
            self._message.content, context=" and ".join(answers), max_tokens=150
        )

        return answer

    def __get_entity_relation(self) -> tuple[Entity | None, Relation | None]:
        entities = self._message.entities
        relations = self._message.relations

        if entities and relations:
            return entities[0], relations[0]

        return None, None
