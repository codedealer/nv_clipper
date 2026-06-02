from __future__ import annotations

from dataclasses import dataclass

import numpy as np

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
        self.stdin = _FakeStream()
        self.returncode = 0

    def wait(self) -> int:
        return self.returncode


def test_extract_video_frames_tokenizes_ffmpeg_command(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_popen(args, stdout=None, bufsize=None):
        captured["args"] = args
        captured["stdout"] = stdout
        captured["bufsize"] = bufsize
        return _FakeProcess()

    monkeypatch.setattr("clipper.rife_interpolation.Popen", fake_popen)

    extract_video_frames(
        "ffmpeg -headers 'User-Agent: Mozilla/5.0\r\nAccept: text/html\r\n' -i input.mkv",
    )

    assert isinstance(captured["args"], list)
    assert captured["args"][1] == "-headers"
    assert captured["args"][2].endswith("\r\n")


def test_pipe_frames_to_ffmpeg_tokenizes_ffmpeg_command(monkeypatch) -> None:
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

    def fake_popen(args, stdin=None):
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