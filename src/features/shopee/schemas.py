from typing import Any
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
