from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field
from features.cashbacks.shopee.schemas import Conversion

class CashbackRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., alias="userId")
    platform: str
    cashback: float
    status: str
    checkout_id: str = Field(..., alias="checkoutId")
    conversion: Conversion | None = None
    created_at: str | None = Field(None, alias="createdAt")
    updated_at: str | None = Field(None, alias="updatedAt")
