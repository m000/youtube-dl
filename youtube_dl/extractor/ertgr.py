# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    clean_html,
)
import logging
import re


class ERTGRIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ertflix\.gr/(?P<path>[a-z0-9/-]+)/(?P<id>[a-z0-9-]+)'

    # To get the md5sum for the tests, use:
    #    python3 -m youtube_dl <url> --test
    #    md5sum <output file>
    _TESTS = (
        {
            'url': 'https://www.ertflix.gr/archeio/froytopia-s1-ep2/',
            'md5': 'e1be6b161d7a286db4ba2e45275fbfec',
            'info_dict': {
                'id': 'froytopia-s1-ep2',
                'ext': 'mp4',
                'title': 'Φρουτοπία Σ1:ΕΠ2',
                'uploader': 'contains:ΕΡΤ',
                'thumbnail': r're:^https?://www.ertflix.gr/.*\.(jpg|png)$',
                'description': 'contains:ΦΡΟΥΤΟΠΙΑ',
                'is_live': False,
                'season_number': 1,
                'episode_number': 2,
            }
        },
    )

    # Use non-greedy match qualifiers (+?, *?) where possible.
    __TITLE_RE = (
        r'<div[^>]+class="video-title"[^>]*>([^<]+)<',
        r'<title>(.+?)</title>',
    )
    __UPLOADER_RE = (
        r'<span[^>]+class="copy-right"[^>]*>[^-]+- ([^<]+)<',
        r'<span[^>]+class="copy-right"[^>]*>([^<]+)<',
    )
    __PLAYER_IFRAME_RE = (
        r'<div[^>]+id="player-embed"[^>]*>[^<]*<iframe[^>]+src="([^"]+)"',
    )
    __PLAYER_POSTER_RE = (
        r'poster\s*:\s*"([^"]+)"',
        r"poster\s*:\s*'([^']+)'",
    )
    __PLAYER_PLAYLIST_RE = (
        r"HLSLink\s*=\s*'([^']+\.m3u8)'",
        r'HLSLink\s*=\s*"([^"]+\.m3u8)"',
    )
    __META_ISLIVE_RE = (
        r"isLive'\s*:\s*(true|false)\s*,",
    )
    __META_EPISODE_RE = (
        r"\s*Σ(?P<season>\d+)\s*:ΕΠ(?P<episode>\d+)\s*",
        r"\s*S(?P<season>\d+)\s*:E(?P<episode>\d+)\s*",
    )

    def _real_extract(self, url):
        # video id and playlist url
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        player_iframe_url = self._search_regex(self.__PLAYER_IFRAME_RE, webpage, 'player url', fatal=True)
        playerpage = self._download_webpage(player_iframe_url, video_id)
        playlist_url = self._search_regex(self.__PLAYER_PLAYLIST_RE, playerpage, 'playlist url', fatal=True, flags=re.I)

        # additional metadata
        # see: https://github.com/ytdl-org/youtube-dl#output-template
        is_live = self._search_regex(self.__META_ISLIVE_RE, playerpage, 'live flag', default='', fatal=False, flags=re.I)
        is_live = True if is_live.lower() == 'true' else (False if is_live.lower() == 'false' else None)
        season_number = self._search_regex(self.__META_EPISODE_RE, webpage, 'season', default=None, fatal=False, flags=re.I, group='season')
        season_number = int(season_number) if season_number is not None else None
        episode_number = self._search_regex(self.__META_EPISODE_RE, webpage, 'episode', default=None, fatal=False, flags=re.I, group='episode')
        episode_number = int(episode_number) if episode_number is not None else None

        # description extract - if you can extract this with a single regex, I'll buy you a beer
        in_description = False
        description_html = ''
        description_ndiv = 0
        for l in webpage.splitlines():
            if not in_description:
                in_description = re.search(r'<div[^>]+class="video-the-content"', l) is not None
            if in_description:
                description_html += l
                description_ndiv += len(re.findall(r'<\s*div[\s>]', l))
                description_ndiv -= len(re.findall(r'<\s*/div[\s>]', l))
                if not description_ndiv > 0:
                    in_description = False
                    break

        # description cleanup
        description_html = re.sub(r'\s*>\s+', '>', description_html)
        description_html = re.sub(r'\s+<\s*', '<', description_html)
        description_html = re.sub(r'\s+', ' ', description_html)
        description_html = re.sub(r'<div>', '<p>', description_html)
        description_html = re.sub(r'</div>', '</p>', description_html)
        description = clean_html(description_html)

        data = {
            'id': video_id,
            'title': self._html_search_regex(self.__TITLE_RE, webpage, 'title'),
            'description': description,
            'uploader': self._html_search_regex(self.__UPLOADER_RE, webpage, 'uploader', fatal=False),
            'thumbnail': self._search_regex(self.__PLAYER_POSTER_RE, playerpage, 'thumbnail', fatal=False),
            'formats': self._extract_m3u8_formats(playlist_url, video_id, 'mp4', m3u8_id='hls', fatal=True),
            'is_live': is_live,
            'season_number': season_number,
            'episode_number': episode_number,
        }
        logging.error(data)

        return data

