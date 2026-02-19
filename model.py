import sys
from typing import Literal

from muscad import Cube, Cylinder, Union

from util import InvalidParameterException

if sys.platform == 'emscripten':
    # direct import is not possible, since we need to download the files manually
    includes = {
        "internal": "./internal.py",
        }
else:
    import internal

def generate(length: float, count: int, mode: Literal["centered", "offset"]) -> list[tuple[str, str]]:
    size = internal.size
    if count < 1:
        raise InvalidParameterException(["count"], "count must be at least 1")
    c1 = Cube(length, size, size)
    c2 = Union(*[Cylinder(h=length, d=size).y_rotate(90.0).align(center_y=i) for i in range(count)])
    if mode == "offset":
        c1 = c1.align(left=size)
        c2 = c2.align(left=size)
    return [
            ("cube", str(c1)),
            ("cylinder", str(c2))
            ]
