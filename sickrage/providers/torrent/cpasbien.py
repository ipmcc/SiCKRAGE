#!/usr/bin/env python2

# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import traceback

import sickrage
from core.caches import tv_cache
from core.helpers import bs4_parser
from providers import TorrentProvider


class CpasbienProvider(TorrentProvider):
    def __init__(self):
        super(CpasbienProvider, self).__init__("Cpasbien")

        self.supportsBacklog = True
        self.public = True
        self.ratio = None
        self.url = "http://www.cpasbien.io"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = CpasbienCache(self)

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        size = -1
        seeders = 1
        leechers = 0

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            sickrage.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    sickrage.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.url + '/recherche/' + search_string.replace('.', '-') + '.html'
                sickrage.srLogger.debug("Search URL: %s" % searchURL)
                data = self.getURL(searchURL)

                if not data:
                    continue

                try:
                    with bs4_parser(data) as html:
                        lin = erlin = 0
                        resultdiv = []
                        while erlin == 0:
                            try:
                                classlin = 'ligne' + str(lin)
                                resultlin = html.findAll(attrs={'class': [classlin]})
                                if resultlin:
                                    for ele in resultlin:
                                        resultdiv.append(ele)
                                    lin += 1
                                else:
                                    erlin = 1
                            except Exception:
                                erlin = 1

                        for row in resultdiv:
                            try:
                                link = row.find("a", title=True)
                                title = link.text.lower().strip()
                                pageURL = link[b'href']

                                # downloadTorrentLink = torrentSoup.find("a", title.startswith('Cliquer'))
                                tmp = pageURL.split('/')[-1].replace('.html', '.torrent')

                                downloadTorrentLink = ('http://www.cpasbien.io/telechargement/%s' % tmp)

                                if downloadTorrentLink:
                                    download_url = downloadTorrentLink
                                    size = -1
                                    seeders = 1
                                    leechers = 0

                            except (AttributeError, TypeError):
                                continue

                            if not all([title, download_url]):
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode is not 'RSS':
                                sickrage.srLogger.debug("Found result: %s " % title)

                            items[mode].append(item)

                except Exception as e:
                    sickrage.srLogger.error("Failed parsing provider. Traceback: %s" % traceback.format_exc())

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class CpasbienCache(tv_cache.TVCache):
    def __init__(self, provider_obj):
        tv_cache.TVCache.__init__(self, provider_obj)

        self.minTime = 30

    def _getRSSData(self):
        # search_strings = {'RSS': ['']}
        return {'entries': {}}
