import os
import tempfile
import requests

from tqdm import tqdm
from concurrent import futures


class DownloadManager:
    def __init__(self, url, buffer_size=1024, verbose=False):
        self._url = url
        self._prefix_url = self._url.split('.smil/')[0] + '.smil/'
        self._ts_links = self.parse_ts_links()
        self._junk_files = []
        self._buffer_size = buffer_size  # in bytes
        self._verbose = verbose

    def parse_ts_links(self):
        try:
            res = requests.get(self._url)
            lines = res.text.split('\n')
            self._ts_links = [self._prefix_url +
                              line for line in lines if not line.startswith('#') and line != '' and '.ts' in line]
            return self._ts_links
        except requests.exceptions.RequestException:
            print('Oops! Connection error')

    def get_ts_links(self):
        return self._ts_links

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        # print('clean up junk')
        for junk in self._junk_files:
            try:
                os.remove(junk)
            except OSError:
                pass

    # dist is a distination file
    def download_and_save(self, dist, buffer_size=None):

        if not os.path.isdir(os.path.dirname(dist)):
            raise NotADirectoryError(f"'{dist}' is not a directory")
        # if os.path.isfile(dist):
        #     raise FileExistsError(f"'{dist}' is a file, and it's shouldn't be")

        if buffer_size is None:
            buffer_size = self._buffer_size

        # this temp folder will be remove with its files one we get out from this function.
        tempdir = tempfile.TemporaryDirectory(prefix='spacetoon.')
        chunk_paths = self._download_ts_files(tempdir)
        self._merge_ts_files(dist, chunk_paths)
        # add files to junk to remove it later in __exit__ function.
        self._junk_files.extend(chunk_paths)

    def _download_ts_files(self, tempdir, buffer_size=None):
        # print(f'Downloading ({len(self.get_ts_links())}) ts files')

        if buffer_size is None:
            buffer_size = self._buffer_size

        chunk_paths = {}
        with futures.ThreadPoolExecutor() as executor:
            futures_list = {executor.submit(
                self.download, link, tempfile.mkstemp(dir=tempdir.name)[1], buffer_size): link for link in self.get_ts_links()}

            with tqdm(total=len(futures_list), desc='Downloading...', ascii=True, leave=False,
                      dynamic_ncols=True,
                      disable=not self._verbose,
                      bar_format="{desc}({percentage:6.02f}%): [{bar}] remaining: {remaining} "
                      ) as pbar:

                for future in futures.as_completed(futures_list):
                    try:
                        link = futures_list[future]
                        # returns path of downloaded chunk.
                        chunk_paths.update({link: future.result()})
                        pbar.update(1)
                    except Exception as e:
                        print(e)

            # sorting chunks in correct order
        return [chunk_paths[l] for l in self.get_ts_links()]

    def _merge_ts_files(self, dist, chunk_paths, buffer_size=None):
        # print('Merging ts files')
        if buffer_size is None:
            buffer_size = self._buffer_size

        with tqdm(total=len(chunk_paths), desc='Coping...', ascii=True,
                  # leave=False,
                  dynamic_ncols=True,
                  unit='chunk',
                  disable=not self._verbose,
                  bar_format="{desc}({percentage:6.02f}%): [{bar}] remaining: {remaining} "
                  ) as pbar:

            with open(dist, 'wb') as video:
                for file in chunk_paths:
                    with open(file, 'rb') as f:
                        chunk = f.read(buffer_size)
                        while chunk:
                            video.write(chunk)
                            chunk = f.read(buffer_size)
                    pbar.update(1)

    @staticmethod
    def download(url, save_to=None, buffer_size=None):
        # print(f'[Downloding]...{url}')
        if save_to is None:
            save_to = tempfile.mkstemp()[1]

        if buffer_size is None:
            buffer_size = self._buffer_size

        while True:
            try:
                res = requests.get(url, stream=True)
                with open(save_to, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=buffer_size):
                        f.write(chunk)
                return save_to
            except requests.exceptions.RequestException:
                pass
            except IOError:
                raise
