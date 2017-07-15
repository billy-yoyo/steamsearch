"""
MIT License

Copyright (c) 2016-2017 billyoyo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import asyncio
import aiohttp
import operator
import json
import math
import re
from urllib import parse
from bs4 import BeautifulSoup

# used to map currency symbols to currency codes
CURRENCY_MAP = {
    "lek": "ALL",
    "$": "USD",
    "ман": "AZN",
    "p.": "BYR",
    "BZ$": "BZD",
    "$b": "BOB",
    "KM": "BAM",
    "P": "BWP",
    "лв": "BGN",
    "R$": "BRL",
    "¥": "JPY",
    "₡": "CRC",
    "kn": "HRK",
    "₱": "CUP",
    "Kč": "CZK",
    "kr": "DKK",
    "RD$": "DOP",
    "£": "GBP",
    "€": "EUR",
    "¢": "GHS",
    "Q": "GTQ",
    "L": "HNL",
    "Ft": "HUF",
    "Rp": "IDR",
    "₪": "ILS",
    "J$": "JMD",
    "₩": "KRW",
    "₭": "LAK",
    "ден": "MKD",
    "RM": "MYR",
    "Rs": "MUR",
    "руб": "RUB"
}

# list of country codes
COUNTRY_CODES = ['af','ax','al','dz','as','ad','ao','ai','aq','ag','ar','am','aw','au','at','az','bs','bh','bd','bb',
                 'by','be','bz','bj','bm','bt','bo','ba','bw','bv','br','io','bn','bg','bf','bi','kh','cm','ca','cv',
                 'ky','cf','td','cl','cn','cx','cc','co','km','cg','cd','ck','cr','ci','hr','cu','cy','cz','dk','dj',
                 'dm','do','ec','eg','sv','gq','er','ee','et','fk','fo','fj','fi','fr','gf','pf','tf','ga','gm','ge',
                 'de','gh','gi','gr','gl','gd','gp','gu','gt','gg','gn','gw','gy','ht','hm','va','hn','hk','hu','is',
                 'in','id','ir','iq','ie','im','il','it','jm','jp','je','jo','kz','ke','ki','kp','kr','kw','kg','la',
                 'lv','lb','ls','lr','ly','li','lt','lu','mo','mk','mg','mw','my','mv','ml','mt','mh','mq','mr','mu',
                 'yt','mx','fm','md','mc','mn','ms','ma','mz','mm','na','nr','np','nl','an','nc','nz','ni','ne','ng',
                 'nu','nf','mp','no','om','pk','pw','ps','pa','pg','py','pe','ph','pn','pl','pt','pr','qa','re','ro',
                 'ru','rw','an','da','rw','sh','kn','lc','pm','vc','ws','sm','st','sa','sn','cs','sc','sl','sg','sk',
                 'si','sb','so','za','gs','es','lk','sd','sr','sj','sz','se','ch','sy','tw','tj','tz','th','tl','tg',
                 'tk','to','tt','tn','tr','tm','tc','tv','ug','ua','ae','gb','us','um','uy','uz','vu','ve','vn','vg',
                 'vi','wf','eh','ye','zm','zw']

# list of currencies I can convert to
VALID_CURRENCIES = ['AED', 'AFN', 'ALL', 'AMD', 'ANG', 'AOA', 'ARS', 'AUD', 'AWG', 'AZN', 'BAM', 'BBD', 'BDT', 'BGN',
                    'BHD', 'BIF', 'BMD', 'BND', 'BOB', 'BRL', 'BSD', 'BTC', 'BTN', 'BWP', 'BYN', 'BYR', 'BZD', 'CAD',
                    'CDF', 'CHF', 'CLF', 'CLP', 'CNY', 'COP', 'CRC', 'CUC', 'CUP', 'CVE', 'CZK', 'DJF', 'DKK', 'DOP',
                    'DZD', 'EEK', 'EGP', 'ERN', 'ETB', 'EUR', 'FJD', 'FKP', 'GBP', 'GEL', 'GGP', 'GHS', 'GIP', 'GMD',
                    'GNF', 'GTQ', 'GYD', 'HKD', 'HNL', 'HRK', 'HTG', 'HUF', 'IDR', 'ILS', 'IMP', 'INR', 'IQD', 'IRR',
                    'ISK', 'JEP', 'JMD', 'JOD', 'JPY', 'KES', 'KGS', 'KHR', 'KMF', 'KPW', 'KRW', 'KWD', 'KYD', 'KZT',
                    'LAK', 'LBP', 'LKR', 'LRD', 'LSL', 'LTL', 'LVL', 'LYD', 'MAD', 'MDL', 'MGA', 'MKD', 'MMK', 'MNT',
                    'MOP', 'MRO', 'MTL', 'MUR', 'MVR', 'MWK', 'MXN', 'MYR', 'MZN', 'NAD', 'NGN', 'NIO', 'NOK', 'NPR',
                    'NZD', 'OMR', 'PAB', 'PEN', 'PGK', 'PHP', 'PKR', 'PLN', 'PYG', 'QAR', 'RON', 'RSD', 'RUB', 'RWF',
                    'SAR', 'SBD', 'SCR', 'SDG', 'SEK', 'SGD', 'SHP', 'SLL', 'SOS', 'SRD', 'STD', 'SVC', 'SYP', 'SZL',
                    'THB', 'TJS', 'TMT', 'TND', 'TOP', 'TRY', 'TTD', 'TWD', 'TZS', 'UAH', 'UGX', 'USD', 'UYU', 'UZS',
                    'VEF', 'VND', 'VUV', 'WST', 'XAF', 'XAG', 'XAU', 'XCD', 'XDR', 'XOF', 'XPD', 'XPF', 'XPT', 'YER',
                    'ZAR', 'ZMK', 'ZMW', 'BCN', 'BTS', 'DASH', 'DOGE', 'EAC', 'EMC', 'ETH', 'FCT', 'FTC', 'LD', 'LTC',
                    'NMC', 'NVC', 'NXT', 'PPC', 'STR', 'VTC', 'XCP', 'XEM', 'XMR', 'XPM', 'XRP', 'VEF_BLKMKT',
                    'VEF_SIMADI']

STEAM_KEY = ""  # contains your Steam API key (set using set_key)
STEAM_CACHE = True  # whether or not steamsearch should cache some results which generally aren't going to change
STEAM_SESSION = ""  # your Steam Session for SteamCommunityAjax
STEAM_PRINTING = False  # whether or not steamsearch will occasionally print warnings


def set_key(key, session, cache=True, printing=False):
    """Used to initiate your key + session strings, also to enable/disable caching

    Args:
        key (str): Your Steam API key
        session (str): Your SteamCommunityAjax session, this basically just needs to be any string containing only a-z, A-Z or 0-9
        cache (bool, optional): True to enable caching
    """
    global STEAM_KEY, STEAM_CACHE, STEAM_SESSION, STEAM_PRINTING
    STEAM_KEY = key
    STEAM_SESSION = session
    STEAM_CACHE = cache
    STEAM_PRINTING = printing


def count_cache():
    """Counts the amount of cached results

    Returns:
        the number of cached results (int)
    """
    return len(gameid_cache) + len(item_name_cache) + len(userid_cache)


def clear_cache():
    """Clears all of the cached results

    Returns:
        the number of results cleared
    """
    global gameid_cache, item_name_cache, userid_cache
    items = count_cache()
    gameid_cache = {}
    item_name_cache = {}
    userid_cache = {}
    return items


class SteamKeyNotSet(Exception):
    """Exception raised if STEAM_KEY is used before it was set"""
    pass


class SteamSessionNotSet(Exception):
    """Exception raised if STEAM_SESSION is used before it was set"""
    pass


def _check_key_set():
    """Internal method to ensure STEAM_KEY has been set before attempting to use it"""
    if not isinstance(STEAM_KEY, str) or STEAM_KEY == "":
        raise SteamKeyNotSet


def _check_session_set():
    """Internal method to ensure STEAM_SESSION has been set before attempting to use it"""
    if not isinstance(STEAM_KEY, str) or STEAM_SESSION == "":
        raise SteamSessionNotSet

@asyncio.coroutine
def exchange(amount, from_curr, to_curr, timeout=10):
    """Converts an amount of money from one currency to another

    Args:
        amount (float): The amount of money you want to convert
        from_curr (str): The currency you want to convert from,
            either country symbol (e.g USD) or currency smybol (e.g. £)
        to_curr (str): The currency you want to convert to, same format as from_curr
        timeout (int, optional): The time in seconds aiohttp will take to timeout the request
    Returns:
        float: the converted amount of money to 2 d.p., or the original amount of the conversion failed.
    """
    try:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://api.fixer.io/latest?symbols=" + from_curr + "," + to_curr)
                data = yield from resp.json()
                if "rates" in data:
                    return int((amount / data["rates"][from_curr]) * data["rates"][to_curr] * 100)/100
    except:
        return amount


def is_integer(x):
    try:
        int(x)
        return True
    except:
        return False


# link, id, image, title, released, review, reviewLong, discount, price, discountPrice,
class GamePageResult:
    def __init__(self, link, id, soup):
        self.title = "???"
        titlesoup = soup.find("div", {"class": "apphub_AppName"})
        if titlesoup is not None:
            self.title = titlesoup.get_text()

        self.link = link
        self.id = id

        imgsoup = soup.find("img", {"class": "game_header_image_full"})
        self.image = "???"
        if imgsoup is not None:
            self.image = imgsoup.get("src")

        self.released = "???"
        releasesoup = soup.find("div", {"class": "release_date"})
        if releasesoup is not None:
            releasesoup = soup.find("span", {"class": "date"})
            if releasesoup is not None:
                self.released = releasesoup.get_text()

        self.review = "???"
        reviewsoup = soup.find("span", {"class": "game_review_summary"})
        if reviewsoup is not None:
            self.review = reviewsoup.get_text().replace("\n", "").replace("\r", "").replace("\t", "").replace("(", "").replace(")", "").replace("-", "").strip()

        self.reviewLong = "???"
        reviewsoup = soup.find_all("span", {"class": "responsive_reviewdesc"})
        if reviewsoup is not None and len(reviewsoup) >= 2:
            self.reviewLong = reviewsoup[1].get_text().replace("\n", "").replace("\r", "").replace("\t", "").replace("(", "").replace(")", "").replace("-", "").strip()

        self.discount = ""
        discountsoup = soup.find("div", {"class": "discount_pct"})
        if discountsoup is not None:
            self.discount = discountsoup.get_text().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "").replace("(", "").replace(")", "")

        if self.discount == "":
            self.price = "???"
            self.discountPrice = "???"
            pricesoup = soup.find("div", {"class": "game_purchase_price"})
            if pricesoup is not None:
                self.price = pricesoup.get_text().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "").replace("(", "").replace(")", "").replace("-", "")
        else:
            self.price = "???"
            self.discountPrice = "???"
            pricesoup = soup.find("div", {"class": "discount_original_price"})
            if pricesoup is not None:
                self.price = pricesoup.get_text().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "").replace("(", "").replace(")", "").replace("-", "")

            pricesoup = soup.find("div", {"class": "discount_final_price"})
            if pricesoup is not None:
                self.discountPrice = pricesoup.get_text().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "").replace("(", "").replace(")", "").replace("-", "")

    @asyncio.coroutine
    def update_price(self, currency, currency_symbol):
        """Attempts to convert the price to GBP

        Args:
            currency (str): The currency code (e.g USD or GBP) to convert the price to
            currency_symbol (str): The currency symbol to add to the start of the price
            """
        if currency != "GBP":
            try:
                if self.price != "???" and self.price != "" and self.price != "Free to Play":
                    rawprice = yield from exchange(float(self.price[1:]), "GBP", currency)
                    self.price = currency_symbol + str(rawprice)
            except:
                if STEAM_PRINTING:
                    print("failed to convert currency (GBP)")

    def __str__(self):
        return self.title

class GameResult:
    """Class containing information about a game search result"""
    def __init__(self, soup):
        """

        Args:
            soup (BeautifulSoup): soup from game search page
        """
        self.link = soup.get("href")
        linkspl = self.link.split("/")
        self.link = "/".join(linkspl[:5])
        self.id = linkspl[4]


        self.image = None #"http://cdn.edgecast.steamstatic.com/steam/apps/%s/capsule_184x69.jpg" % self.id
        imgsoup = soup.find("img")
        if imgsoup is not None:
            self.image = imgsoup.get("src")

        self.title = "???"
        titlesoup = soup.find("span", {"class": "title"})
        if titlesoup is not None:
            self.title = titlesoup.get_text()

        self.released = "???"
        releasesoup = soup.find("div", {"class": "col search_released responsive_secondrow"})
        if releasesoup is not None:
            self.released = releasesoup.get_text()

        self.review = "???"
        self.reviewLong = "???"
        reviewsoup = soup.findAll("span")
        for span in reviewsoup:
            cls = span.get("class")
            if cls is not None and "search_review_summary" in cls:
                reviewRaw = span.get("data-store-tooltip").split("<br>")
                self.review = reviewRaw[0]
                self.reviewLong = reviewRaw[1]
                break

        self.discount = ""
        discountsoup = soup.find("div", {"class": "col search_discount responsive_secondrow"})
        if discountsoup is not None:
            span = discountsoup.find("span")
            if span is not None:
                self.discount = span.get_text().replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

        self.price = "???"
        self.discountPrice = "???"

        if self.discount == "":
            pricesoup = soup.find("div", {"class": "col search_price responsive_secondrow"})
            self.price = pricesoup.get_text().replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "")
        else:
            pricesoup = soup.find("div", {"class": "col search_price discounted responsive_secondrow"})
            span = pricesoup.find("span")
            if span is not None:
                self.price = span.get_text().replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "").replace("<strike>", "").replace("</strike>", "")
            self.discountPrice = pricesoup.get_text().replace(" ", "").replace("\n", "").replace("\t", "").replace("\r", "").replace(self.price, "")

        if self.price.lower() == "freetoplay":
            self.price = "Free to Play"

    #def set_image_size(self, width, height):
    #    if self.image is not None:
    #        self.image = re.sub("width=[0-9]+", "width=%s" % width, self.image)
    #        self.image = re.sub("height=[0-9]+", "height=%s" % height, self.image)

    def get_price_text(self):
        if self.discount == "":
            return self.price
        else:
            return self.discountPrice + " (" + self.discount + ")"

    @asyncio.coroutine
    def update_price(self, currency, currency_symbol):
        """Attempts to convert the price to GBP

        Args:
            currency (str): The currency code (e.g USD or GBP) to convert the price to
            currency_symbol (str): The currency symbol to add to the start of the price
            """
        if currency != "GBP":
            try:
                if self.price != "???" and self.price != "" and self.price != "Free to Play":
                    rawprice = yield from exchange(float(self.price[1:]), "GBP", currency)
                    self.price = currency_symbol + str(rawprice)
            except:
                if STEAM_PRINTING:
                    print("failed to convert currency (GBP)")

    def __str__(self):
        return self.title



class CategoryResult:
    def __init__(self, soup):

        self.link = "/".join(soup.get("href").split("/")[:-1]) or "???"
        self.id = soup.get("data-ds-appid") or "???"

        name_soup = soup.find("span", {"class": "title"})
        self.title = name_soup.get_text() if name_soup is not None else "???"

        img_soup = soup.find("img")
        self.img = img_soup.get("src") if img_soup is not None else "???"
        self.img = self.img or "???"

        discount_soup = soup.find("div", {"class": "search_discount"})
        self.discount = discount_soup.get_text().strip() if discount_soup is not None else "???"

        price_soup = soup.find("div", {"class": "search_price"})
        if price_soup is not None:
            price_text_raw = "".join([x for x in price_soup.get_text().split() if x != ""])

            discount_price_soup = price_soup.find("span")
            if discount_price_soup is not None:
                self.price = discount_price_soup.get_text().strip()
                self.discount_price = price_text_raw.replace(self.price, "")
            else:
                self.price = price_text_raw
                self.discount_price = "???"
        else:
            self.price = "???"

        if self.price.replace(" ", "").lower() == "freetoplay":
            self.price = "free to play"
        elif self.price == "":
            self.price = "???"

    def get_price_text(self):
        if self.discount == "???":
            return self.price
        elif self.discount == "":
            return self.price
        else:
            return self.discount_price + " (" + self.discount + ")"


class NewCategoryResult:
    def __init__(self, soup):
        self.link = "/".join(soup.get("href").split("/")[:-1]) or "???"
        self.id = soup.get("data-ds-appid") or "???"

        name_soup = soup.find("div", {"class": "tab_item_name"})
        self.title = "???"
        if name_soup is not None:
            self.title = name_soup.get_text()

        img_soup = soup.find("img")
        self.img = "???"
        if img_soup is not None:
            self.img = img_soup.get("src") or "???"

        self.discount = "???"
        self.price = "???"
        self.discount_price = "???"

        pricesoup = soup.find("div", {"class": "discount_block"})
        if pricesoup is not None:
            discount = pricesoup.find("div", {"class": "discount_pct"})
            if discount is not None:
                self.discount = discount.get_text()
            dpsoup = pricesoup.find("div", {"class": "discount_prices"})
            if dpsoup is not None:
                if self.discount == "???":
                    price = dpsoup.find("div", {"class": "discount_final_price"})
                    self.price = price.get_text()
                else:
                    price = dpsoup.find("div", {"class": "discount_original_price"})
                    self.price = price.get_text()
                    discountprice = dpsoup.find("div", {"class": "discount_final_price"})
                    self.discount_price = discountprice.get_text()

        if self.price.lower() == "freetoplay":
            self.price = "Free to Play"

    def get_price_text(self):
        if self.discount == "???":
            return self.price
        elif self.discount == "":
            return self.price
        else:
            return self.discount_price + " (" + self.discount + ")"


class TopResult:
    """Class containing information about the games on the front of the store (new releases, specials etc.)"""
    def __init__(self, soup):
        """

        Args:
            soup (BeautifulSoup): Soup for the section of the store page containing the game information
        """
        self.link = "???"

        linksoup = soup.find("a", {"class": "tab_item_overlay"})
        if linksoup is not None:
            self.link = linksoup.get("href")
            if self.link is None:
                self.link = "???"

        self.image = "???"
        imagesoup = soup.find("div", {"class": "tab_item_cap"})
        if imagesoup is not None:
            img = imagesoup.get("img")
            if img is not None:
                self.image = img.get("src")

        self.discount = ""
        self.price = ""
        self.discountPrice = "???"

        pricesoup = soup.find("div", {"class": "discount_block"})
        if pricesoup is not None:
            discount = pricesoup.find("div", {"class": "discount_pct"})
            if discount is not None:
                self.discount = discount.get_text()
            dpsoup = pricesoup.find("div", {"class": "discount_prices"})
            if dpsoup is not None:
                if self.discount == "":
                    price = dpsoup.find("div", {"class": "discount_final_price"})
                    self.price = price.get_text()
                else:
                    price = dpsoup.find("div", {"class": "discount_original_price"})
                    self.price = price.get_text()
                    discountprice = dpsoup.find("div", {"class": "discount_final_price"})
                    self.discountPrice = discountprice.get_text()

        if self.price.lower() == "freetoplay":
            self.price = "Free to Play"

        titlesoup = soup.find("div", {"class": "tab_item_content"})
        if titlesoup is not None:
            title = soup.find("div", {"class": "tab_item_name"})
            self.title = title.get_text()

        self.review = "???"
        self.reviewLong = "???"
        self.released = "???"

    def get_price_text(self):
        if self.discount == "":
            return self.price
        else:
            return self.discountPrice + " (" + self.discount + ")"

    @asyncio.coroutine
    def update_price(self, currency, currency_symbol):
        """Attempts to convert the price to GBP

        Args:
            currency (str): The currency code (e.g USD or GBP) to convert the price to
            currency_symbol (str): The currency symbol to add to the start of the price
            """
        if currency != "GBP":
            try:
                if self.price != "???" and self.price != "" and self.price != "Free to Play":
                    rawprice = yield from exchange(float(self.price[1:]), "GBP", currency)
                    self.price = currency_symbol + str(rawprice)

                if self.discountPrice != "???" and self.price != "":
                    rawdiscountprice = yield from exchange(float(self.discountPrice[1:]), "GBP", currency)
                    self.discountPrice = currency_symbol + str(rawdiscountprice)
            except:
                if STEAM_PRINTING:
                    print("failed to convert currency (GBP)")

    def __str__(self):
        return self.title


class SteamSaleResult(TopResult):
    def __init__(self, soup):
        self.link = "/".join(soup.get("href").split("/")[:-1])
        self.id = soup.get("data-ds-appid")

        self.image = "???"
        imagesoup = soup.find("img", {"class": "sale_capsule_image"})
        if imagesoup is not None:
            self.image = imagesoup.get("src")

        self.discount = ""
        self.price = ""
        self.discountPrice = "???"

        pricesoup = soup.find("div", {"class": "discount_block"})
        if pricesoup is not None:
            discount = pricesoup.find("div", {"class": "discount_pct"})
            if discount is not None:
                self.discount = discount.get_text()
            dpsoup = pricesoup.find("div", {"class": "discount_prices"})
            if dpsoup is not None:
                if self.discount == "":
                    price = dpsoup.find("div", {"class": "discount_final_price"})
                    self.price = price.get_text()
                else:
                    price = dpsoup.find("div", {"class": "discount_original_price"})
                    self.price = price.get_text()
                    discountprice = dpsoup.find("div", {"class": "discount_final_price"})
                    self.discountPrice = discountprice.get_text()

        if self.price.lower() == "freetoplay":
            self.price = "Free to Play"

        self.title = "???"

        self.review = "???"
        self.reviewLong = "???"
        self.released = "???"

    @asyncio.coroutine
    def get_title(self, cc="gb", timeout=10):
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://store.steampowered.com/api/appdetails/?appids=" + self.id)
                data = yield from resp.json()

                self.title = parse.unquote(data[self.id]["data"]["name"])

class UserResult:
    """Class containing information about a specific user"""
    def __init__(self, data):
        """

        Args:
            data (dict): part of the JSON returned by the Steam API
        """
        self.id = data.get("steamid", "???")
        self.name = data.get("personaname", "???")
        self.visibilityState = str(data.get("communityvisibilitystate", "???"))
        self.profileStage = str(data.get("profilestate", "???"))
        self.lastLogoff = str(data.get("lastlogoff", "???"))
        self.url = data.get("profileurl", "???")
        self.avatar = data.get("avatar", "???")
        self.avatarMedium = data.get("avatarmedium", "???")
        self.avatarFull = data.get("avatarfull", "???")
        self.personaState = data.get("personastate", "???")
        self.realName = data.get("realname", "???")
        self.clan = data.get("primaryclanid", "???")
        self.created = str(data.get("timecreated", "???"))
        self.country = data.get("loccountrycode", "???")


class UserGame:
    """Class containing information about user's playtime on a specific game"""
    def __init__(self, data):
        """

        Args:
            data (dict): part of the JSON returned by the Steam API
        """
        self.id = str(data.get("appid", "???"))
        self.name = data.get("name", "???")
        self.playtime_2weeks = str(data.get("playtime_2weeks", "???"))  #  IN MINUTES
        self.playtime_forever = str(data.get("playtime_forever", "???"))  #  IN MINUTES
        self.playtime_forever_int = 0
        if self.playtime_forever != "???":
            self.playtime_forever_int = int(self.playtime_forever)
        self.icon = data.get("img_icon_url", "???")
        self.logo = data.get("img_logo_url", "???")


    def format_playtime(self, playtime):
        """Formats the playtime in to hours

        Args:
            playtime (str | int): must be something representing an integer, playtime in minutes
        Returns:
            str: the formatted playtime in to Hours to 2 d.p.
        """
        if playtime != "???":
            return str(int(int(playtime) / 6)/10)
        else:
            return playtime

    def get_playtime_string(self, start="%s hours on record", end=" (%s hours in the last 2 weeks)"):
        """Converts the object to single line format

        Returns:
            A string representing this object
        """
        if self.playtime_2weeks != "???":
            start += end
            return start % (self.format_playtime(self.playtime_forever), self.format_playtime(self.playtime_2weeks))
        else:
            return start % self.format_playtime(self.playtime_forever)


class UserLibrary:
    """Class containing information about a set of games in the users library"""
    def __init__(self, data):
        self.count = data.get("game_count", "???")
        self.games = {}
        for game in data.get("games", []):
            ugame = UserGame(game)
            self.games[ugame.id] = ugame

    def get_game_list(self, limit=10, start="%s hours on record", end=" (%s hours in the last 2 weeks)"):
        """Converts the game list to a list of singe line formatted strings

        Args:
            limit (int): how many of the games to get, in decreasing order of total playtime
        Returns:
            a list of strings representing the user's most played games
            """
        results = sorted(self.games.values(), key=operator.attrgetter('playtime_forever_int'))[-1:-(limit+1):-1]
        pairs = [("", "")] * len(results)
        longest_name = 0
        for i, result in enumerate(results):
            pairs[i] = (result.name, result.get_playtime_string(start=start, end=end))
            if len(result.name) > longest_name:
                longest_name = len(result.name)
        final = [""] * len(results)
        longest_name += 3
        max_i_len = len(str(len(pairs)))
        for i, pair in enumerate(pairs):
            final[i] = " " * (max_i_len - len(str(i+1))) + str(i+1) + ". " + pair[0] + " " * (longest_name - len(pair[0])) + pair[1]
        return final


class UserAchievement:
    """Class containing information about a user's specific achievement for a specific game"""
    def __init__(self, data):
        """

        Args:
            data is part of the JSON returned by the Steam API
        """
        self.apiname = data.get("apiname", "???")
        self.displayname = self.apiname
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self.displayname = self.displayname.replace(letter, " " + letter)
        if self.displayname[0] == " ":
            self.displayname = self.displayname[1:]
        self.achieved = bool(data.get("achieved", False))
        self.name = data.get("name", "???")
        self.description = data.get("description", "???")


        #self.id = "???"

    def line_format(self):
        """Format the achievement in to a single line"""
        return ("✅" if self.achieved else "❎") + " " + (self.name if self.name != "???" else self.apiname)


class UserAchievements:
    """Class containing information about a user's achievements for a specific game"""
    def __init__(self, gameid, gamename, data):
        """

        Args:
            gameid (str): the appid of the game these achievements are for
            gamename (str): the gamename of the game these achievements are for
            data (dict): part of the JSON returned by the Steam API
        """
        self.gameid = gameid
        self.game = gamename
        self.achievements = sorted([UserAchievement(x) for x in data], key=operator.attrgetter("apiname"))

    def get(self, name):
        """Get an achievement matching 'name'

        Args:
            name (str): the name of the achievement you want to find, NOT FUZZY
        Returns:
            UserAchievement: the user achievement found, None if no achievement with that name found
            """
        name = name.lower().replace(" ", "").replace("-", "")
        for achiev in self.achievements:
            if achiev.apiname.lower() == name:
                return achiev
        return None

    def lines_format(self):
        """Return a list of all the achievements in line order

        Returns:
            list[str]: a list of the line formats"""
        return [x.line_format() for x in self.achievements]


class GlobalAchievement:
    """Class containing information about a specific achievement for a specific game"""
    def __init__(self, soup):
        """

        Args:
            soup (BeautifulSoup): part of the soup found on the achievements page
        """
        textSoup = soup.find("div", {"class": "achieveTxt"})
        if textSoup is not None:
            name = textSoup.find("h3")
            desc = textSoup.find("h5")

            if name is not None:
                self.name = name.get_text()
            else:
                self.name = "???"

            if desc is not None:
                self.desc = desc.get_text()
            else:
                self.desc = "???"
        else:
            self.name = "???"
            self.desc = "???"

        self.apiname = self.name.replace(" ", "").replace("-", "")
        percentSoup = soup.find("div", {"class": "achievePercent"})
        if percentSoup is not None:
            self.percent = percentSoup.get_text()
        else:
            self.percent = "??%"

        imgSoup = soup.find("div", {"class": "achieveImgHolder"})
        if imgSoup is not None:
            imgSoup = imgSoup.find("img")
            if imgSoup is not None:
                self.img = imgSoup.get("src")
            else:
                self.img = "???"
        else:
            self.img = "???"


class GlobalAchievements:
    """Contains information about all the achievements for a specific game"""
    def __init__(self, soup):
        """

        Args:
            soup (BeautifulSoup): part of the soup found on the achievements page
        """
        rows = soup.find_all("div", {"class": "achieveRow"})
        self.achievements = sorted([GlobalAchievement(x) for x in rows], key=operator.attrgetter("apiname"))

    def get(self, name):
        """Get an achievement matching 'name'

        Args:
            name (str): the name of the achievement you want to find, NOT FUZZY
        Returns:
            GlobalAchievement: the user achievement found, None if no achievement with that name found
            """
        name = name.lower()
        for achiev in self.achievements:
            if achiev.apiname.lower() == name:
                return achiev
        return None


class UserWishlistGame:
    def __init__(self, game):
        self.name = game[0]
        self.link = game[1]
        self.price = game[2]

        self.discount_price = None
        self.discount_percent = None

        if len(game) > 3:
            self.discount_price = game[3]
            self.discount_percent = game[4]


class UserWishlist:
    def __init__(self, games):
        self.games = [UserWishlistGame(game) for game in games]


class SteamGame:

    def __init__(self, **data):
        self.id = data.pop("id", "???")
        self.title = data.pop("name", "???")
        self.type = data.pop("type", "???")
        self.headline = data.pop("headline", "???")

        self.small_image = data.pop("small_capsule_image", "???")
        self.large_image = data.pop("large_capsule_image", "???")
        self.header_image = data.pop("header_image", "???")

        self.linux = data.pop("linux_available", False)
        self.mac = data.pop("mac_available", False)
        self.windows = data.pop("windows_available", False)
        self.controller = data.pop("controller_support", False)
        self.streaming_video = data.pop("streamingvideo_available", False)

        self.discounted = data.pop("discounted", False)
        self.original_price = data.pop("original_price", 0)
        self.price = data.pop("final_price", 0)
        self.discount_expiration = data.pop("discount_expiration", "???")
        self.discount_percent = data.pop("discount_percent", 0)
        self.currency = data.pop("currency", "???")


    def get_price_text(self):
        if self.discounted:
            return str(self.price/100)
        else:
            return str(self.price/100) + " (-" + str(self.discount_percent) + "%)"


class ItemResult:
    """Class containing information about an item on the steam market"""
    def __init__(self, soup):
        """

        Args:
            soup (BeautifulSoup): the soup of the item's store page
        """
        price = soup.find("span", {"class": "market_listing_price_with_publisher_fee_only"})
        self.price = "???"
        self.game = "???"
        if price is not None:
            rawprice = price.get_text().replace("\n", "").replace("\t", "").replace("\r", "")
            before = ""
            after = ""
            while len(rawprice) > 0 and rawprice[0] not in "0123456789.,":
                before += rawprice[0]
                rawprice = rawprice[1:]
            while len(rawprice) > 0 and rawprice[-1] not in "0123456789.,":
                after = rawprice[-1] + after
                rawprice = rawprice[:-1]
            before = before.replace(" ", "")
            after = after.replace(" ", "")

            currency = after
            if before in CURRENCY_MAP:
                currency = CURRENCY_MAP[before]
            elif after in CURRENCY_MAP:
                currency = CURRENCY_MAP[after]
            elif STEAM_PRINTING:
                print("no currency matching `" + before + "` or `" + after + "`")

            self.price = rawprice
            self.currency = currency
        elif STEAM_PRINTING:
            print("failed to find price")

        text = str(soup)
        self.icon = "???"
        iconindex = text.find('"icon_url":')
        if iconindex > 0:
            iconurl = text[iconindex+len('"icon_url":'):text.find(',', iconindex)].replace(" ", "").replace('"', "")
            self.icon = "http://steamcommunity-a.akamaihd.net/economy/image/" + iconurl
        elif STEAM_PRINTING:
            print("failed to find icon")

        index = text.find("var g_rgAssets")
        nindex = text.find("\n", index)
        jsontext = text[index:nindex]
        while jsontext[0] != "{" and jsontext[0] != "[":
            jsontext = jsontext[1:]
        while jsontext[-1] != "}" and jsontext[-1] != "]":
            jsontext = jsontext[:-1]


        try:
            data = json.loads(jsontext)
            raw = {}
            for k1 in data:
                for k2 in data[k1]:
                    for k3 in data[k1][k2]:
                        if "tradable" in data[k1][k2][k3] and data[k1][k2][k3]["tradable"] == 1:
                            raw = data[k1][k2][k3]
                            break

            self.actions = raw.get("actions", [])
            self.name = raw.get("name", "???")
            self.gameIcon = raw.get("app_icon", "???")
            self.icon = "http://steamcommunity-a.akamaihd.net/economy/image/" + raw.get("icon_url", "???")
            self.type = raw.get("type", "???")
            self.desc = [BeautifulSoup(x.get("value", ""), "html.parser").get_text() for x in raw.get("descriptions", [])]
        except:
            self.actions = []
            self.name = "???"
            self.gameIcon = "???"
            self.icon_url = "???"
            self.type = "???"
            self.desc = ""
            if STEAM_PRINTING:
                print("failed to load market data")

    @asyncio.coroutine
    def update_price(self, currency, currency_symbol):
        """Attempts to convert the price to GBP

        Args:
            currency (str): The currency code (e.g USD or GBP) to convert the price to
            currency_symbol (str): The currency symbol to add to the start of the price
            """
        try:
            rawprice = yield from exchange(float(self.price.replace(",", ".")), self.currency, currency)
            self.price = currency_symbol + str(rawprice)
        except:
            if STEAM_PRINTING:
                print("failed to convert currency (" + self.currency + ")")


@asyncio.coroutine
def check_game_sales(checks, old, optional_test=None, timeout=120):
    """

    :param checks: a list of tuples (gameid, percent, cc, other)
    :param old: a dict of games found last time {gameid: percent}
    :return: a list of tuples (gameid, check_percent, old_percent, price_overview, name, other)
    """
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            cached = optional_test or {}
            print("useing optional test: %s" % cached)
            results, new_old = [], {}

            print("using checks: %s" % str(checks))

            for check in checks:
                try:
                    if check[0] not in cached:
                        resp = yield from session.get("http://store.steampowered.com/api/appdetails/?appids=" + check[0] + "&cc=" + check[2])
                        json = yield from resp.json()

                        if not isinstance(json, dict):
                            print("failed to find percent for %s" % check[0])
                            continue

                        if json[check[0]]["success"]:
                            if "price_overview" not in json[check[0]]["data"]:
                                cached[check[0]] = None
                                continue
                            price_overview = json[check[0]]["data"]["price_overview"]
                            cached[check[0]] = (price_overview, json[check[0]]["data"]["name"])
                        else:
                            cached[check[0]] = None

                        resp.close()

                    if cached[check[0]] is not None:
                        result = cached[check[0]]
                        old_percent = float(old.get(check[0], 0))
                        if (result[0]["discount_percent"] < old_percent and old_percent >= float(check[1])) or (result[0]["discount_percent"] >= float(check[1]) and result[0]["discount_percent"] != old_percent):
                            results.append([check[0], float(check[1]), old_percent, result[0], result[1]] + list(check[3:]))
                except:
                    pass
            for gameid in cached:
                if cached[gameid] is not None:
                    new_old[gameid] = cached[gameid][0]["discount_percent"]
                else:
                    new_old[gameid] = 0
            return results, new_old

@asyncio.coroutine
def is_valid_game_id(appid, timeout=10):
    if not isinstance(appid, str):
        return False
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get( "http://store.steampowered.com/api/appdetails/?appids=" + appid)
            json = yield from resp.json()

            return json[appid]["success"]


@asyncio.coroutine
def get_game_name_by_id(appid, timeout=10):
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/api/appdetails/?appids=" + appid)
            data = yield from resp.json()

            return parse.unquote(data[appid]["data"]["name"])

@asyncio.coroutine
def get_game_by_id(appid, timeout=10, cc="gb"):
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/app/" + appid + "/?cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            return GamePageResult("http://store.steampowered.com/app/" + appid, appid, soup)

@asyncio.coroutine
def get_recommendations(appid, timeout=10):
    appid = str(appid)
    similar = []
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/recommended/morelike/app/" + appid)
            text = yield from resp.text()
            print(text)

            soup = BeautifulSoup(text, "html.parser")


            items = soup.find_all("div", {"class": "similar_grid_item"})
            print("found %s items" % len(items))
            for item in items:
                subsoup = item.find("div", {"class": "similar_grid_capsule"})
                if subsoup is not None:
                    similar_id = subsoup.get("data-ds-appid")
                    if similar_id is not None:
                        similar.append(similar_id)
                    else:
                        print("failed to find appid")
                else:
                    print("failed to get item")
    return similar

@asyncio.coroutine
def get_user_level(userid, timeout=10, be_specific=False):
    if not is_integer(userid):
        userid = yield from search_for_userid(userid, timeout=timeout, be_specific=be_specific)
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://api.steampowered.com/IPlayerService/GetSteamLevel/v1/?key=%s&steamid=%s" % (STEAM_KEY, userid))
            data = yield from resp.json()

            if "response" in data:
                return data["response"].get("player_level")
            return None

@asyncio.coroutine
def get_games(term, timeout=10, limit=-1, cc="gb"):
    """Search for a game on steam

    Args:
        term (str): the game you want to search for
        timeout (int, optional): how long aiohttp should wait before raising a timeout error
        limit (int, optional): how many results you want to return, 0 or less means every result
    Returns:
        a list of GameResult objects containing the results
    """
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):

            resp = yield from session.get("http://store.steampowered.com/search/?term=" + parse.quote(term) + "&cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.findAll("div", {"id": "search_result_container"})[0]
            rawResults = subsoup.findAll("a")
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                n += 1
                cls = x.get("class")
                if cls is not None and "search_result_row" in cls:
                    gr = GameResult(x)
                    #yield from gr.update_price(currency, currency_symbol)
                    results.append(gr)
            return results


@asyncio.coroutine
def category_search(link, timeout=10, limit=-1, cc="gb"):
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/" + link + "&cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            results = []
            soups = soup.find_all("a", {"class": "search_result_row"})
            for subsoup in soups:
                results.append(CategoryResult(subsoup))
                if 0 < limit <= len(results):
                    break
            return results

@asyncio.coroutine
def top_search(*args, **kwargs):
    result = yield from category_search("search/?filter=topsellers", *args, **kwargs)
    return result

@asyncio.coroutine
def upcoming_search(*args, **kwargs):
    result = yield from category_search("search/?filter=comingsoon", *args, **kwargs)
    return result

@asyncio.coroutine
def specials_search(*args, **kwargs):
    result = yield from category_search("search/?specials=1", *args, **kwargs)
    return result

@asyncio.coroutine
def new_search(timeout=10, limit=-1, cc="gb"):
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/explore/new/?cc=%s" % cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            results = []
            subsoups = soup.find_all("a", {"class": "tab_item"})
            for subsoup in subsoups:
                results.append(NewCategoryResult(subsoup))
                if 0 < limit <= len(results):
                    break

            return results

@asyncio.coroutine
def new_specials(timeout=10, limit=-1, cc="gb"):
    """Search for a game on steam

    Args:
        term (str): the game you want to search for
        timeout (int, optional): how long aiohttp should wait before raising a timeout error
        limit (int, optional): how many results you want to return, 0 or less means every result
    Returns:
        a list of GameResult objects containing the results
    """
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):

            resp = yield from session.get("http://store.steampowered.com/search/?specials=1&cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.findAll("div", {"id": "search_result_container"})[0]
            rawResults = subsoup.findAll("a")
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                n += 1
                cls = x.get("class")
                if cls is not None and "search_result_row" in cls:
                    gr = GameResult(x)
                    #yield from gr.update_price(currency, currency_symbol)
                    results.append(gr)
            return results



@asyncio.coroutine
def top_sellers(timeout=60, limit=-1, cc="gb"):
    """gets the top sellers on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/?cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_topsellers_content"})
            rawResults = subsoup.findAll("a", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break

                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                #if cls is not None and "sale_capsule" in cls:
                    tr = TopResult(x)
                    results.append(tr)
                    n += 1
                    #try:
                    #    tr = SteamSaleResult(x)
                    #    yield from tr.get_title(cc=cc, timeout=timeout)
                    #    #yield from tr.update_price(currency, currency_symbol)
                    #    results.append(tr)
                    #    n += 1
                    #except:
                    #    print("WARNING: failed to create result")
            return results


@asyncio.coroutine
def new_releases(timeout=10, limit=-1, cc="gb"):
    """gets the new releases on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/?cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_newreleases_content"})
            rawResults = subsoup.findAll("a", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                cls = x.get("class")

                if cls is not None and "tab_item" in cls:
                #if cls is not None and "sale_capsule" in cls:
                    tr = TopResult(x)
                    results.append(tr)
                    n += 1
                    #try:
                    #    tr = SteamSaleResult(x)
                    #    yield from tr.get_title(cc=cc, timeout=timeout)
                    #    #yield from tr.update_price(currency, currency_symbol)
                    #    results.append(tr)
                    #    n += 1
                    #except:
                    #    print("WARNING: failed to create result")
            return results


@asyncio.coroutine
def upcoming(timeout=10, limit=-1, cc="gb"):
    """gets the upcoming games on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/?cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_upcoming_content"})
            rawResults = subsoup.findAll("a", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                #if cls is not None and "sale_capsule" in cls:
                    tr = TopResult(x)
                    results.append(tr)
                    n += 1
                    #try:
                    #    tr = SteamSaleResult(x)
                    #    yield from tr.get_title(cc=cc, timeout=timeout)
                    #    #yield from tr.update_price(currency, currency_symbol)
                    #    results.append(tr)
                    #    n += 1
                    #except:
                    #    print("WARNING: failed to create result")
            return results


@asyncio.coroutine
def specials(timeout=10, limit=-1, cc="gb"):
    """gets the specials on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/?cc=" + cc)
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_specials_content"})
            rawResults = subsoup.findAll("a", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                    tr = TopResult(x)
                    #yield from tr.update_price(currency, currency_symbol)
                    results.append(tr)
                    n += 1
            return results


@asyncio.coroutine
def get_user(steamid, timeout=10, be_specific=False):
    """Gets some information about a specific steamid

    Args:
        steamid (str): The user's steamid
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        a UserResult object
        """
    if not is_integer(steamid):
        steamid = yield from search_for_userid(steamid, be_specific=be_specific)
    if steamid is not None:
        _check_key_set()
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key=" + STEAM_KEY + "&steamids=" + steamid)
                data = yield from resp.json()

                if "response" in data and "players" in data["response"] and len(data["response"]["players"]) > 0:
                    player = data["response"]["players"][0]
                    return UserResult(player)
    return None


@asyncio.coroutine
def get_user_library(steamid, timeout=10, be_specific=False):
    """Gets a list of all the games a user owns

    Args:
        steamid (str): The user's steamid
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        a UserLibrary object
    """
    if not is_integer(steamid):
        steamid = yield from search_for_userid(steamid, be_specific=be_specific)
    if steamid is not None:
        _check_key_set()
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + STEAM_KEY + "&steamid=" + steamid + "&format=json&include_appinfo=1&include_played_free_games=1")
                data = yield from resp.json()

                if "response" in data:
                    player = data["response"]
                    return UserLibrary(player)
    return None


userid_cache = {}  # caches search terms to steamids


@asyncio.coroutine
def get_user_id(name, timeout=10):
    """Resolves a username to a steamid, however is limited to ONLY vanity URL's. search_user_id is recommended

    Args:
        name (str): The name of the user to find the steamid of
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        either None or a steamid (str) if a vanity url matching that name is found
        """
    if name in userid_cache:
        return userid_cache[name]
    else:
        _check_key_set()
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):

                resp = yield from session.get("http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=" + STEAM_KEY + "&vanityurl=" + parse.quote(name))
                data = yield from resp.json()

                if "response" in data and "success" in data["response"] and data["response"]["success"] == 1:
                    id = data["response"]["steamid"]
                    if STEAM_CACHE:
                        userid_cache[name] = id
                    return id
                return None


@asyncio.coroutine
def search_for_userid(username, timeout=10, be_specific=False):
    """Searches for a steamid based on a username, not using vanity URLs

    Args:
        username (str): the username of the user you're searching for
        timeout (int, optional): the amount of time before aiohttp throws a timeout error
    Returns:
        A steamid (str)
        """
    if username in userid_cache:
        return userid_cache[username]
    else:
        if be_specific:
            uid = yield from get_user_id(username, timeout=timeout)
            return uid
        else:
            links = yield from search_for_users(username, limit=1, timeout=timeout)
            if len(links) > 0:
                uid = yield from extract_id_from_url(links[0][0], timeout=timeout)
                return uid
            else:
                uid = yield from get_user_id(username, timeout=timeout)
                return uid


@asyncio.coroutine
def search_for_users(username, limit=1, timeout=10):
    """Searches for basic information about users

    Args:
        username (str): the username of the user you're searching for
        timeout (int, optional): the amount of time before aiohttp throws a timeout error
        limit (int, optional): the amount of user results to return, 0 or less for all of them
    Returns:
        a list of tuples containing (steam_profile_url (str), steam_user_name (str))
        """
    _check_session_set()
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://steamcommunity.com/search/SearchCommunityAjax?text=" + parse.quote(username) + "&filter=users&sessionid=" + STEAM_SESSION + "&page=1", headers={"Cookie": "sessionid=" + STEAM_SESSION})
            data = yield from resp.json()
            soup = BeautifulSoup(data["html"], "html.parser")
            stuff = soup.find_all("a", {"class": "searchPersonaName"})
            links = []
            for thing in stuff:
                try:
                    links.append((thing.get("href"), thing.get_text()))
                    if len(links) >= limit > 0:
                        return links
                except:
                    pass
            return links


@asyncio.coroutine
def extract_id_from_url(url, timeout=10):
    """Extracts a steamid from a steam user's profile URL, or finds it based on a vanity URL

    Args:
        url (str): The url of the user's profile
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        the steamid of the user (str) or None if no steamid could be extracted
    """
    if url.startswith("http://steamcommunity.com/profiles/"):
        return url[len("http://steamcommunity.com/profiles/"):]
    elif url.startswith("http://steamcommunity.com/id/"):
        vanityname = url[len("http://steamcommunity.com/id/"):]
        id = yield from get_user_id(vanityname, timeout=timeout)
        return id


@asyncio.coroutine
def get_item(appid, item_name, timeout=10, currency="GBP", currency_symbol="£"):
    """Gets information about an item from the market

    Args:
        appid (str): The appid of the game the item belongs to, or the name if you don't know the ID
        item_name (str): The item you're searching for
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
        currency (str, optional): The currency to convert the item's price to (default GBP)
        currency_symbol (str, optional): the currency symbol to use for the item's price (default £)
    Returns:
        an ItemResult object
        """
    if not is_integer(appid):
        appdata = yield from get_app(appid, timeout)
        appid = appdata[0]
    if appid is not None:
        item_name = yield from get_item_name(item_name, appid, timeout=timeout)
        if item_name is not None:
            with aiohttp.ClientSession() as session:
                with aiohttp.Timeout(timeout):
                    resp = yield from session.get("http://steamcommunity.com/market/listings/" + appid + "/" + parse.quote(item_name))
                    text = yield from resp.text()
                    soup = BeautifulSoup(text, "html.parser")

                    result = ItemResult(soup)
                    yield from result.update_price(currency, currency_symbol)
                    return result


gameid_cache = {}  # caches search terms to (appid, appname) tuples


@asyncio.coroutine
def get_app(name, timeout=10):
    """Gets an appid based off of the app name

    Args:
        name (str): the name of the app (game)
        timeout (int, optional): the amount of time before aiohttp raises a timeout error
    Returns:
        A tuple containing (appid (str), apptitle (str))
        """
    if name in gameid_cache:
        return gameid_cache[name]
    else:
        dat = yield from get_games(name, limit=1, timeout=timeout)
        if len(dat) > 0:
            if STEAM_CACHE:
                gameid_cache[name] = (dat[0].id, dat[0].title)
            return dat[0].id, dat[0].title
        else:
            return None, None


item_name_cache = {}  # caches search terms to item url names


@asyncio.coroutine
def get_item_name(name, appid, timeout=10):
    """Finds an item's name required for the URL of it's store page

    Args:
        name (str): The name of the item you're searching for
        appid (str): The appid of the game the item belongs to
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        the item name (str) or None if no item could be found
        """
    cache_name = appid + "::" + name
    if cache_name in item_name_cache:
        return item_name_cache[cache_name]
    else:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                if appid != "":
                    resp = yield from session.get("http://steamcommunity.com/market/search?appid=" + appid + "&q=" + parse.quote(name))
                else:
                    resp = yield from session.get("http://steamcommunity.com/market/search?q=" + parse.quote(name))
                text = yield from resp.text()
                soup = BeautifulSoup(text, "html.parser")

                namesoup = soup.find("span", {"class": "market_listing_item_name"})
                if namesoup is not None:
                    item_name = namesoup.get_text()
                    if STEAM_CACHE:
                        item_name_cache[cache_name] = item_name
                    return item_name
                return None


@asyncio.coroutine
def get_wishlist(userid, cc="gb", timeout=10, discount_only=True, be_specific=False):
    if not is_integer(userid):
        userid = yield from search_for_userid(userid, be_specific=be_specific)
    if userid is not None:
        print(userid)
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://steamcommunity.com/profiles/" + userid + "/wishlist?cc=" + cc)
                text = yield from resp.text()
                soup = BeautifulSoup(text, "html.parser")

                games = []

                wishlist_soup = soup.find("div", {"id": "wishlist_items"})
                if wishlist_soup is not None:
                    wishlist_items = wishlist_soup.find_all("div", {"class": "wishlistRowItem"})
                    for row in wishlist_items:
                        game_link = "???"
                        item = row.find("a", {"class": "pullup_item storepage_btn_alt"})
                        if item is not None:
                            game_link = item.get("href")

                        game_name = "???"
                        game_name_soup = row.find("h4")
                        if game_name_soup is not None:
                            game_name = game_name_soup.get_text()



                        discount_soup = row.find("div", {"class": "discount_block"})
                        if discount_soup is not None:
                            discount_percent = "??%"
                            discount_percent_soup = discount_soup.find("div", {"class": "discount_pct"})
                            if discount_percent_soup is not None:
                                discount_percent = discount_percent_soup.get_text()

                            discount_price = "???"
                            discount_price_soup = discount_soup.find("div", {"class": "discount_final_price"})
                            if discount_price_soup is not None:
                                discount_price = discount_price_soup.get_text()

                            discount_original_price = "???"
                            discount_original_price_soup = discount_soup.find("div", {"class": "discount_original_price"})
                            if discount_original_price_soup is not None:
                                discount_original_price = discount_original_price_soup.get_text()

                            games.append((game_name, game_link, discount_original_price, discount_price, discount_percent))
                        elif not discount_only:
                            price = "???"
                            price_soup = item.find("div", {"class": "price"})
                            if price_soup is not None:
                                price = price_soup.get_text()

                            games.append((game_name, game_link, price))

                return UserWishlist(games)


@asyncio.coroutine
def get_screenshots(username, timeout=10, limit=-1):
    """Searches for the most recent (public) screenshots a user has uploaded,

    Args:
        username (str): The name of the user you're finding screenshots for
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
        limit (intm optional): The amount of screenshots to find, 0 or less for all of them
    Returns:
        a list of URLs (strings) linking to the screenshots
        """
    ulinks = yield from search_for_users(username, limit=1)
    if len(ulinks) > 0:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get(ulinks[0][0] + "/screenshots/")
                text = yield from resp.text()
                soup = BeautifulSoup(text, "html.parser")

                links = []
                screensoups = soup.find_all("a", {"class": "profile_media_item"})
                for ssoup in screensoups:
                    imgsoup = ssoup.find("img")
                    if imgsoup is not None:
                        links.append(imgsoup.get("src"))
                        if len(links) >= limit > 0:
                            break
                return links
    else:
        return None


@asyncio.coroutine
def top_game_playercounts(limit=10, timeout=10):
    """Gets the top games on steam right now by player count

    Args:
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
        limit (int, optional): The amount of playercounts to return, 0 or less for all found
    Returns:
        A list of tuples in the format (current_players (str), peak_players (str), game_name (str), game_link (str))
        """
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/stats")
            text = yield from resp.text()
            soup = BeautifulSoup(text, "html.parser")

            stats = []
            ssoups = soup.find_all("tr", {"class": "player_count_row"})
            for subsoup in ssoups:
                linksoup = subsoup.find("a", {"class": "gameLink"})
                name = linksoup.get_text()
                link = linksoup.get("href")
                stuff = subsoup.find_all("span", {"class": "currentServers"})
                if len(stuff) > 0:
                    current_players = stuff[0].get_text()
                    peak_players = stuff[1].get_text()
                    stats.append((current_players, peak_players, name, link))
                    if len(stats) >= limit > 0:
                        break
            return stats

@asyncio.coroutine
def get_playercount(appid, timeout=10):
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?key=%s&format=json&appid=%s" % (STEAM_KEY, appid))
            data = yield from resp.json()

            if "response" in data:
                return data["response"].get("player_count")

@asyncio.coroutine
def search_for_playercount(appid, timeout=10, be_specific=False):
    if not be_specific:
        appid, appname = yield from get_app(appid)
    else:
        appname = appid

    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/stats")
            text = yield from resp.text()
            soup = BeautifulSoup(text, "html.parser")

            number = 0
            ssoups = soup.find_all("tr", {"class": "player_count_row"})
            for subsoup in ssoups:
                number += 1
                linksoup = subsoup.find("a", {"class": "gameLink"})
                name = linksoup.get_text()
                link = linksoup.get("href")
                if link.split("/")[-2] == appid:
                    stuff = subsoup.find_all("span", {"class": "currentServers"})
                    if len(stuff) > 0:
                        current_players = stuff[0].get_text()
                        peak_players = stuff[1].get_text()
                        return (name, current_players, peak_players, number, link)

    if appid is None:
        return None

    current_players = yield from get_playercount(appid, timeout=timeout)
    if current_players is not None:
        return (appname, current_players, "???", "???", "http://store.steampowered.com/app/%s/" % appid)



@asyncio.coroutine
def steam_user_data(timeout=10):
    """Gets information about the amount of users on steam over the past 48 hours

    Args:
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        A tuple containing (min_users (int), max_users (int), current_users (int))"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/stats/userdata.json")
            data = yield from resp.json()
            data = data[0]["data"]

            min_users = -1
            max_users = -1
            for pair in data:
                if min_users == -1 or pair[1] < min_users:
                    min_users = pair[1]
                if max_users == -1 or pair[1] > max_users:
                    max_users = pair[1]
            return min_users, max_users, data[-1][1]



@asyncio.coroutine
def get_user_achievements(username, gameid, timeout=10, be_specific=False):
    """Gets information about a specific user's achievements for a specific game

    Args:
        username (str): the id or name of the user you want the achievements for
        gameid (str): the id or name of the game you want the achievements for
        timeout (int): the amount of time before aiohttp raises a timeout error
    Returns:
        UserAchievement: the user achievements found"""
    if not is_integer(username):
        username = yield from search_for_userid(username, timeout=timeout, be_specific=be_specific)
    if not is_integer(gameid):
        gameid, gamename = yield from get_app(gameid, timeout=timeout)
    else:
        gamename = "???"
    _check_key_set()
    if username is not None and gameid is not None:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid=" + gameid + "&key=" + STEAM_KEY + "&steamid=" + username)
                data = yield from resp.json()
                if "playerstats" in data and "achievements" in data["playerstats"]:
                    return UserAchievements(gameid, gamename, data["playerstats"]["achievements"])


@asyncio.coroutine
def get_global_achievements(gameid, timeout=10):
    """Gets information about a game's global achievement stats (name, description, percent completed)

    Args:
        gameid (str): the id or name of the game you want the achievements for
        timeout (int, optional): the amount of time before aiohttp raises a timeout error
    Returns:
        GlobalAchievements: the global achievements found
        """
    if not is_integer(gameid):
        gameid, gamename = yield from get_app(gameid, timeout=timeout)
    if gameid is not None:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://steamcommunity.com/stats/" + gameid + "/achievements/")
                text = yield from resp.text()
                soup = BeautifulSoup(text, "html.parser")

                return GlobalAchievements(soup)



@asyncio.coroutine
def count_user_removed(username, timeout=10, be_specific=False):
    if not is_integer(username):
        username = yield from search_for_userid(username, be_specific=be_specific)
    if username is not None:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://removed.timekillerz.eu/content/steambot.php?steamid=" + parse.quote(username))
                data = yield from resp.json()
                if "response" in data and "removed_count" in data["response"] and "game_count" in data["response"] and data["response"]["games"] is not None\
                        and "players" in data["response"] and len(data["response"]["players"]) > 0 and "personaname" in data["response"]["players"][0] and "total_removed_count" in data["response"]:
                    return (data["response"]["removed_count"], data["response"]["game_count"], data["response"]["total_removed_count"], data["response"]["players"][0]["personaname"])


    return None


def convert_to_table(items, columns, seperator="|", spacing=1):
    """Utility function to convert a list of times in to a neat table, with the given columns

    Args:
        items (list[str]): the strings you want to put in the table
        columns (int): the amount of columns you want in the table
        seperator (str, optional): what to seperate the columns by, default is |
        spacing (int, optional): how many spaces to put either side of the seperator, default is 1
    Returns:
        list[str]: the rows of the table
        """
    max_sizes = [0] * columns
    for i, item in enumerate(items):
        column = i % columns
        if len(item) > max_sizes[column]:
            max_sizes[column] = len(item)

    spacing = " " * spacing
    lines = [""] * math.ceil(len(items) / columns)
    for i in range(0, len(items), columns):
        line = ""
        maxc = min(len(items), i+columns)
        for j in range(i, maxc):
            c = j - i
            line += items[j] + " " * (max_sizes[c] - len(items[j]))
            if c < maxc - 1:
                line += spacing + seperator + spacing
        lines.append(line)
    return lines
