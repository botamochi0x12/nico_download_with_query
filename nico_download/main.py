import argparse
import json
from pathlib import Path
from typing import List, Tuple

import nndownload
import requests

ENDPOINT_URL = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"


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
            print(f"#DRYRUN# Download from url: {url}")
            return save_path

        if not overwrite and save_path.exists():
            raise RuntimeError(f"{save_path} already exists.")

        try:
            print(nndownload)
            nndownload.execute(
                "-u", self._uid, "-p", self._passwd, "-o", str(save_path), url
            )
        except Exception as e:
            print(e)
            raise RuntimeError()
        return save_path


def fetch_video_id(query: str, targets: str) -> List[Tuple[str, str]]:
    query_dict = {
        "q": query,
        "targets": targets,
        "fields": "contentId,title",
        "_sort": "startTime",
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
        "--outdir", type=str, default="./", help="output root directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="download action will not be actually performed",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite the mp4 file if existing."
    )
    args = parser.parse_args()

    params = {
        "q": "THE IDOLM@STER MillionRADIO",
        "targets": "title",
        "fields": "contentId,title",
        "_sort": "startTime",
    }
    res = requests.get(ENDPOINT_URL, params)

    response_dict = json.loads(res.text)
    movie_id = response_dict["data"][0]["contentId"]
    title = response_dict["data"][0]["title"]

    results = fetch_video_id(query="THE IDOLM@STER MillionRADIO", targets="title")
    save_root = Path("/mnt/c/Users/ayase/Downloads")

    with open("./passwd.json", "r") as f:
        settings = json.load(f)
    manager = DownloadManager(**settings)
    for movie_id, title in results:
        save_path = save_root / f"{title}.mp4"

        if save_path.exists() and not args.overwrite:
            raise RuntimeError(f"{save_path} already exists.")
        manager.download_video(movie_id, save_path, args.dry_run)


if __name__ == "__main__":
    main()
