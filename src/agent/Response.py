from core import KnowledgeGraph

from .Answer import Answer
from .FactualAnswer import FactualAnswer
from .Message import Message
from .MultiMediaAnswer import MultiMediaAnswer
from .RecommendationAnswer import RecommendationAnswer


class Response(str):

    def __new__(cls, message: Message, knowledge_graph: KnowledgeGraph):
        AnswerType = cls.__get_answer_type(message)
        answer_instance = AnswerType(message, knowledge_graph)
        answer = answer_instance.formatted_answer()
        obj = str.__new__(cls, answer)
        obj.answer_type = AnswerType.__name__
        obj.answer = answer_instance.answer()
        return obj

    def __repr__(self):
        return f"Response(answer_type={self.answer_type}, content={super().__str__()}, answers={self.answer})"

    @staticmethod
    def __get_answer_type(message: Message) -> type[Answer]:
        text = message.content.lower()

        keywords = {
            MultiMediaAnswer: [
                "picture",
                "image",
                "photo",
                "poster",
                "look like",
                "show me",
                "visual",
                "img",
            ],
            RecommendationAnswer: [
                "recommend",
                "suggestion",
                "suggest",
                "similar",
                "like",
                "liked",
                "enjoy",
                "enjoyed",
                "favorite",
                "other movies",
                "watch",
                "best",
            ],
            FactualAnswer: [
                "who",
                "what",
                "when",
                "where",
                "directed",
                "director",
                "writer",
                "screenwriter",
                "composed",
                "composer",
                "genre",
                "release",
                "date",
                "year",
                "budget",
                "cost",
                "box office",
                "nominated",
                "award",
                "won",
                "did",
                "star",
                "cast",
                "play",
                "role",
            ],
        }

        scores = {key: 0 for key in keywords}

        for category, tokens in keywords.items():
            for token in tokens:
                if token in text:
                    if token in ["recommend", "image", "poster", "picture"]:
                        scores[category] += 2
                    else:
                        scores[category] += 1

        best_match = max(scores, key=scores.get)

        if scores[best_match] == 0:
            return FactualAnswer

        return best_match
