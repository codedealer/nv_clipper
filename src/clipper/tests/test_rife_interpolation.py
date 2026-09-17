from __future__ import annotations

from dataclasses import dataclass
from subprocess import DEVNULL

import numpy as np
import pytest

from clipper.rife_interpolation import extract_video_frames, pipe_frames_to_ffmpeg


@dataclass
class _FakeStream:
    data: bytes = b""

    def readable(self) -> bool:
        return True

    def read(self, _size: int = -1) -> bytes:
        return self.data

    def close(self) -> None:
        return None


class _FakeProcess:
    def __init__(self) -> None:
        self.stdout = _FakeStream()
        self.stderr = None
        self.stdin = _FakeStream()
        self.returncode = 0

    def wait(self) -> int:
        return self.returncode


def test_extract_video_frames_tokenizes_ffmpeg_command(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_popen(
        args: list[str],
        stdout: object | None = None,
        stderr: object | None = None,
        bufsize: int | None = None,
    ) -> _FakeProcess:
        captured["args"] = args
        captured["stdout"] = stdout
        captured["stderr"] = stderr
        captured["bufsize"] = bufsize
        return _FakeProcess()

    monkeypatch.setattr("clipper.rife_interpolation.Popen", fake_popen)

    extract_video_frames(
        "ffmpeg -headers 'User-Agent: Mozilla/5.0\r\nAccept: text/html\r\n' -i input.mkv",
    )

    assert isinstance(captured["args"], list)
    assert captured["args"][1] == "-headers"
    assert captured["args"][2].endswith("\r\n")
    assert captured["stderr"] is DEVNULL


def test_pipe_frames_to_ffmpeg_tokenizes_ffmpeg_command(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeStdin:
        def write(self, _data: bytes) -> None:
            return None

        def close(self) -> None:
            return None

    class FakeProcess:
        def __init__(self) -> None:
            self.stdin = FakeStdin()
            self.returncode = 0

        def wait(self) -> int:
            return self.returncode

    def fake_popen(args: list[str], stdin: object | None = None) -> FakeProcess:
        captured["args"] = args
        captured["stdin"] = stdin
        return FakeProcess()

    monkeypatch.setattr("clipper.rife_interpolation.Popen", fake_popen)

    frames = [np.zeros((2, 2, 3), dtype=np.uint8)]
    pipe_frames_to_ffmpeg(
        frames,
        "ffmpeg -headers 'User-Agent: Mozilla/5.0\r\nAccept: text/html\r\n' -i - <__RIFE_placeholder>",
    )

    assert isinstance(captured["args"], list)
    assert captured["args"][1] == "-headers"
    assert captured["args"][2].endswith("\r\n")


def test_extract_video_frames_decodes_png_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    import cv2

    success, encoded = cv2.imencode(".png", np.zeros((2, 3, 3), dtype=np.uint8))
    assert success

    class OnceStream(_FakeStream):
        def __init__(self, data: bytes) -> None:
            super().__init__(data)
            self.consumed = False

        def read(self, _size: int = -1) -> bytes:
            if self.consumed:
                return b""
            self.consumed = True
            return self.data

    class PngProcess:
        def __init__(self) -> None:
            self.stdout = OnceStream(encoded.tobytes())
            self.stderr = None
            self.returncode = 0

        def wait(self) -> int:
            return self.returncode

    monkeypatch.setattr("clipper.rife_interpolation.Popen", lambda *args, **kwargs: PngProcess())

    frames = extract_video_frames("ffmpeg -f image2pipe -vcodec png -")

    assert len(frames) == 1
    assert frames[0].shape == (2, 3, 3)