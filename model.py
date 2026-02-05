from typing import Literal

from muscad import Cube, Cylinder, Union

from openswebcad import InvalidParameterException

def generate(length: float, count: int, mode: Literal["centered", "offset"]) -> list[tuple[str, str]]:
    if count < 1:
        raise InvalidParameterException(["count"], "count must be at least 1")
    c1 = Cube(length, 10.0, 10.0)
    c2 = Union(*[Cylinder(h=length, d=10.0).y_rotate(90.0).align(center_y=i) for i in range(count)])
    if mode == "offset":
        c1 = c1.align(left=5.0)
        c2 = c2.align(left=5.0)
    return [
            ("cube", str(c1)),
            ("cylinder", str(c2))
            ]
