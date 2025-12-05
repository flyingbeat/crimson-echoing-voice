from core import IMG, SCHEMA

from .Answer import Answer


class MultiMediaAnswer(Answer):

    def answer(self) -> list[str]:
        if self._message.entities:
            image_type = SCHEMA.Poster if "poster" in self._message.content.lower() else SCHEMA.Backdrop
            for key, image_list in self._message.entities[0].images.items():
                if (key.uri == image_type) and image_list:
                    return [str(image.uri) for image in image_list]
        if self._message.properties:
            for image_list in self._message.properties[0].images.values():
                if image_list:
                    return [str(image.uri) for image in image_list]
        return []

    def formatted_answer(self) -> str:
        answer = self.answer()
        if not answer:
            return "I couldn't find any multimedia content based on your input."
        formatted_image_uris = [
            self.__format_image_uri(image_uri) for image_uri in answer
        ]
        return formatted_image_uris[0]

    @staticmethod
    def __format_image_uri(image_uri: str) -> str:
        uri = str(image_uri)
        image_id = uri.removeprefix(str(IMG)).removesuffix(".jpg")
        return f"image:{image_id}"
