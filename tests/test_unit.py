
import pytest

from d3s.units import SmartUnit


def test_smoke():
    small = SmartUnit(123, '', 'B')
    assert "{}".format(small) == "123B"
    assert "{:smart}".format(small) == "123B"

    large = SmartUnit(8192 * 1024, '', 'B')
    assert "{}".format(large) == "8388608B"
    assert "{:smart}".format(large) == "8MB"

@pytest.mark.parametrize("inp, expected", [
    ("123B", "123B"),
    ("4MB", "4194304B"),
])
def test_from_string(inp, expected):
    value = SmartUnit.from_string(inp)
    assert "{:base}".format(value) == expected
