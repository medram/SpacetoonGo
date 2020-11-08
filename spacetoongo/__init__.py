import os
import requests

from functools import reduce
from dotenv import load_dotenv
from requests.exceptions import RequestException

from . import utils

# load envirement variables from .env file.
load_dotenv()

HEADERS = {'user-agent': 'okhttp/3.12.1'}

PAYLOAD = {
    'sid': os.getenv('sid'),
    'app_version': os.getenv('app_version'),
    'session_key': os.getenv('session_key'),
    'uuid': os.getenv('uuid'),
    'udid': os.getenv('udid')
}


class SpacetoonGo:
    def __init__(self):
        # self._url = ''
        self._headers = HEADERS.copy()
        self._payload = PAYLOAD.copy()
        self._data = {}
        self._all_series_data = []
        self._all_series = []

    def get_all_series(self, refresh=False):
        url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_all_tv_series'

        # return that cached one
        if refresh and self._all_series:
            return self._all_series

        # trying to get new series from Spacetoon servers.
        res = requests.post(url, data=self._payload, headers=self._headers)

        self._all_series_data = res.json()
        # print(json.dumps(res.json(), indent=2, sort_keys=True))
        return Serie.factory(self._all_series_data)

    def check_account(self):
        pass

    def get_favorite_series(self):
        pass


class Serie:
    def __init__(self, json_data):
        self._data = json_data
        self._ep_data = []
        self._ep = []

    @property
    def title(self):
        return self._data.get('name')

    @property
    def cover(self):
        return self._data.get('cover_full_path')

    @property
    def trailer_cover(self):
        return self._data.get('trailer_cover_full_path')

    @property
    def ep_count(self):
        return self._data.get('ep_count')

    def get_episodes(self, refresh=False):
        if refresh and self._ep:
            return self._ep

        url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_episodes_by_tv_series'
        payload = PAYLOAD.copy()

        payload.update({'series_id': self.id})
        res = requests.post(url, data=payload, headers=HEADERS)

        self._ep_data = res.json()
        self._ep = Episode.factory(self._ep_data.get('episodes', []))
        return self._ep

    @classmethod
    def factory(cls, series_json_date):
        return [cls(serie) for serie in series_json_date]

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self):
        return f"<Serie (id={self.id}, eps={self.ep_count})>"


class Episode:
    def __init__(self, json_data):
        self._data = json_data
        self._link_data = {}
        self._available_stream_links = []

    @property
    def cover(self):
        return self._data.get('cover_full_path')

    @property
    def title(self):
        return self._data.get('pref')

    @property
    def duration(self):
        return self._data.get('ep_duration')

    def main_stream_link(self):
        try:
            return self._link_data['link']
        except KeyError:
            pass

        url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_episode_link'
        payload = PAYLOAD.copy()

        payload.update({'epid': self.id})
        res = requests.post(url, data=payload, headers=HEADERS)

        self._link_data = res.json()
        return self._link_data.get('link')

    def available_stream_links(self, refresh=False):
        if refresh and self._available_stream_links:
            return self._available_stream_links

        url = self.main_stream_link()  # m3u8 file (contains different quality links)
        prefix_url = url.split('manifest.m3u8')[0]

        res = requests.get(url, headers=HEADERS)
        ls = res.text.split('\n')

        # parsing resolutions and links
        resolutions = [line for line in ls if line.startswith(
            '#') and 'RESOLUTION' in line]
        resolutions = [r.split(',')[-1].replace('RESOLUTION=', '')
                       for r in resolutions]

        links = [
            prefix_url + line for line in ls if not line.startswith('#') and line != '']
        self._available_stream_links = list(zip(resolutions, links))

        return self._available_stream_links

    def high_quality_stream_link(self):
        max_resolution = 0
        high_quality_link = ''
        for key, value in self.available_stream_links():
            # list of int (like [1080, 720])
            tmp = map(int, key.lower().split('x'))
            tmp = reduce(lambda x, y: x * y, tmp)  # retult of 1080*720
            if tmp > max_resolution:
                max_resolution = tmp
                high_quality_link = value
        return high_quality_link

    def download(self, dist, link=None):
        # download the max resolution video (high quality)
        if link is None:
            link = self.high_quality_stream_link()

        # downloading in parallel & save the video to distination.
        with utils.DownloadManager(link) as dm:
            dm.download_and_save(os.path.abspath(dist))

    @classmethod
    def factory(cls, episodes_json_data):
        return [cls(ep) for ep in episodes_json_data]

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self):
        return f"<Episode (id={self.id}, number={self.number}, duration={self.ep_duration}, cost={self.cost})>"
