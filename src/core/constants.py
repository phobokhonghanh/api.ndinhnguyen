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
    "?origin_link=https://shopee.vn/product/{item_id}/{shop_id}"
    "&affiliate_id={affiliate_id}"
    "&sub_id={sub_id}"
    "&deep_and_deferred={deep_and_deferred}"
)
SHOPEE_REPORT_LIST_URL = "https://affiliate.shopee.vn/api/v3/report/list"
