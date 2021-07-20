import argparse
import json
import logging
from pathlib import Path
from typing import List, Tuple

import nndownload
import requests
import toml

from nico_download.logger import get_logger, get_verbosity, set_verbosity

ENDPOINT_URL = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"

print(__name__)
logger = get_logger(__name__)


class FileExistsError(Exception):
    pass


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
            logger.info(f"#DRYRUN# Download from url: {url} to {save_path}")
            return save_path

        if not overwrite and save_path.exists():
            raise FileExistsError(f"{save_path} already exists.")

        try:
            nndownload.execute(
                "-u", self._uid, "-p", self._passwd, "-o", str(save_path), url
            )
        except Exception as e:
            print(e)
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
    res = requests.get(ENDPOINT_URL, query_dict)

    response_dict = json.loads(res.text)
    return_value: List[Tuple[str, str]] = []
    for data in response_dict["data"]:
        movie_id = data["contentId"]
        title = data["title"]
        return_value.append((movie_id, title))
    return return_value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="./config.toml",
        help="config json path, see passwd.json.example",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="download action will not be actually performed",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="set log level to DEBUG",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite the mp4 file if existing."
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    set_verbosity(log_level)

    with open(args.config, "r") as f:
        config = toml.load(f)

    manager = DownloadManager(uid=config["uid"], passwd=config["passwd"])
    limit = config["limit"]
    for query in config["queries"]:
        results = fetch_video_id(
            query=query["query"], targets=query["target"], max_videos=limit
        )
        print(results)
        savedir = Path(config["saveroot"])
        if len(query["subdir"]) > 0:
            savedir = savedir / query["subdir"]

        for movie_id, title in results:
            save_path = savedir / f"{title}.mp4"
            try:
                manager.download_video(
                    movie_id, save_path, args.overwrite, args.dry_run
                )
            except FileExistsError as e:
                print(e)


if __name__ == "__main__":
    main()
