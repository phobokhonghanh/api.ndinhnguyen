from typing import Any, List
from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    itemId: int | None = Field(None, alias="itemId")
    productName: str = Field(..., alias="productName")
    shopName: str | None = Field(None, alias="shopName")
    price: int = Field(..., alias="price")
    sales: int | None = Field(None, alias="sales")
    imageUrl: str | None = Field(None, alias="imageUrl")
    productLink: str | None = Field(None, alias="productLink")
    rating: Any | None = Field(None, alias="rating")
    commission: float | int | None = Field(None, alias="commission")
    sellerComFinal: float | int | None = Field(None, alias="sellerComFinal")
    shopeeComFinal: float | int | None = Field(None, alias="shopeeComFinal")
    isXtra: bool | None = Field(None, alias="isXtra")
    hasSellerCommission: bool | None = Field(None, alias="hasSellerCommission")
    hasShopeeCommission: bool | None = Field(None, alias="hasShopeeCommission")
    isCapped: bool | None = Field(None, alias="isCapped")
    isLimitCap: bool | None = Field(None, alias="isLimitCap")
    cap: float | int | None = Field(None, alias="cap")
    capRaw: float | int | None = Field(None, alias="capRaw")
    capAfterRate: float | int | None = Field(None, alias="capAfterRate")
    lastUpdate: str | None = Field(None, alias="lastUpdate")
    dataSource: str | None = Field(None, alias="dataSource")


class AffiliateRequest(BaseModel):
    link: str
    affiliate_id: str
    sub_ids: list[str] = Field(default_factory=list)
    deep_and_deferred: int = 1


class AffiliateResponseData(BaseModel):
    affiliate_link: str
    product: Product | None = None


class AffiliateResponseEnvelope(BaseModel):
    ok: bool
    code: str
    data: AffiliateResponseData


class ConversionItem(BaseModel):
    display_item_status: str | None = None
    affiliate_item_status: int | None = None
    shop_id: int | None = None
    shop_name: str | None = None
    item_id: int | None = None
    item_name: str | None = None
    item_price: int | None = None
    item_commission: int | None = None
    img_code: str | None = None
    actual_amount: int | None = None
    qty: int | None = None
    is_fraud: int | None = None
    fraud_reason: str | None = None
    fraud_status: int | None = None
    platform_commission_rate: int | None = None


class ConversionOrder(BaseModel):
    order_id: str | None = None
    order_status: str | None = None
    display_order_status: int | None = None
    complete_time: int | None = None
    fraud_complete_time: int | None = None
    items: list[ConversionItem] = []


class ConversionRecord(BaseModel):
    purchase_time: int | None = None
    checkout_id: str | None = None
    checkout_status: str | None = None
    checkout_status_app: int | None = None
    checkout_complete_time: int | None = None
    affiliate_id: int | None = None
    affiliate_name: str | None = None
    affiliate_net_commission: str | None = None
    utm_content: str | None = None
    device: str | None = None
    orders: list[ConversionOrder] = []


class ConversionReportData(BaseModel):
    page_num: int
    page_size: int
    total_count: int
    list: List[ConversionRecord] = []


class ConversionReportEnvelope(BaseModel):
    ok: bool
    code: str
    data: ConversionReportData | None = None
