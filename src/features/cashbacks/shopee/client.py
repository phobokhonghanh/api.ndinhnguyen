from datetime import datetime, time as datetime_time, timezone, timedelta
from core.constants import SHOPEE_REPORT_LIST_URL_TEMPLATE
from infra.http import fetch_json


from api.helpers import get_shopee_cookie


class ShopeeAffiliateClient:
    def __init__(self, cookie: str | None = None):
        self.cookie = cookie or get_shopee_cookie()
        self.user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0"

    async def get_conversion_reports(
        self,
        page_size: int = 20,
        page_num: int = 1,
        sub_id: str | None = None,
        purchase_time_s: int | None = None,
        purchase_time_e: int | None = None,
    ) -> dict[str, object]:
        """
        Fetches raw conversion reports from Shopee API.
        Defaults purchase_time_s and purchase_time_e to the start and end of today in GMT+7.
        """
        if purchase_time_s is None or purchase_time_e is None:
            tz = timezone(timedelta(hours=7))
            today = datetime.now(tz).date()
            get_ts = lambda dt_time: int(datetime.combine(today, dt_time, tzinfo=tz).timestamp())
            
            purchase_time_s = purchase_time_s or get_ts(datetime_time.min)
            purchase_time_e = purchase_time_e or get_ts(datetime_time.max)

        url = SHOPEE_REPORT_LIST_URL_TEMPLATE.format(
            page_size=page_size,
            page_num=page_num,
            sub_id=sub_id if sub_id is not None else "",
            purchase_time_s=purchase_time_s,
            purchase_time_e=purchase_time_e,
        )

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://affiliate.shopee.vn/report/conversion_report",
            "Affiliate-Program-Type": "1",
            "Cookie": self.cookie,
        }

        return await fetch_json(url, headers=headers)
