from core import Entity, Relation
from llm import LargeLanguageModel

from .Answer import Answer


class FactualAnswer(Answer):

    def answer(self) -> list[str]:
        answers, _ = self.__get_factual_answer_with_context()
        return answers

    def formatted_answer(self) -> str:
        answers, context = self.__get_factual_answer_with_context()
        if not answers:
            return "I'm not sure about the answer to that specific question."

        llm = LargeLanguageModel()

        print(f"LLM(prompt='{self._message.content}', context='{context}')")

        answer = llm.prompt(self._message.content, context=context, max_tokens=150)

        return answer

    def __get_factual_answer_with_context(self) -> tuple[list[str], str]:
        entity, relation = self.__get_entity_relation()
        if entity is None or relation is None:
            return [], ""

        forward_triplets = self.__get_forward_triplets(entity, relation)
        if forward_triplets:
            context = "\n".join(
                f"{p} is {relation.label} of {entity.label}" for p in forward_triplets
            )
            return forward_triplets, context

        backward_triplets = self.__get_backward_triplets(relation, entity)
        if backward_triplets:
            context = "\n".join(
                f"{entity.label} is {relation.label} of {s}" for s in backward_triplets
            )
            return backward_triplets, context
        return [], ""

    def __get_forward_triplets(self, entity: Entity, relation: Relation) -> list[str]:
        triplets = self._knowledge_graph.get_triplets(entity=entity, relation=relation)
        return [str(p) for _, _, p in triplets]

    def __get_backward_triplets(
        self, relation: Relation, property: Entity
    ) -> list[str]:
        triplets = self._knowledge_graph.get_triplets(
            relation=relation, property=property
        )
        return [str(e) for e, _, _ in triplets]

    def __get_entity_relation(self) -> tuple[Entity | None, Relation | None]:
        entities = self._message.entities
        relations = self._message.relations

        if entities and relations:
            return entities[0], relations[0]

        return None, None
