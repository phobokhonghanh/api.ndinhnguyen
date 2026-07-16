from features.cashbacks.shopee.helper import calculate_commission_cashback
from features.cashbacks.schemas import CashbackRecord
from features.cashbacks.interfaces import PlatformAdapter
from features.cashbacks.shopee.helper import extract_user_id_from_utm, map_raw_to_schema_conversion
from core.constants import (
    CASHBACK_STATUS_PENDING,
    CASHBACK_STATUS_APPROVED,
    CASHBACK_STATUS_COMPLETED,
    CASHBACK_STATUS_CANCELLED,
    SHOPEE_STATUS_PENDING,
    SHOPEE_STATUS_WAITING,
    SHOPEE_STATUS_COMPLETED,
    SHOPEE_STATUS_CANCELLED,
)

class ShopeePlatformAdapter(PlatformAdapter):
    """
    Platform adapter implementation for Shopee.
    Handles mapping Shopee API checkout statuses to standard cashback statuses,
    and extracting orders and user ids from Shopee conversion reports.
    """

    def map_status(self, raw_status: object) -> str:
        """
        Maps a Shopee raw status (which is one of the Shopee status constants)
        to a standard Cashback status.

        Args:
            raw_status (object): Raw status string from Shopee Affiliate API.

        Returns:
            str: One of the lowercase CASHBACK_STATUS constants.
        """
        shopee_to_cashback_map = {
            SHOPEE_STATUS_PENDING: CASHBACK_STATUS_PENDING,
            SHOPEE_STATUS_WAITING: CASHBACK_STATUS_APPROVED,
            SHOPEE_STATUS_COMPLETED: CASHBACK_STATUS_COMPLETED,
            SHOPEE_STATUS_CANCELLED: CASHBACK_STATUS_CANCELLED,
        }

        if not isinstance(raw_status, str):
            return CASHBACK_STATUS_PENDING

        return shopee_to_cashback_map.get(raw_status, CASHBACK_STATUS_PENDING)

    def extract_orders(self, record: dict[str, object]) -> CashbackRecord:
        """
        Extracts order items, calculates cashback amounts, and formats conversion data
        for each order present in a Shopee conversion record.

        Args:
            record (dict[str, object]): Raw Shopee conversion record.

        Returns:
            list[dict[str, object]]: List of extracted order dictionaries with keys:
                                  "cashback_amount", "conversion_data".
        """

        conversion = map_raw_to_schema_conversion(record)
        if conversion is None:
            return None

        user_id = extract_user_id_from_utm(conversion.utm_content)
        if not user_id:
            user_id = "system"

        affiliate_net_commission = conversion.affiliate_net_commission or 0.0
        cashback_amount = calculate_commission_cashback(affiliate_net_commission)
        cashback = CashbackRecord(
            userId=user_id,
            platform="shopee",
            cashback=cashback_amount,
            status=self.map_status(conversion.checkout_status),
            checkoutId=conversion.checkout_id or "",
            conversion=conversion
        )
        
        return cashback