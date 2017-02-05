#!/usr/bin/env python3

"""
pyvanza.py.
~~~~~~~~~~~

A module to fetch information from Avanza.se.

"""

import time
import websocket
import json
import logging

import bs4
import requests

import const
from decorators import auth_required
from exceptions import AuthError


class Avanza(object):

    DEBUG = True

    def __init__(self, username=None, password=None, headers=None, proxy=None):
        """Initialize an Avanza object"""
        self.session = requests.Session()
        self.headers = headers
        self.proxy = proxy
        self.username = username
        self.password = password
        self.id_ = 0

        if headers:
            self.session.headers.update(self.headers)
        else:
            self.session.headers.update(const.HEADERS)

        if proxy:
            self.session.proxies.update(self.proxy)

        if Avanza.DEBUG:
            logging.basicConfig(level=logging.DEBUG)

        if self.username and self.password:
            # self.connection = websocket.create_connection(const.SOCKET_URL)
            self.login()

    def login(self):
        """Log into the Avanza website."""
        form_data = {
            "j_username": self.username,
            "j_password": self.password
        }

        request = self.session.post(const.URL + "/ab/handlelogin",
                                    data=form_data)

        if request.status_code != requests.codes.ok:
            raise AuthError("Authentication failed with error code: "
                            "{}".format(request.status_code))

    def html(self, page):
        """Return the parsed HTML of a page."""
        request = self.session.get(const.URL + page, stream=True)

        return bs4.BeautifulSoup(request.content.decode("UTF-8"), "lxml")

    def scrape(self, page, selector):
        """Return the text of a HTML tag."""
        # Avanza returns status code 200 even if the information is not
        # available...
        try:
            return (self.html(page).find(class_=selector).get_text(
                    strip=True).replace("\xa0", ""))
        except AttributeError:
            return

    @auth_required
    def balance(self):
        """Get your accounts balance."""
        return self.scrape(const.HOMEPAGE, const.TOTAL_BALANCE)

    @auth_required
    def purchase_balance(self):
        """Get the amount of money available to make purchases with."""
        return self.scrape(const.HOMEPAGE, const.BUYING_POWER)

    @auth_required
    def total_value(self):
        """Get your accounts total value (balance + stocks)."""
        return self.scrape(const.HOMEPAGE, const.TOTAL_VALUE)

    @auth_required
    def growth(self):
        """Get your growth this year."""
        try:
            return self.scrape(const.HOMEPAGE, const.GROWTH_POS)
        except (AttributeError, KeyError):
            return self.scrape(const.HOMEPAGE, const.GROWTH_NEG)

    @auth_required
    def accounts(self):
        """Get all your Avanza accounts"""
        find_all_accounts = (self.html("/mina-sidor/min-profil/"
                                       "mina-konton.html").find_all(
                                       "a", class_="link "))

        return [account.text for account in find_all_accounts]

    @auth_required
    def account_info(self, account):
        """Get account info"""
        url = "/mina-sidor/kontooversikt.{}.html".format(account)

        try:
            growth = self.scrape(url, const.GROWTH_POS)
        except (AttributeError, KeyError):
            growth = self.scrape(url, const.GROWTH_NEG)

        return {
            account: {
                "Utveckling i år": growth,
                "Saldo": self.scrape(url, const.TOTAL_BALANCE),
                "Tillgänligt för köp": self.scrape(url, const.BUYING_POWER),
                "Totalt värde": self.scrape(url, const.TOTAL_VALUE)}
               }

    # TODO: needs improvement, possibly get titles + date
    def telegrams(self, limit=None):
        """Get all the telegrams from Avanza's Placera website."""
        get_links = (self.html("/placera/telegram.html").find_all(
                     "li", {"class": ["oddItem", "evenItem"]}))

        return [const.URL + link.a["href"] for link in get_links[:limit]]

    @property
    def token(self):
        """Get the token needed to establish a websocket connection"""
        page_src = self.html(const.HOMEPAGE).find("div", class_="loginWrapper")
        token = page_src["data-push_subscriptionid"]

        return token

    @property
    def client_id(self):
        """Get the client id needed to send data to the websocket"""
        handshake_data = json.dumps([
            {
                "advice": {
                    "timeout": 60000,
                    "interval": 0
                },
                "channel": "/meta/handshake",
                "ext": {
                    "subscriptionId": self.token
                },
                "id": self.id_,
                "minimumVersion": "1.0",
                "supportedConnectionTypes": ['websocket', 'long-polling',
                                             'callback-polling'],
                "version": "1.0"
            }
        ])

        data = self.socket_data(handshake_data)
        client_id = data[0]["clientId"]

        return client_id

    def connect_websocket(self):
        connect_data = json.dumps([
            {
                "id": self.id_,
                "channel": "/meta/connect",
                "connectionType": "websocket",
                "advice": {
                    "timeout": 0
                },
                "clientId": self.client_id}
        ])

        data = self.socket_data(connect_data)

        return data

    def socket_data(self, data_to_send):
        """Send data through the established websocket connection"""
        self.connection.send(data_to_send)
        response = self.connection.recv()

        return json.loads(response)

    @property
    def unix_timestamp(self):
        """Returns the current UNIX time, including the millis"""
        return int(round(time.time() * 1000))

    def search(self, term):
        """Search the Avanza website"""
        results = {}
        url = "/ab/sok/inline?query={}&_={}".format(term, self.unix_timestamp)
        page_src = self.html(url)
        result_page = page_src.find_all("a", class_="srchResLink")
        items = page_src.find_all("table", class_="noHighlight pad")
        items_css_class = ("tRight upperCase bold "
                           "XSText noPaddingRight bottomAlign")
        types = {
            "aktier": "stock",
            "optioner": "option",
            "terminer": "futures",
            "obligationer": "equity bond"}

        for result, item in zip(result_page, items):
            type_ = result["href"].split("/")[1]
            item_info = item.find("td", class_=items_css_class).find_next()
            last_updated = item_info["title"].split()[2]
            price = item_info.get_text(strip=True)
            name = result["title"]
            url_path = result["href"]
            orderbook_id = result["href"].split("/")[3]

            try:
                type_ = types[type_]
            except KeyError:
                type_ = None

            results[name] = {"type": type_,
                             "url": const.URL + url_path,
                             "id": orderbook_id,
                             "price": price,
                             "lastUpdated": last_updated}

        return results

# TODO: get purchased stocks
# TODO: get transactions
# TODO: allow `get_telegrams` to get more than one page (default: 1)

#  vim: set ts=4 sw=4 tw=80 et :
