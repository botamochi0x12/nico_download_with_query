import json
from pathlib import Path
from typing import List, Tuple

import nndownload
import requests

from nico_download.exceptions import FileExistsError
from nico_download.logger import get_logger

ENDPOINT_URL = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"

logger = get_logger(__name__)


class DownloadManager(object):
    movie_url_prefix = "https://www.nicovideo.jp/watch/"

    def __init__(self, uid: str, passwd: str):
        self._uid = uid
        self._passwd = passwd

    def download_video(
        self,
        video_id: str,
        save_path: Path,
        overwrite: bool = False,
        dry_run: bool = False,
    ) -> Path:
        url = self.movie_url_prefix + str(video_id)
        if dry_run:
            logger.info(f"DRYRUN: Download from url: {url} to {save_path}")
            return save_path

        logger.debug(f"Start download from {url}, save to {save_path}")
        if save_path.exists():
            if not overwrite:
                mes = f"{save_path} already exists."
                logger.critical(mes)
                raise FileExistsError(mes)
            else:
                logger.warning(
                    f"File {save_path} already exists, but overwrite flag is set."
                )
                logger.warning("Continue to download.")

        try:
            nndownload.execute(
                "-u", self._uid, "-p", self._passwd, "-o", str(save_path), url
            )
        except Exception as e:
            logger.critical("Something wrong happened in nndownload.execute()")
            logger.critical(str(e))
            raise RuntimeError()
        return save_path


def fetch_video_id(
    query: str, targets: str, max_videos: int = 100
) -> List[Tuple[str, str]]:
    query_dict = {
        "q": query,
        "targets": targets,
        "fields": "contentId,title",
        "_sort": "-startTime",
        "_limit": str(max_videos),
    }
    logger.debug(f"{query_dict=}")
    res = requests.get(ENDPOINT_URL, query_dict)

    response_dict = json.loads(res.text)
    logger.debug(f"{response_dict=}")
    return_value: List[Tuple[str, str]] = []
    for data in response_dict["data"]:
        movie_id = data["contentId"]
        title = data["title"]
        return_value.append((movie_id, title))
    logger.debug(f"{return_value=}")
    return return_value
