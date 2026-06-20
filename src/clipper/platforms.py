import os
import shlex
import sys
from typing import Any, Mapping

from clipper.clipper_types import KnownPlatform, Settings
from clipper.ytc_logger import logger


def _get_platform_headers(platform: str) -> dict[str, str]:
    if platform == KnownPlatform.afreecatv.name:
        return {
            "Referer": "https://play.afreecatv.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0",
        }

    return {}


def getFfmpegHeaders(platform: str, extra_headers: Mapping[str, Any] | None = None) -> str:
    merged_headers: dict[str, tuple[str, str]] = {
        name.lower(): (name, value)
        for name, value in _get_platform_headers(platform).items()
        if isinstance(name, str) and isinstance(value, str) and name and value
    }

    if extra_headers:
        for name, value in extra_headers.items():
            if not isinstance(name, str) or not isinstance(value, str):
                continue
            header_name = name.strip()
            header_value = " ".join(value.split())
            if not header_name or not header_value:
                continue
            merged_headers[header_name.lower()] = (header_name, header_value)

    if not merged_headers:
        return ""

    header_block = "\r\n".join(f"{name}: {value}" for name, value in merged_headers.values())
    return f"-headers {shlex.quote(f'{header_block}\r\n')}"


def getVideoPageURL(settings: Settings, platform: str, videoID: str) -> str:
    if platform == KnownPlatform.youtube.name:
        return f"https://www.youtube.com/watch?v={videoID}"
    if platform == KnownPlatform.vlive.name:
        return f"https://www.vlive.tv/video/{videoID}"
    if platform == KnownPlatform.naver_now_watch.name:
        return f"https://now.naver.com/watch/{videoID}"
    if platform == KnownPlatform.weverse.name:
        return settings["videoUrl"]
    if platform == KnownPlatform.naver_tv.name:
        return f"https://tv.naver.com/v/{videoID}"
    if platform == KnownPlatform.afreecatv.name:
        return settings["videoUrl"]
    if platform == KnownPlatform.ytc_generic.name:
        if settings["inputVideo"]:
            return "unknown_video_url_for_input_video"
        logger.warning("Video page URL not found and no local input video was provided.")
        logger.warning(
            "Enter a video page URL at the prompt below OR rerun with an input video (e.g. by using the input video helper script).",
        )
        videoPageUrl = input("Please enter a compatible video page URL for processing markers: ")
        if videoPageUrl:
            return videoPageUrl

        logger.fatal(f"Neither video page URL nor input video provided.")
        if os.environ.get("YTC_GUI_WORKER") == "1":
            raise ValueError("Missing video page URL and input video")
        sys.exit(1)

    logger.fatal(f"Unknown platform: {platform}")
    if os.environ.get("YTC_GUI_WORKER") == "1":
        raise ValueError(f"Unknown platform: {platform}")
    sys.exit(1)
