from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Product(BaseSchema):
    id: str | None = None
    name: str | None = None  # (Tên sản phẩm)
    shop: str | None = None  # (Tên cửa hàng)
    price: float | None = None  # (Giá)
    sales: int | None = None  # (Lượt bán)
    image: str | None = None  # (Ảnh)
    link: str | None = None  # (Link sản phẩm)
    rating: float | None = None  # (Đánh giá)
    commission: float | None = None  # (Hoa hồng)
    lastUpdate: str | None = None  # (Thời gian cập nhật)
    dataSource: str | None = None  # (Nguồn dữ liệu)


class Item(BaseSchema):
    product: Product | None = None
    qty: int | None = None  # (Số lượng)
    actual_amount: float | None = None  # (Số tiền thực tế)
    is_fraud: int | None = None  # (Có phải gian lận hay không)


class Order(BaseSchema):
    id: str | None = None
    order_sn: str | None = None  # (Mã đơn hàng)
    items: list[Item] | None = None  # (Danh sách sản phẩm trong đơn hàng)


class Conversion(BaseSchema):
    click_id: str | None = None  # (Click ID)
    click_time: int | None = None  # (Thời gian click)
    checkout_id: str | None = None  # (Checkout ID)
    purchase_time: int | None = None  # (Thời gian đặt hàng)
    checkout_complete_time: int | None = None  # (Thời gian hoàn thành đơn hàng)
    checkout_status: str | int | None = None  # (Trạng thái đơn hàng)
    affiliate_id: str | None = None  # (Affiliate ID)
    affiliate_net_commission: float | None = None  # (Hoa hồng)
    utm_content: str | None = None  # (UTM content)
    orders: list[Order] | None = None  # (Danh sách đơn hàng)


class AffiliateRequest(BaseSchema):
    link: str  # (Link sản phẩm)
    affiliate_id: str  # (Affiliate ID)
    sub_ids: list[str] = Field(default_factory=list)  # (Sub ID)
    deep_and_deferred: int = 1  # (Deep and deferred)


class AffiliateResponseData(BaseSchema):
    affiliate_link: str  # (Link affiliate)
    product: Product | None = None  # (Thông tin sản phẩm)
