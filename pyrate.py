from lxml.html import fromstring
from lxml.html.clean import clean_html
from operator import attrgetter
from re import search, sub
from requests import get
from requests.utils import unquote
import datetime


class Torrent(object):

    def __init__(self):
        self.obj = {
            'date': '',
            'size_str': '0 Kib',
            'size': 0,
            'seeders': 0,
            'leechers': 0,
            'comment_amount': 0,
            'torrent': '',
            'link': '',
            'full_link': '',
            'magnet': '',
            'uploader': '',
            'category': '',
            'attributes': {
                'magnet': False,
                'trusted': False,
                'comments': False,
                'torrent_link': False,
                'vip': False,
                'cover_image': False
            }
        }

    def __getattr__(self, name):
        if name in self.obj:
            return self.obj[name]
        raise AttributeError

    def info(self):
        info = ''
        info += 'Title:    {}\n'.format(self.title)
        info += 'Link:     {}\n'.format(self.link)
        info += 'Size:     {}\n'.format(self.size_str)
        info += 'Category: {}\n'.format(self.category)
        info += 'Seeders:  {}\n'.format(self.seeders)
        info += 'Leechers: {}\n'.format(self.leechers)
        return info

    def print(self):
        print(self.info())


class TorrentList(list):

    def __add__(self, _list):
        return TorrentList(list(self) + _list)

    def order(self, key=None, reverse=False):
        return TorrentList(sorted(self, key=attrgetter(key), reverse=reverse))

    def map(self, key):
        if key is None:
            raise ValueError('key must not be None')
        try:
            attributes = [getattr(torrent, key) for torrent in self]
        except AttributeError:
            raise AttributeError('Torrent key does not exist: "{}"'
                                 .format(key))
        return attributes

    def print(self):
        for torrent in self:
            torrent.print()

    def __getitem__(self, item):
        result = list.__getitem__(self, item)
        if type(result) == list:
            return TorrentList(result)
        return result


class Pyrate(object):

    sorts = {
        'type': ['13', '14'],
        'name': ['1', '2'],
        'date': ['3', '4'],
        'size': ['5', '6'],
        'seeders': ['7', '8'],
        'leechers': ['9', '10'],
        'uploader': ['11', '12']
    }

    categories = {
        'all': 'all',
        'audio': {
            'all': 100,
            'music': 101,
            'audio_books': 102,
            'sound_clips': 103,
            'flac': 104,
            'other': 199
        },
        'video': {
            'all': 200,
            'movies': 201,
            'movies_dvdr': 202,
            'music_videos': 203,
            'movie_clips': 204,
            'tv_shows': 205,
            'handheld': 206,
            'hd_movies': 207,
            'hd_tv_shows': 208,
            '3d': 209,
            'other': 299
        },
        'applications': {
            'all': 300,
            'windows': 301,
            'mac': 302,
            'unix': 303,
            'handheld': 304,
            'ios': 305,
            'android': 306,
            'other': 399
        },
        'games': {
            'all': 400,
            'pc': 401,
            'mac': 402,
            'psx': 403,
            'xbox360': 404,
            'wii': 405,
            'handheld': 406,
            'ios': 407,
            'android': 408,
            'other': 499
        },
        'porn': {
            'all': 500,
            'movies': 501,
            'movies_dvdr': 502,
            'pictures': 503,
            'games': 504,
            'hd': 505,
            'movie_clips': 506,
            'other': 599
        },
        'other': {
            'all': 600,
            'e-books': 601,
            'comics': 602,
            'pictures': 603,
            'covers': 604,
            'physibles': 605,
            'other': 699
        }
    }

    def __init__(self, load_file=False):
        self.load_file = load_file
        self.base_url = 'http://thepiratebay.se'

    def _parse_url(self, url):
        if self.load_file:
            return clean_html(fromstring(open('tpb.html', 'r').read()))
        else:
            return clean_html(fromstring(get(url).text))

    def _parse_category(self, string):
        string = string.split('.')
        cur = self.categories
        for cat in string:
            try:
                cur = cur[cat]
            except KeyError:
                raise KeyError('Category does not exist')
        if type(cur) not in [int, str]:
            cur = cur['all']
        return cur

    def _parse_html(self, data):
        content = data.xpath('.//table[@id="searchResult"]')[0]

        torrents = TorrentList()

        if content is None:
            return torrents

        for torrent in content.xpath('.//tr'):

            link_info = torrent.xpath('.//div[@class="detName"]/a')
            if len(link_info) == 0:
                continue
            link_info = link_info[0]

            peer_info = torrent.xpath('.//td[@align="right"]')
            if len(peer_info) != 2:
                continue

            torrent_info = Torrent()

            torrent_info.title = link_info.text_content()
            torrent_info.link = sub('/[^/]*$', '',
                                    self.base_url + link_info.attrib['href'])
            torrent_info.full_link = self.base_url + link_info.attrib['href']
            torrent_info.seeders = int(peer_info[0].text)
            torrent_info.leechers = int(peer_info[1].text)

            description = torrent.find_class('detDesc')

            if len(description):
                description = description[0].text_content()
                description = sub('\s', ' ', description)
                date = search('[a-zA-Z0-9]+-[a-zA-Z0-9]+\s\d+(:\d+)?',
                              description)
                if date:
                    date = date.group()
                    if 'Y-day' in date:
                        time = datetime.datetime.today()
                        date = date.replace('Y-day', '-'.join([str(i).zfill(2)
                                            for i in [time.month, time.day]]))
                    torrent_info.date = date
                size_str = search('Size[^,]*', description)
                if size_str:
                    size_str = size_str.group()[5:]
                    torrent_info.size_str = size_str
                size_info = size_str.lower().split(' ')
                size = float(size_info[0])
                if size_info[1] == 'kib':
                    size *= 1024
                elif size_info[1] == 'mib':
                    size *= 1048576
                elif size_info[1] == 'gib':
                    size *= 1073741824
                torrent_info.size = size
                uploader = search('ULed\sby\s.*', description)
                if uploader:
                    torrent_info.uploader = uploader.group()[8:]

            ttype = torrent.find_class('vertTh')
            attr = None

            if len(ttype) != 0:
                ttype = ttype[0]
                attr = ttype.getnext()
                ttype = ttype.xpath('.//a')
            if len(ttype) == 2:
                category = '.'.join([i.text_content().lower() for i in ttype])
                torrent_info.category = sub('[\s-]+', '_', category)

            if attr is not None:
                attr = [i for i in attr.xpath('.//a|.//img')
                        if i.tag == 'a' or i.tag == 'img']
                for link in attr:
                    if link.tag == 'a':
                        attributes = link.attrib
                        if 'href' in attributes and \
                                attributes['href'][:7] == 'magnet:':
                            torrent_info.attributes['magnet'] = True
                            torrent_info.magnet = unquote(attributes['href'])
                        elif 'href' in attributes and \
                                attributes['href'][-7:] == 'torrent':
                            torrent_info.attributes['torrent_link'] = True
                            torrent_info.torrent = attributes['href']
                    else:
                        iattr = link.attrib
                        if 'alt' in iattr and iattr['alt'] == 'Trusted':
                            torrent_info.attributes['trusted'] = True
                        elif 'alt' in iattr and iattr['alt'] == 'VIP':
                            torrent_info.attributes['vip'] = True
                        if 'src' in iattr and 'title' in iattr:
                            if 'cover image' in iattr['title']:
                                torrent_info.attributes['cover_image'] = True
                            elif 'comments.' in iattr['title']:
                                torrent_info.attributes['comments'] = True
                                count = search('\d+', iattr['title'])
                                if count:
                                    torrent_info.comment_amount = \
                                        int(count.group())

            torrents.append(torrent_info)

        return torrents

    def _parse_sort(self, sort, ascending):
        if type(sort) == str:
            try:
                sort = self.sorts[sort][int(ascending)]
            except KeyError:
                raise KeyError('Invalid sort')
        return sort

    def top100(self, category='all'):
        cat_id = self._parse_category(category)
        url = '{}/top/{}'.format(self.base_url, str(cat_id))
        dom = self._parse_url(url)
        return self._parse_html(dom)

    def browse(self,
               category=None,
               page=0,
               maxlen=30,
               sort=0,
               ascending=False):

        if category is None:
            raise ValueError('category must be set')
        if category is 'all':
            raise ValueError('the browse method does not have \
                             the "all" category')

        cat_id = self._parse_category(category)
        sort = self._parse_sort(sort, ascending)
        torrents = TorrentList()
        while maxlen > 0:
            url = '{}/browse/{}/{}/{}'.format(self.base_url,
                                              cat_id,
                                              page,
                                              sort)
            block = self._parse_html(self._parse_url(url))
            if len(block) == 0:
                break
            torrents += block[:maxlen]
            maxlen -= len(block)
            page += 1

        return torrents

    def search(self,
               search=None,
               category='all',
               page=0,
               sort=0,
               maxlen=30,
               ascending=False):

        if type(search) != str:
            raise TypeError('search must be a string')
        if len(search) == 0:
            raise ValueError('search must be at least one letter long')
        cat_id = self._parse_category(category)
        sort = self._parse_sort(sort, ascending)
        torrents = TorrentList()
        while maxlen > 0:
            url = '{}/search/{}/{}/{}/{}'.format(self.base_url,
                                                 search,
                                                 page,
                                                 sort,
                                                 cat_id)
            block = self._parse_html(self._parse_url(url))
            torrents += block[:maxlen]
            if len(block) == 0 or len(block) != 30:
                break
            maxlen -= len(block)
            page += 1

        return torrents
