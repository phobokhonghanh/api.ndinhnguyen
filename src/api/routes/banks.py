from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.banks import get_banks_list
from core.responses import Response, json_response

router = APIRouter(tags=["Banks"])


class BankSchema(BaseModel):
    code: str = Field(..., description="Mã ngân hàng (ví dụ: MB, VCB, TCB, ACB)", json_schema_extra={"example": "MB"})
    name: str = Field(..., description="Tên đầy đủ của ngân hàng", json_schema_extra={"example": "Ngân hàng TMCP Quân Đội"})
    short_name: str = Field(..., description="Tên viết tắt của ngân hàng", json_schema_extra={"example": "MBBank"})
    bin: str = Field(..., description="Mã BIN ngân hàng VietQR", json_schema_extra={"example": "970422"})
    logo: str = Field(..., description="URL logo ngân hàng", json_schema_extra={"example": "https://api.vietqr.io/img/MB.png"})


@router.get(
    "/api/banks",
    response_model=Response[list[BankSchema]],
    summary="Lấy danh sách các ngân hàng Việt Nam",
    description="Trả về danh sách tất cả các ngân hàng Việt Nam đã được sắp xếp theo thứ tự bảng chữ cái để hiển thị trên giao diện chọn ngân hàng (dropdown). API này công khai và không yêu cầu xác thực.",
)
async def get_banks() -> JSONResponse:
    """
    Returns list of supported Vietnamese banks sorted alphabetically.
    """
    banks = get_banks_list()
    return json_response(data=banks)
