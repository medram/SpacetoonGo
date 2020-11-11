# SpacetoonGo
A simple Spacetoon API for automating stuff instead of Spacetoon Go app using Python, (Not official API from Spacetoon).

# installation:
Install SpacetoonGo API from PyPi using terminal:
```Shell
$ pip install spacetoongo
```
Then setup these envirement variables in your terminal or put them in your .env file then load them using 'dotenv' package :
```Shell
SPACETOONGO_USER_ID=           # Your SpacetoonGo account id (required)
SPACETOONGO_APP_VERSION=95     # SpacetoonGo app version, the API is tested on v95 (required)
SPACETOONGO_SESSION_KEY=       # Your SpacetoonGo account session (optional)
SPACETOONGO_UUID=              # UUID of your phone (optional)
SPACETOONGO_UDID=              # UDID of your phone (optional)
```
The variable SPACETOONGO_USER_ID is very importent to be set.

## Notes:
- This API has the same permissions/privileges as your SpacetoonGo account has.
- You need a Premium SpacetoonGo account to be able to download tv-series & episodes.
- Make sure to connect from an Arabic country to get access to all SpacetoonGo tv-series.

# A simple docs:
```Python
sp = SpacetoonGo()

sp.series_count                   # count all tv series in SpacetoonGo app
sp.get_all_series(refresh=False)  # list all tv series
sp.get_favorite_series()          # list all favorite tv series on my account
sp.get_serie(serie_id)            # get a tv serie by its id


serie = ...

serie.id                          # tv serie id
serie.title                       # tv serie title
serie.ep_count                    # count tv serie episodes
serie.trailer_cover               # trailer cover image link
serie.cover                       # cover image link of the current tv serie
serie.get_episodes(refresh=False) # returns list of all episodes of the current tv serie
serie.get_episode(number)         # get tv serie episode by its number ( 1 <= number <= max-episodes )
serie.download_ep(number, dist, verbose=False)  # downloading an episode, ('dist' is a distination file)


ep = ...

ep.id
ep.title
ep.cover                          # cover image link of the current for episode
ep.duration                       # duration time of this episode
ep.serie                          # returns the serie Object of this episode

ep.main_stream_link(refresh=False)            # returns the main streaming link (.m3u8 file format),
                                              # not downloadable but streamable (use VLC to watch it directly)

ep.available_stream_links(refresh=False)      # returns a list of tuples [(resolution, link), ...]
ep.high_quality_stream_link(refresh=False)    # returns the high quality streaming link

ep.download(dist, link=None, verbose=False)   # downloading this episode with the high quality available,
                                              # To download a specific quality, pass to disired quality link
                                              # via 'link' paramiter
```
Note:
- Always leave 'refresh=False' parameter (which is the default and recommended) unless you want to make a new request to SpacetoonGo servers insead of caching, don't use this unless you have to.

# How to Use?:
These are some useful examples:

```Python
import os

from spacetoongo import SpacetoonGo

sp = SpacetoonGo()

# To list all tv series on SpacetoonGo app
for serie in sp.get_all_series():
	print(serie.title)
	print(serie)

# To list my account favorite tv series list
for serie in sp.get_favorite_series():
	print(serie.title)
	print(serie)
```

To download all episodes of a tv serie:
```Python
serie = sp.get_serie(393) # 393 is a tv serie id

for ep in serie.get_episodes():
	print(f'{serie.title} (episode: {ep.number}):')

	dist = os.path.abspath(f'files/{serie.id}_EP{ep.number}.mp4')
	ep.download(dist, verbose=True)

	print(f'[OK] Successfully downloaded to: {dist}\n')
```

To download a specific video quality of an episode:
```Python
ep = serie.get_episode(1)	# 1 means the first episode

# return a list of tuples (resolution, link)
quality_links = ep.available_stream_links()

# to see the available qualities
print(quality_links)

# to download this episode with a specific quality
dist = os.path.abspath(f'files/{serie.id}_EP{ep.number}.mp4')
ep.download(dist, link=quality_links[-1][1], verbose=True)
```

## Credits
I've grown with Spacetoon tv channel, I've watched the most of its tv-series (it was a Golden Age).
Special thanks to Spacetoon, its ambitions and whoever supports it 😁.

## License
MIT License
