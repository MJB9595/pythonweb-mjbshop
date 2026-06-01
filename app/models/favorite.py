from odmantic import Model


class FavoriteModel(Model):
    product_id: str    # 네이버 쇼핑 상품 ID (고유 키)
    title: str
    link: str
    image: str
    lprice: int
    hprice: int
    mall_name: str
    brand: str
    maker: str
    category1: str
    category2: str
    category3: str
    category4: str

    model_config = {"collection": "favorites"}
