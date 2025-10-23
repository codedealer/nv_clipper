import base64
import hashlib
import re
from importlib import util as importlib_util
from typing import Any, Dict, Union


def is_module_available(mod: str) -> bool:
    return importlib_util.find_spec(mod) is not None


def dictTryGetKeys(d: Dict, *keys: str, default: Any = None) -> Any:  # noqa: ANN401
    for key in keys:
        value = d.get(key)
        if value is not None:
            return value

    return default


def notifyOnComplete(titleSuffix: str) -> None:
    from notifypy import Notify

    n = Notify()
    n.application_name = "yt_clipper"
    n.title = "yt_clipper Completed Run"
    n.message = f"Processed {titleSuffix}.json."
    n.send(block=False)


def getTrimmedBase64Hash(string: str, n_bytes: int = 9) -> str:
    hash_object = hashlib.sha256(string.encode(encoding="utf-8", errors="replace"))
    hex_dig = hash_object.digest()[:n_bytes]
    return base64.b64encode(hex_dig).decode("ascii")


def escapeSingleQuotesFFmpeg(string: str) -> str:
    return re.sub(r"'", r"'\\''", string)


def floorToEven(x: Union[int, str, float]) -> int:
    x = int(x)
    return x & ~1

def escapeBracketsFFmpeg(string: str) -> str:
    """Escape square brackets within quoted segments for FFmpeg filters.

    FFmpeg interprets unescaped brackets as stream labels. We only escape
    brackets that appear inside quoted substrings (single or double quotes),
    which is where file paths and other literals reside. Brackets that denote
    actual stream labels are left untouched so filter graphs continue to work.
    """

    escaped: list[str] = []
    in_single = False
    in_double = False
    prev_char = ""

    for ch in string:
        if ch == "'" and not in_double and prev_char != "\\":
            in_single = not in_single
            escaped.append(ch)
        elif ch == '"' and not in_single and prev_char != "\\":
            in_double = not in_double
            escaped.append(ch)
        elif ch in "[]" and (in_single or in_double):
            escaped.append("\\" + ch)
        else:
            escaped.append(ch)

        prev_char = ch

    return "".join(escaped)