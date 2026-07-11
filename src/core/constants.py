# Google OAuth API Endpoints
GOOGLE_TOKENINFO_URL_TEMPLATE = (
    "https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
)

# Shopee Integration Endpoints
SHOPEE_PRODUCT_DATA_URL_TEMPLATE = (
    "https://data.addlivetag.com/product-data/product-data.php?url={link}"
)
SHOPEE_AFFILIATE_REDIRECT_TEMPLATE = (
    "https://s.shopee.vn/an_redir"
    "?origin_link=https://shopee.vn/product/{shop_id}/{item_id}"
    "&affiliate_id={affiliate_id}"
    "&sub_id={sub_id}"
    "&deep_and_deferred={deep_and_deferred}"
)
SHOPEE_REPORT_LIST_URL_TEMPLATE = (
    "https://affiliate.shopee.vn/api/v3/report/list"
    "?page_size={page_size}&page_num={page_num}&version=1"
    "&sub_id={sub_id}&purchase_time_s={purchase_time_s}&purchase_time_e={purchase_time_e}"
)

SHOPEE_PRODUCT_LINK_TEMPLATE = (
    "https://shopee.vn/product/{shop_id}/{item_id}"
)

CASHBACK_STATUS_PENDING = "Pending"
CASHBACK_STATUS_APPROVED = "Approved"
CASHBACK_STATUS_COMPLETED = "Completed"
CASHBACK_STATUS_CANCELLED = "Cancelled"

CASHBACK_STATUSES = {
    CASHBACK_STATUS_PENDING,
    CASHBACK_STATUS_APPROVED,
    CASHBACK_STATUS_COMPLETED,
    CASHBACK_STATUS_CANCELLED,
}


# Shopee Checkout Statuses
SHOPEE_STATUS_PENDING = "Pending"
SHOPEE_STATUS_WAITING = "Waiting for payment"
SHOPEE_STATUS_COMPLETED = "Completed"
SHOPEE_STATUS_CANCELLED = "Cancelled"

SHOPEE_CHECKOUT_STATUSES = {
    SHOPEE_STATUS_PENDING: 0,
    SHOPEE_STATUS_WAITING: 1,
    SHOPEE_STATUS_COMPLETED: 2,
    SHOPEE_STATUS_CANCELLED: 3,
}

MICRO_UNIT_SCALE: float = 100000.0