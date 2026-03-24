import pytest

from clipper import util
from clipper.clipper_types import ClipperPaths, ClipperState
from clipper.ytc_settings import disableVideoStreamingProtocols
from clipper.ytdl import ytdl_bin_get_args_base


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param("", "", id="empty string"),
        ("non-empty", "non-empty"),
        ("'squoted'", r"'\''squoted'\''"),
    ],
)
def test_escapeSingleQuotesFFmpeg(test_input: str, expected: str) -> None:
    assert expected == util.escapeSingleQuotesFFmpeg(test_input)


def test_disableVideoStreamingProtocols_uses_filter_only_selector_when_unset() -> None:
    settings = {"format": ""}

    disableVideoStreamingProtocols(settings, ["m3u8", "m3u8_native"])

    assert settings["format"] == "[protocol!=m3u8][protocol!=m3u8_native]"


def test_disableVideoStreamingProtocols_preserves_custom_format() -> None:
    settings = {"format": " best/bv+ba "}

    disableVideoStreamingProtocols(settings, ["m3u8"])

    assert settings["format"] == "(best/bv+ba)[protocol!=m3u8]"


def test_ytdl_bin_get_args_base_skips_blank_format_inputs() -> None:
    cs = ClipperState(
        settings={
            "format": "   ",
            "formatSort": ["", "   "],
            "downloadVideoPath": "./video",
            "cookiefile": "",
            "username": "",
            "password": "",
        },
        clipper_paths=ClipperPaths(ytdlPath="yt-dlp"),
    )

    ytdl_args = ytdl_bin_get_args_base(cs)

    assert "--format" not in ytdl_args
    assert "--format-sort" not in ytdl_args


def test_ytdl_bin_get_args_base_normalizes_format_inputs() -> None:
    cs = ClipperState(
        settings={
            "format": " best/bv+ba ",
            "formatSort": [" ", "res,fps", "proto"],
            "downloadVideoPath": "./video",
            "cookiefile": "",
            "username": "",
            "password": "",
        },
        clipper_paths=ClipperPaths(ytdlPath="yt-dlp"),
    )

    ytdl_args = ytdl_bin_get_args_base(cs)

    assert "--format" in ytdl_args
    assert "best/bv+ba" in ytdl_args
    assert "--format-sort" in ytdl_args
    assert "res,fps,proto" in ytdl_args
