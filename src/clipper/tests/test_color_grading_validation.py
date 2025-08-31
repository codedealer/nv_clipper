import pytest

from clipper.ffmpeg_filter import _validate_color_grading_filter


@pytest.mark.parametrize(
    ("filter_str", "expected"),
    [
        ("hue=s=1.20:b=1:h=15", True),
        ("lutyuv=y=gammaval(0.769231)", True),
        (
            "lutyuv=y='min(max((val-(maxval+minval)/2)*1.15+(maxval+minval)/2,minval),maxval)'",
            True,
        ),
        (
            "hue=s=0.75:b=-2.5,hue=h=25:lutyuv=y=gammaval(1.25),lutyuv=y='min(max((val-(maxval+minval)/2)*0.85+(maxval+minval)/2,minval),maxval)'",
            True,
        ),
        # Legacy eq should still be accepted for backward compatibility
        ("eq=brightness=0.05:contrast=1.2:saturation=1.1:gamma=0.9", True),
        # Disallowed filter name
        ("scale=iw:ih", False),
        # Dangerous characters
        ("hue=s=1.1;b=1;echo hacked", False),
    ],
)
def test_validate_color_grading_filter(filter_str: str, expected: bool) -> None:
    assert _validate_color_grading_filter(filter_str) is expected
