import requests

from requests.exceptions import RequestException


HEADERS = {'user-agent': 'okhttp/3.12.1'}

PAYLOAD = {
		'sid': 5234053,
		'app_version': 95,
		'session_key': 1602722650,
		'uuid': 'UUID-aaa085b94a084d025a6e012f5da2dc07_5f8ee6ae90af37.91712457',
		'udid': 'UDID-Andorid-aaa085b94a084d025a6e012f5da2dc07_5f8ee6ae90afa0.20681458'
	}

class SpacetoonGo:
	def __init__(self):
		# self._url = ''
		self._headers = HEADERS.copy()
		self._data = {}
		self._all_series_data = []
		self._all_series = []
		self._payload = PAYLOAD.copy()


	def get_all_series(self, refresh=False):
		url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_all_tv_series'

		# return that cached one
		if refresh and self._all_series:
			return self._all_series

		# trying to get new series from Spacetoon servers.
		try:
			res = requests.post(url, data=self._payload, headers=self._headers)
			self._all_series_data = res.json()
			# print(json.dumps(res.json(), indent=2, sort_keys=True))
			return Serie.factory(self._all_series_data)
		except RequestException:
			print('Oops! Connection error')


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

		try:
			payload.update({'series_id': self.id})
			res = requests.post(url, data=payload, headers=HEADERS)

			self._ep_data = res.json()
			self._ep = Episode.factory(self._ep_data.get('episodes', []))
			return self._ep

		except RequestException:
			print('Oops! Connection error')



	@classmethod
	def factory(cls, series_json_date):
		return [ cls(serie) for serie in series_json_date ]


	def __getattr__(self, name):
		try:
			return self._data[name]
		except KeyError:
			raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

	def __repr__(self):
		return f"<Serie (id={self.id}, eps={self.ep_count})>"



class Episode:
	def __init__(self, json_data):
		self._data = json_data
		self._link_data = {}


	@property
	def cover(self):
		return self._data.get('cover_full_path')

	@property
	def title(self):
		return self._data.get('pref')

	@property
	def duration(self):
		return self._data.get('ep_duration')

	def get_stream_link(self):
		try:
			return self._link_data['link']
		except KeyError:
			pass

		url = 'https://spacetoongo.com/API/Mob/v3/ContentInfo/get_episode_link'
		payload = PAYLOAD.copy()

		try:
			payload.update({'epid': self.id})
			res = requests.post(url, data=payload, headers=HEADERS)

			self._link_data = res.json()
			return self._link_data.get('link')

		except RequestException:
			print('Oops! Connection error')

	def get_available_links(self):
		url = self.get_stream_link() # m3u8 file (contains different quality links)
		prefix_url = url.split('manifest.m3u8')[0]

		try:
			res = requests.get(url, headers=HEADERS)
			ls = res.text.split('\n')

			# parsing resolutions and links
			resolutions = [ line for line in ls if line.startswith('#') and 'RESOLUTION' in line ]
			resolutions = [ r.split(',')[-1].replace('RESOLUTION=', '') for r in resolutions ]


			links = [ prefix_url+line for line in ls if not line.startswith('#') and line != '' ]
			return list(zip(resolutions, links))

		except RequestException:
			print('Oops! Connection error')


	@classmethod
	def factory(cls, episodes_json_data):
		return [ cls(ep) for ep in episodes_json_data ]

	def __getattr__(self, name):
		try:
			return self._data[name]
		except KeyError:
			raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

	def __repr__(self):
		return f"<Episode (id={self.id}, number={self.number}, duration={self.ep_duration}, cost={self.cost})>"
