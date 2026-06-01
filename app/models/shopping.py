from odmantic import Model


class ShoppingModel(Model):
    keyword: str
    title: str
    link: str
    image: str
    lprice: int         # 최저가
    hprice: int         # 최고가
    mall_name: str      # 쇼핑몰명
    product_id: str     # 네이버 쇼핑 상품 ID
    brand: str
    maker: str
    category1: str
    category2: str
    category3: str
    category4: str

    model_config = {"collection": "shopping"}
