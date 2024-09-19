from math import ceil
# import logging
from curl_cffi import requests


rootURL = "https://api.amiami.com/api/v1.0/items"
PER_PAGE = 30

# buy_flg
# : 
# 0
# buy_price
# : 
# 0
# buy_remarks
# : 
# null
# c_price_taxed
# : 
# 6050
# cate6
# : 
# null
# cate7
# : 
# null
# condition_flg
# : 
# 0
# element_id
# : 
# null
# for_women_flg
# : 
# 0
# gcode
# : 
# "GOODS-04428514"
# genre_moe
# : 
# 1
# gname
# : 
# "[Bonus] Touhou Plush Series 20 Koishi Komeiji FumoFumo Koishi."
# image_category
# : 
# "234/"
# image_name
# : 
# "GOODS-04428514"
# image_on
# : 
# 1
# instock_flg
# : 
# 1
# jancode
# : 
# "4580731042761"
# list_amiami_limited
# : 
# 0
# list_backorder_available
# : 
# 0
# list_preorder_available
# : 
# 0
# list_store_bonus
# : 
# 0
# maker_name
# : 
# "Gift"
# max_price
# : 
# 6050
# metaalt
# : 
# null
# min_price
# : 
# 6050
# order_closed_flg
# : 
# 0
# preorderitem
# : 
# 0
# preowned_sale_flg
# : 
# 0
# releasedate
# : 
# "2024-07-31 00:00:00"
# resale_flg
# : 
# 1
# saleitem
# : 
# 0
# salestatus
# : 
# null
# salestatus_detail
# : 
# null
# saletopitem
# : 
# 0
# stock_flg
# : 
# 1
# thumb_alt
# : 
# "GOODS-04428514.jpg"
# thumb_title
# : 
# "[Bonus] Touhou Plush Series 20 Koishi Komeiji FumoFumo Koishi."
# thumb_url
# : 
# "/images/product/main/234/GOODS-04428514.jpg"
class Item:
    def __init__(self, *args, **kwargs):
        self.productURL = kwargs['productURL']
        self.imageURL = kwargs['imageURL']
        self.productName = kwargs['productName']
        self.price = kwargs['price']
        self.productCode = kwargs['productCode']
        self.availability = kwargs['availability']
        self.flags = kwargs['flags']

class ResultSet:
    def __init__(self, keyword, proxies=None, **search_params):
        self.keyword = keyword
        self.proxies = proxies
        self.search_params = search_params
        self.items = []
        self.maxItems = -1
        self.init = False
        self.currentPage = 0
        self.pages = -1
        self._itemCount = 0

    # tostring, print out item count, current page, max items, hasMore
    def __str__(self):
        return "ResultSet: itemCount={}, currentPage={}, maxItems={}, hasMore={}".format(
            self._itemCount,
            self.currentPage,
            self.maxItems,
            self.hasMore,
        )

    @property
    def hasMore(self):
        return self._itemCount < self.maxItems

    # def getNextPage(self):
    #     if self.hasMore:
    #         self.currentPage += 1
    #         return search_page(self.keyword, self.currentPage, self.proxies)
    #     else:
    #         return None

    def searchNextPage(self):
        data = {
            "s_keywords": self.keyword,
            "pagecnt": self.currentPage + 1,
            "pagemax": PER_PAGE,
            "lang": "eng",
            **self.search_params  # Include additional search parameters
        }
        headers = {
            "X-User-Key": "amiami_dev",
            "User-Agent": "python-amiami_dev",
        }
        resp = requests.get(rootURL, params=data, headers=headers, impersonate="chrome110", proxies=self.proxies)
        self.__parse(resp.json())
        self.currentPage += 1


    def __add(self, productInfo):
       
        availability = "Unknown status?"
        isSale = productInfo['saleitem'] == 1
        isLimited = productInfo['list_store_bonus'] == 1 or productInfo['list_amiami_limited'] == 1
        isPreowned = productInfo['condition_flg'] == 1
        isPreorder = productInfo['preorderitem'] == 1
        isBackorder = productInfo['list_backorder_available'] == 1
        isClosed = productInfo['order_closed_flg'] == 1
        
        flags = {
            "isSale": isSale,
            "isLimited": isLimited,
            "isPreowned": isPreowned,
            "isPreorder": isPreorder,
            "isBackorder": isBackorder,
            "isClosed": isClosed,
        }
        if isClosed:
            if isPreorder:
                availability = "Pre-order Closed"
            elif isBackorder:
                availability = "Back-order Closed"
            else:
                availability = "Order Closed"
        else:
            if isPreorder:
                availability = "Pre-order"
            elif isBackorder:
                availability = "Back-order"
            elif isPreowned:
                availability = "Pre-owned"
            elif isLimited:
                availability = "Limited"
            elif isSale:
                availability = "On Sale"
            else:
                availability = "Available"

        if availability == "Unknown status?":
            print("STATUS ERROR FOR {}: flags:{}, avail:{}".format(
                productInfo['gcode'],
                flags,
                availability,
            ))
        item = Item(
            productURL="https://www.amiami.com/eng/detail/?gcode={}".format(productInfo['gcode']),
            imageURL="https://img.amiami.com{}".format(productInfo['thumb_url']),
            productName=productInfo['gname'],
            price=productInfo['c_price_taxed'],
            productCode=productInfo['gcode'],
            availability=availability,
            flags=flags,
        )
        self.items.append(item)

    def __parse(self, obj):
        # returns true when done
        # false if can be called again
        if not self.init:
            self.maxItems = obj['search_result']['total_results']
            self.pages = int(ceil(self.maxItems / float(PER_PAGE)))
            self.init = True
        for productInfo in obj['items']:
            self.__add(productInfo)
            self._itemCount += 1

        return self._itemCount == self.maxItems

# leaving this here because I need it every time some shit breaks and don't wanna dig it up
# logging.basicConfig(
#     format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     level=logging.DEBUG
# )

def search(keywords, proxies=None, **search_params):
    rs = searchPaginated(keywords=keywords, proxies=proxies, **search_params)

    while rs.hasMore:
        rs.searchNextPage()

    return rs

def searchPaginated(keywords, proxies=None, **search_params):
    rs = ResultSet(keyword=keywords, proxies=proxies, **search_params)
    rs.searchNextPage()

    return rs