from random import choice

from core import Entity, Relation

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
        factual_answer_intros = [
            "The answer to your question is:",
            "According to my data:",
            "Here is the information you asked for:",
            "I found this information:",
            "The answer is:",
        ]
        answer_intro = choice(factual_answer_intros)
        answer_text = " and ".join(answers)
        return f"{answer_intro} {answer_text}"

    def __get_entity_relation(self) -> tuple[Entity | None, Relation | None]:
        entities = self._message.entities
        relations = self._message.relations

        if entities and relations:
            return entities[0], relations[0]

        return None, None
