"""
This file contains constants that are used throughout the avanza.py file

"""

__version__ = "0.01"

SOCKET_URL = "wss://www.avanza.se/_push/cometd"
URL = "https://avanza.se"
HOMEPAGE = "/mina-sidor/kontooversikt.html"

TOTAL_BALANCE = "totalBalance"
BUYING_POWER = "buyingPower"
TOTAL_VALUE = "totalValue"
GROWTH_POS = "SText fRight tRight bold positive"
GROWTH_NEG = "SText fRight tRight bold negative"

LATEST_PRICE = "pushBox roundCorners3"
HIGHEST_PRICE = "highestPrice SText bold"
LOWEST_PRICE = "lowestPrice SText bold"
TIME = "updated SText bold"

HEADERS = {
    "User-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/532.36 "
                  "(KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.37"
    }
#  vim: set ts=4 sw=4 tw=80 et :
