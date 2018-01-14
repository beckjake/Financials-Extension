#  baseclient.py
#
#  license: GNU LGPL
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.


import codecs
import gzip
import logging
import random
import select

from http.client import HTTPConnection, HTTPSConnection, HTTPException
from http import cookiejar

import urllib.request

from datacode import Datacode

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class RedirectException(HTTPException):
    def __init__(self, location):
        self.location = location


class HttpException(HTTPException):
    def __init__(self, url, status):
        self.url = url
        self.status = status


class BaseClient:
    def __init__(self):
        self.connections = {}
        self.cookies = cookiejar.CookieJar()

        user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0'
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.79 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',

            # some older mobile agents
            'Mozilla/5.0 (Linux; Android 4.3; Nexus 4 Build/JSS15Q) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.72 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.3; Nexus 4 Build/JWR66D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.111 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.3; Nexus 4 Build/JWR66Y) AppleWebKit/537.36 (KHTML like Gecko) Chrome/35.0.1916.141 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.3; Nexus 4 Build/JWR66Y) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.72 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.3; Nexus 4 Build/JWR66Y) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.82 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.136 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.136 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.93 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.99 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.138 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.141 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.131 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.135 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.117 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 4 Build/KTU84Q) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 4.4; Nexus 4 Build/KRT16S) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.0.1; Nexus 4 Build/LRX22C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.93 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.0.2; Nexus 4 Build/LRX22G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.93 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 4 Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.93 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 4 Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.109 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 4 Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.111 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1.1; Nexus 4 Build/LMY47V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.93 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1; Nexus 4 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.109 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1; Nexus 4 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 5.1; Nexus 4 Build/LMY47D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.109 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; U; Android 4.2.1; en-us; Nexus 4 Build/JOP40D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'Mozilla/5.0 (Linux; U; Android 4.2.2; en-us; Nexus 4 Build/JDQ39) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'Mozilla/5.0 (Linux; U; Android 4.2; en-us; Nexus 4 Build/JOP12D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'Mozilla/5.0 (Linux; U; Android 4.2; en-us; Nexus 4 Build/JOP12D) Gecko/20100101 Firefox/25.0',
            'Mozilla/5.0 (Linux; U; Android 4.2; en-us; Nexus 4 Build/JVP15I) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'Mozilla/5.0 (Linux; U; Android 5.0.1; en-gb; Nexus 4 Build/LRX22C) AppleWebKit/537.16 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.16',
            'Mozilla/5.0 (Linux; U; Android 5.0.2; en-us; Nexus 4 Build/LRX22G) AppleWebKit/537.16 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.16',
        ]

        self.default_headers = {
            'User-Agent': random.sample(user_agents, 1)[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
        }

    def request(self, method: str, url: str, data=None, headers={}, **kwargs):

        _headers = self.default_headers.copy()
        for key, value in headers.items():
            _headers[key] = value

        connection = None

        scheme, _, host, path = url.split('/', 3)

        if (scheme, host) in self.connections:
            connection = self.connections.get((scheme, host))

        if connection and select.select([connection.sock], [], [], 0)[0]:
            connection.close()
            connection = None

        if not connection:
            logger.debug('Creating connection --------------------------------------------------')
            connection = HTTPConnection(host, **kwargs) if scheme == 'http:' else HTTPSConnection(host, **kwargs)

        logger.debug('Creating request -----------------------------------------------------')
        logger.info('url=%s', url)

        # generate and add cookie headers
        request = urllib.request.Request(url)

        self.cookies.add_cookie_header(request)
        if request.get_header('Cookie'):
            _headers['Cookie'] = request.get_header('Cookie')

        for key, value in _headers.items():
            logger.debug('Header: %s=%s', key, value)

        # request
        connection.request(method, '/' + path, data, _headers)
        response = connection.getresponse()

        logger.debug('Processing response --------------------------------------------------')

        # logger.debug('response.status={}'.format(response.status))
        for key, value in response.getheaders():
            logger.debug('Header: %s=%s', key, value)

        self.cookies.extract_cookies(response, request)
        self.connections[(scheme, host)] = connection

        return response

    def urlopen(self, url, redirect=True, data=None, headers={}, **kwargs):

        response = self.request('POST' if data else 'GET', url, data, headers, **kwargs)
        text = response.read()

        if 300 <= response.status < 400:
            location = response.getheader('Location')

            if location and redirect:

                if location.startswith('/'):
                    scheme, _, host, path = url.split('/', 3)
                    location = '{}//{}{}'.format(scheme, host, location)

                response = self.request('POST' if data else 'GET', location, data, headers, **kwargs)
                text = response.read()
            else:
                raise RedirectException(location)

        if response.status >= 400:
            raise HttpException(url, response.status)

        if response.getheader('Content-Encoding') == 'gzip':
            text = gzip.decompress(text)

        content_type = response.headers.get_content_charset()
        if content_type is None:
            content_type = 'utf-8'
        text = codecs.decode(text, encoding=content_type, errors='ignore')

        return text

    def _return_value(self, data: dict, datacode: int):

        """
        Format data from tick data to out put format - mostly formatting date/time

        :param data: tick data
        :param datacode: the requested datacode
        :return: value or None
        """

        try:
            if datacode == Datacode.PREV_CLOSE.value and Datacode.PREV_CLOSE in data:
                return data[Datacode.PREV_CLOSE]

            elif datacode == Datacode.OPEN.value and Datacode.OPEN in data:
                return data[Datacode.OPEN]

            elif datacode == Datacode.CHANGE.value and Datacode.CHANGE in data:
                return data[Datacode.CHANGE]

            elif datacode == Datacode.LAST_PRICE_DATE.value and Datacode.LAST_PRICE_DATE in data:
                return data[Datacode.LAST_PRICE_DATE].isoformat()

            elif datacode == Datacode.LAST_PRICE_TIME.value and Datacode.LAST_PRICE_TIME in data:
                return data[Datacode.LAST_PRICE_TIME].isoformat()

            elif datacode == Datacode.CHANGE_IN_PERCENT.value and Datacode.CHANGE_IN_PERCENT in data:
                return data[Datacode.CHANGE_IN_PERCENT]

            elif datacode == Datacode.LOW.value and Datacode.LOW in data:
                return data[Datacode.LOW]

            elif datacode == Datacode.HIGH.value and Datacode.HIGH in data:
                return data[Datacode.HIGH]

            elif datacode == Datacode.LAST_PRICE.value and Datacode.LAST_PRICE in data:
                return data[Datacode.LAST_PRICE]

            elif datacode == Datacode.LOW_52_WEEK.value and Datacode.LOW_52_WEEK in data:
                return data[Datacode.LOW_52_WEEK]

            elif datacode == Datacode.HIGH_52_WEEK.value and Datacode.HIGH_52_WEEK in data:
                return data[Datacode.HIGH_52_WEEK]

            elif datacode == Datacode.MARKET_CAP.value and Datacode.MARKET_CAP in data:
                return data[Datacode.MARKET_CAP]

            elif datacode == Datacode.VOLUME.value and Datacode.VOLUME in data:
                return data[Datacode.VOLUME]

            elif datacode == Datacode.AVG_DAILY_VOL_3MOMTH.value and Datacode.AVG_DAILY_VOL_3MOMTH in data:
                return data[Datacode.AVG_DAILY_VOL_3MOMTH]

            elif datacode == Datacode.CLOSE.value and Datacode.CLOSE in data:
                return data[Datacode.CLOSE]

            elif datacode == Datacode.ADJ_CLOSE.value and Datacode.ADJ_CLOSE in data:
                return data[Datacode.ADJ_CLOSE]

            elif datacode == Datacode.TICKER.value and Datacode.TICKER in data:
                return data[Datacode.TICKER]

            elif datacode == Datacode.EXCHANGE.value and data[Datacode.EXCHANGE]:
                return data[Datacode.EXCHANGE]

            elif datacode == Datacode.CURRENCY.value and Datacode.CURRENCY in data:
                return data[Datacode.CURRENCY]

            elif datacode == Datacode.NAME.value and data[Datacode.NAME]:
                return data[Datacode.NAME]

            elif datacode == Datacode.TIMEZONE.value and data[Datacode.TIMEZONE]:
                return str(data[Datacode.TIMEZONE])

        except BaseException as e:
            return 'BaseClient.return_value(\'{}\', {}) - {}'.format(data, datacode, e)

        return "Data doesn't exist - {}".format(datacode)

    def save_wrapper(self, f):
        try:
            value = f()
            logger.debug(value)
            return value
        except BaseException as e:
            pass

        return None
