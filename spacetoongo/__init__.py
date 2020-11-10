import os
import requests

from functools import reduce
from dotenv import load_dotenv

from .exceptions import AccountPermissionError, EpisodeNotFound
from . import utils

# load envirement variables from .env file.
load_dotenv()

__version__ = '0.0.2-alpha.3'


HEADERS = {'user-agent': 'okhttp/3.12.1'}

PAYLOAD = {
    'sid': os.getenv('SPACETOONGO_USER_ID'),
    'app_version': os.getenv('SPACETOONGO_APP_VERSION'),
    'session_key': os.getenv('SPACETOONGO_SESSION_KEY'),
    'uuid': os.getenv('SPACETOONGO_UUID'),
    'udid': os.getenv('SPACETOONGO_UDID')
}


class SpacetoonGo:
    def __init__(self):
        self._headers = HEADERS.copy()
        self._payload = PAYLOAD.copy()
        self._data = {}
        self._all_series_data = []
        self._all_series = []
        self._all_fav_series = []

    def get_all_series(self, refresh=False):
        # return that cached one
        if not refresh and self._all_series:
            return self._all_series
        return self._get_all_series(refresh)

    def _get_all_series(self, refresh=False):
        url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_all_tv_series'
        # trying to get new series from Spacetoon servers.
        res = requests.post(url, data=self._payload, headers=self._headers)

        self._all_series_data = res.json()
        self._all_series = Serie.Factory(self._all_series_data)
        # print(json.dumps(res.json(), indent=2, sort_keys=True))
        return self._all_series

    @property
    def series_count(self):
        return len(self.get_all_series())

    def get_serie(self, serie_id):
        serie_id = int(serie_id)
        for serie in self.get_all_series():
            if serie.id == serie_id:
                return serie

    def get_favorite_series(self):
        if self._all_fav_series:
            return self._all_fav_series

        url = 'https://spacetoongo.com/API/Mob/v3/Interaction/get_my_fav_list'
        # trying to get new series from Spacetoon servers.
        res = requests.post(url, data=self._payload, headers=self._headers)

        fav_ids = (int(item['id']) for item in res.json())
        self._all_fav_series = [self.get_serie(id_) for id_ in fav_ids]
        return self._all_fav_series


class Serie:
    def __init__(self, json_data):
        self._data = json_data
        self._ep_data = []
        self._ep = []

    @property
    def id(self):
        return int(self._data.get('id'))

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
        """To count length of a generator use this "sum(1 for _ in self.get_episodes())",
        for list use this "len(self._ep)" is not working
        """
        return int(self._data.get('ep_count'))

    def get_episodes(self, refresh=False):
        if not refresh and self._ep:
            return self._ep

        url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_episodes_by_tv_series'
        payload = PAYLOAD.copy()

        payload.update({'series_id': self.id})
        res = requests.post(url, data=payload, headers=HEADERS)

        self._ep_data = res.json()
        self._ep = Episode.Factory(self, self._ep_data.get('episodes', []))
        return self._ep

    def get_episode(self, number):
        try:
            return self.get_episodes()[number - 1]
        except IndexError:
            raise EpisodeNotFound(
                f"Oops! Episode '{number}' not found, its tv serie has {self.ep_count} episodes to choose from.")

            # dist is a file path
    def download_ep(self, number, dist, verbose=False):
        ep = self.get_episode(number)
        ep.download(dist, verbose=verbose)

    @classmethod
    def Factory(cls, series_json_date):
        return [cls(serie) for serie in series_json_date]

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self):
        return f"<Serie (id={self.id}, ep_count={self.ep_count}, rate={self.rate}, is_movie={self.is_movie}, planet={self.planet}, cost={self.cost})>"


class Episode:
    def __init__(self, serie, json_data):
        self._data = json_data
        self._link_data = {}
        self._available_stream_links = []
        self.serie = serie

    @property
    def cover(self):
        return self._data.get('cover_full_path', '')

    @property
    def title(self):
        return self._data.get('pref', '')

    @property
    def duration(self):
        return self._data.get('ep_duration')

    def main_stream_link(self, refresh=False):
        try:
            if not refresh and self._link_data['link'] is not None:
                return self._link_data['link']
        except KeyError:
            pass

        url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_episode_link'
        payload = PAYLOAD.copy()

        payload.update({'epid': self.id})
        res = requests.post(url, data=payload, headers=HEADERS)

        self._link_data = res.json()
        if self._link_data['link'] is not None:
            return self._link_data['link']
        else:
            raise AccountPermissionError

    def available_stream_links(self, refresh=False):
        if not refresh and self._available_stream_links:
            return self._available_stream_links
        try:
            url = self.main_stream_link(refresh=refresh)  # m3u8 file (contains different quality links)
        except Exception:
            raise
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

    def high_quality_stream_link(self, refresh=False):
        max_resolution = 0
        high_quality_link = ''
        try:
            for key, value in self.available_stream_links(refresh=refresh):
                # list of int (like [1080, 720])
                tmp = map(int, key.lower().split('x'))
                tmp = reduce(lambda x, y: x * y, tmp)  # retult of 1080*720
                if tmp > max_resolution:
                    max_resolution = tmp
                    high_quality_link = value
            return high_quality_link
        except Exception:
            raise

    def download(self, dist, link=None, verbose=False):
        # download the max resolution video (high quality)
        if link is None:
            try:
                link = self.high_quality_stream_link()
            except:
                raise
        # downloading in parallel & save the video to distination.
        with utils.DownloadManager(link, verbose=verbose) as dm:
            dm.download_and_save(os.path.abspath(dist))
        return dist

    @classmethod
    def Factory(cls, serie, episodes_json_data):
        return [cls(serie, ep) for ep in episodes_json_data]

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self):
        return f"<Episode (id={self.id}, number={self.number}, duration={self.ep_duration}, cost={self.cost})>"
