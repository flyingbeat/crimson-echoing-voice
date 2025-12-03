from abc import ABC, abstractmethod

from core import KnowledgeGraph

from .Message import Message


class Answer(ABC):

    def __init__(self, message: Message, knowledge_graph: KnowledgeGraph):
        self._message = message
        self._knowledge_graph = knowledge_graph

    @abstractmethod
    def answer(self) -> list[str]:
        pass

    @abstractmethod
    def formatted_answer(self) -> str:
        pass
