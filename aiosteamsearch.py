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


class SearchResult:
    """Class containing information about a game search result"""
    def __init__(self, soup):
        """

        Args:
            soup (BeautifulSoup): soup from game search page
        """
        self.link = soup.get("href")
        linkspl = self.link.split("/")
        self.id = linkspl[4]

        self.image = ""
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

    def __str__(self):
        return self.title


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

    def __str__(self):
        return self.title


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

    def single_line_format(self):
        """Converts the object to single line format

        Returns:
            A string representing this object
        """
        if self.playtime_2weeks != "???":
            return self.format_playtime(self.playtime_forever) + " hours on record (" + self.format_playtime(self.playtime_2weeks) + " hours in the last 2 weeks)"
        else:
            return self.format_playtime(self.playtime_forever) + " hours on record"


class UserLibrary:
    """Class containing information about a set of games in the users library"""
    def __init__(self, data):
        self.count = data.get("game_count", "???")
        self.games = {}
        for game in data.get("games", []):
            ugame = UserGame(game)
            self.games[ugame.id] = ugame

    def get_game_list(self, limit=10):
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
            pairs[i] = (result.name, result.single_line_format())
            if len(result.name) > longest_name:
                longest_name = len(result.name)
        final = [""] * len(results)
        longest_name += 3
        for i, pair in enumerate(pairs):
            final[i] = pair[0] + " " * (longest_name - len(pair[0])) + pair[1]
        return final


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
    def update_price(self):
        """Attempts to convert the price to GBP"""
        try:
            rawprice = yield from exchange(float(self.price.replace(",", ".")), self.currency, "GBP")
            self.price = "£" + str(rawprice)
        except:
            if STEAM_PRINTING:
                print("failed to convert currency (" + self.currency + ")")


@asyncio.coroutine
def get_games(term, timeout=10, limit=-1):
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

            resp = yield from session.get("http://store.steampowered.com/search/?term=" + parse.quote(term))
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
                    results.append(SearchResult(x))
            return results


@asyncio.coroutine
def top_sellers(timeout=10, limit=-1):
    """gets the top sellers on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/")
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_topsellers_content"})
            rawResults = subsoup.findAll("div", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                n += 1
                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                    results.append(TopResult(x))
            return results


@asyncio.coroutine
def new_releases(timeout=10, limit=-1):
    """gets the new releases on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/")
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_newreleases_content"})
            rawResults = subsoup.findAll("div", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                n += 1
                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                    results.append(TopResult(x))
            return results


@asyncio.coroutine
def upcoming(timeout=10, limit=-1):
    """gets the upcoming games on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/")
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_upcoming_content"})
            rawResults = subsoup.findAll("div", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                n += 1
                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                    results.append(TopResult(x))
            return results


@asyncio.coroutine
def specials(timeout=10, limit=-1):
    """gets the specials on the front page of the store

    Args:
        timeout (int, optional): how long aiohttp should wait before throwing a timeout error
        limit (int, optional): how many results it should return, 0 or less returns every result found
    Returns:
        a list of TopResult objects"""
    with aiohttp.ClientSession() as session:
        with aiohttp.Timeout(timeout):
            resp = yield from session.get("http://store.steampowered.com/")
            text = yield from resp.read()
            soup = BeautifulSoup(text, "html.parser")

            subsoup = soup.find("div", {"id": "tab_specials_content"})
            rawResults = subsoup.findAll("div", recursive=False)
            results = []
            n = 0
            for x in rawResults:
                if n >= limit > 0:
                    break
                n += 1
                cls = x.get("class")
                if cls is not None and "tab_item" in cls:
                    results.append(TopResult(x))
            return results


@asyncio.coroutine
def get_user(steamid, timeout=10):
    """Gets some information about a specific steamid

    Args:
        steamid (str): The user's steamid
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        a UserResult object
        """
    if not is_integer(steamid):
        steamid = yield from search_for_userid(steamid)
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
def get_user_library(steamid, timeout=10):
    """Gets a list of all the games a user owns

    Args:
        steamid (str): The user's steamid
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        a UserLibrary object
    """
    if not is_integer(steamid):
        steamid = yield from search_for_userid(steamid)
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
def search_for_userid(username, timeout=10):
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
        links = yield from search_for_users(username, limit=1, timeout=timeout)
        uid = yield from extract_id_from_url(links[0][0], timeout=timeout)
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
def get_item(appid, item_name, timeout=10):
    """Gets information about an item from the market

    Args:
        appid (str): The appid of the game the item belongs to, or the name if you don't know the ID
        item_name (str): The item you're searching for
        timeout (int, optional): The amount of time before aiohttp raises a timeout error
    Returns:
        an ItemResult object
        """
    if not is_integer(appid):
        appdata = yield from get_app(appid, timeout)
        appid = appdata[0]
    item_name = yield from get_item_name(item_name, appid, timeout=timeout)
    if item_name is not None and appid is not None:
        with aiohttp.ClientSession() as session:
            with aiohttp.Timeout(timeout):
                resp = yield from session.get("http://steamcommunity.com/market/listings/" + appid + "/" + parse.quote(item_name))
                text = yield from resp.text()
                soup = BeautifulSoup(text, "html.parser")

                result = ItemResult(soup)
                yield from result.update_price()
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
        if STEAM_CACHE:
            gameid_cache[name] = (dat[0].id, dat[0].title)
        return dat[0].id, dat[0].title


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


