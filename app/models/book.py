from odmantic import Model


class BookModel(Model):
    keyword: str
    title: str
    author: str
    publisher: str
    price: int
    image: str

    model_config = {"collection": "books"}
