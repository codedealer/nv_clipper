import pytest

from clipper import util
from clipper.clip_maker import getDefaultEncodeSettings
from clipper.clipper_types import ClipperPaths, ClipperState
from clipper.ytc_settings import disableVideoStreamingProtocols, getMoreVideoInfo
from clipper.yt_clipper import setupDepPaths
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


def test_setupDepPaths_uses_sibling_ff_tools_from_ytdl_location(tmp_path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    ytdl_path = bin_dir / "yt-dlp.exe"
    ffprobe_path = bin_dir / "ffprobe.exe"
    ffmpeg_path = bin_dir / "ffmpeg.exe"
    ffplay_path = bin_dir / "ffplay.exe"

    for tool_path in (ytdl_path, ffprobe_path, ffmpeg_path, ffplay_path):
        tool_path.write_text("", encoding="utf-8")

    monkeypatch.setattr("clipper.yt_clipper.shutil.which", lambda path: path)

    cs = ClipperState(settings={"ytdlLocation": str(ytdl_path)})

    setupDepPaths(cs)

    assert cs.clipper_paths.ytdlPath == str(ytdl_path).replace("\\", "/")
    assert cs.clipper_paths.ffprobePath == str(ffprobe_path).replace("\\", "/")
    assert cs.clipper_paths.ffmpegPath == str(ffmpeg_path).replace("\\", "/")
    assert cs.clipper_paths.ffplayPath == str(ffplay_path).replace("\\", "/")


def test_setupDepPaths_leaves_ffprobe_when_no_sibling_binary_exists(tmp_path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    ytdl_path = bin_dir / "yt-dlp.exe"
    ytdl_path.write_text("", encoding="utf-8")

    def fake_which(path: str) -> str | None:
        if path == str(ytdl_path):
            return path
        return None

    monkeypatch.setattr("clipper.yt_clipper.shutil.which", fake_which)

    cs = ClipperState(settings={"ytdlLocation": str(ytdl_path)})

    setupDepPaths(cs)

    assert cs.clipper_paths.ytdlPath == str(ytdl_path).replace("\\", "/")
    assert cs.clipper_paths.ffprobePath == "ffprobe"


# ---------------------------------------------------------------------------
# ffprobe fallback tests (getMoreVideoInfo with _probe_video_settings → None)
# ---------------------------------------------------------------------------

def _make_cs_for_fallback(**settings_overrides) -> ClipperState:
    """Create a minimal ClipperState suitable for getMoreVideoInfo tests."""
    base = {
        "inputVideo": "",
        "platform": "youtube",
        "videoDownloadURL": "https://example.com/video.mp4",
        "audioDownloadURL": "https://example.com/audio.mp4",
        "noRichLogs": True,
        "cropResWidth": 1920,
        "cropResHeight": 1080,
        "noAutoScaleCropRes": False,
        "videoTitle": "test-video",
    }
    base.update(settings_overrides)
    return ClipperState(settings=base)


class TestGetMoreVideoInfo_FfprobeFallback:
    """Tests for getMoreVideoInfo when ffprobe fails (_probe_video_settings → None)."""

    def test_successful_fallback_with_complete_ytdlp_metadata(self, monkeypatch):
        """When ffprobe fails but yt-dlp provides all fields, processing succeeds."""
        monkeypatch.setattr(
            "clipper.ytc_settings._probe_video_settings", lambda cs: None,
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "width": 1920,
            "height": 1080,
            "tbr": 5000,
            "fps": 30,
            "dynamic_range": "SDR",
        }

        getMoreVideoInfo(cs, video_info, video_info, "")

        assert cs.settings["width"] == 1920
        assert cs.settings["height"] == 1080
        assert cs.settings["bit_rate"] == 5000
        assert cs.settings["inputBitDepth"] == 8

    def test_fallback_missing_width_height_raises(self, monkeypatch):
        """When both ffprobe and yt-dlp lack width/height, a clear error is raised."""
        monkeypatch.setattr(
            "clipper.ytc_settings._probe_video_settings", lambda cs: None,
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "tbr": 3000,
            "fps": 24,
            "dynamic_range": "SDR",
        }

        with pytest.raises(RuntimeError, match="required properties.*width.*height"):
            getMoreVideoInfo(cs, video_info, video_info, "")

    def test_fallback_missing_bitrate_defaults_to_none(self, monkeypatch):
        """When bitrate is unavailable from both sources, bit_rate is set to None."""
        monkeypatch.setattr(
            "clipper.ytc_settings._probe_video_settings", lambda cs: None,
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "width": 1280,
            "height": 720,
            "fps": 60,
            "dynamic_range": "SDR",
        }

        getMoreVideoInfo(cs, video_info, video_info, "")

        assert cs.settings["bit_rate"] is None

    def test_fallback_hdr_bit_depth_inferred(self, monkeypatch):
        """When ffprobe fails, bit depth is inferred from yt-dlp dynamic_range."""
        monkeypatch.setattr(
            "clipper.ytc_settings._probe_video_settings", lambda cs: None,
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "width": 3840,
            "height": 2160,
            "tbr": 15000,
            "fps": 30,
            "dynamic_range": "HDR10",
        }

        getMoreVideoInfo(cs, video_info, video_info, "")

        assert cs.settings["inputBitDepth"] == 10

    def test_fallback_none_bitrate_defaults_to_none(self, monkeypatch):
        """When yt-dlp returns tbr=None, bit_rate falls back to None (constant-quality)."""
        monkeypatch.setattr(
            "clipper.ytc_settings._probe_video_settings", lambda cs: None,
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "width": 1920,
            "height": 1080,
            "tbr": None,
            "fps": 30,
            "dynamic_range": "SDR",
        }

        getMoreVideoInfo(cs, video_info, video_info, "")

        assert cs.settings["bit_rate"] is None

    @pytest.mark.parametrize(
        "video_info",
        [
            pytest.param({"width": None, "height": 1080, "fps": 30, "dynamic_range": "SDR"}, id="width-None"),
            pytest.param({"width": 1920, "height": None, "fps": 30, "dynamic_range": "SDR"}, id="height-None"),
            pytest.param({"width": None, "height": None, "fps": 30, "dynamic_range": "SDR"}, id="both-None"),
        ],
    )
    def test_fallback_none_width_height_raises(self, monkeypatch, video_info):
        """yt-dlp returning explicit None for width/height triggers RuntimeError."""
        monkeypatch.setattr(
            "clipper.ytc_settings._probe_video_settings", lambda cs: None,
        )
        cs = _make_cs_for_fallback()

        with pytest.raises(RuntimeError, match="required properties"):
            getMoreVideoInfo(cs, video_info, video_info, "")

    def test_missing_ffprobe_binary_uses_ytdlp_fallback(self, monkeypatch):
        """A missing ffprobe executable should not abort yt-dlp-backed processing."""
        monkeypatch.setattr(
            "clipper.ffprobe.subprocess.check_output",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                FileNotFoundError(2, "The system cannot find the file specified"),
            ),
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "width": 3840,
            "height": 2160,
            "tbr": 12000,
            "fps": 30,
            "dynamic_range": "SDR",
        }

        getMoreVideoInfo(cs, video_info, video_info, "")

        assert cs.settings["width"] == 3840
        assert cs.settings["bit_rate"] == 12000

    def test_missing_ffprobe_binary_reports_actionable_error_when_fallback_insufficient(self, monkeypatch):
        """If ffprobe is unavailable and yt-dlp metadata is insufficient, raise a useful error."""
        monkeypatch.setattr(
            "clipper.ffprobe.subprocess.check_output",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                FileNotFoundError(2, "The system cannot find the file specified"),
            ),
        )
        cs = _make_cs_for_fallback()
        video_info = {
            "tbr": 12000,
            "fps": 30,
            "dynamic_range": "SDR",
        }

        with pytest.raises(RuntimeError, match="ffprobe failure details: Could not start ffprobe"):
            getMoreVideoInfo(cs, video_info, video_info, "")


class TestGetDefaultEncodeSettings_NullBitrate:
    """Ensure getDefaultEncodeSettings handles None bitrate (constant-quality fallback)."""

    def test_none_bitrate_returns_constant_quality(self):
        result = getDefaultEncodeSettings(None)
        assert result["crf"] == 30
        assert result["autoTargetMaxBitrate"] == 0
        assert result["twoPass"] is False

    def test_none_bitrate_times_factor_passthrough(self):
        """Simulates the clip_maker guard: None * factor should not be called."""
        bit_rate = None
        factor = 0.8
        adjusted = bit_rate * factor if bit_rate is not None else None
        result = getDefaultEncodeSettings(adjusted)
        assert result["crf"] == 30
        assert result["autoTargetMaxBitrate"] == 0
