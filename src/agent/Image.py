class Image:

    def __init__(self, identifier: str):
        self.__id = identifier

    def __str__(self):
        return self.__id.removesuffix(".jpg")
