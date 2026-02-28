from typing import Literal

import pytest

from parse import parse_parameters as p, NumericParameter, ChoiceParameter, InvalidParameterAnnotation

def test_no_params():
    def f():
        return []
    assert p(f) == []

def test_three_params():
    def f(a: int, b: float, c: Literal["c1", "c2"]):
        return []

    assert p(f) == [
            NumericParameter(name="a", description="a", t=int, default=None),
            NumericParameter(name="b", description="b", t=float, default=None),
            ChoiceParameter(name="c", description="c", choices=["c1", "c2"], default=None),
            ]
def test_three_params_with_default():
    def f(a: int=3, b: float=4.0, c: Literal["c1", "c2"]="c2"):
        return []

    assert p(f) == [
            NumericParameter(name="a", description="a", t=int, default=3),
            NumericParameter(name="b", description="b", t=float, default=4.0),
            ChoiceParameter(name="c", description="c", choices=["c1", "c2"], default="c2"),
            ]

def assert_invalid(f):
    with pytest.raises(InvalidParameterAnnotation):
        p(f)


def test_invalid_default_int():
    def f(a: int=3.0):
        pass
    def g(a: int="bla"):
        pass
    assert_invalid(f)
    assert_invalid(g)

def test_invalid_default_float():
    def f(a: float=3):
        pass
    def g(a: float="bla"):
        pass
    assert_invalid(f)
    assert_invalid(g)

def test_invalid_default_choice():
    def f(a: Literal["x", "y"]=3):
        pass
    def g(a: Literal["x", "y"]=3.0):
        pass
    def h(a: Literal["x", "y"]="a"):
        pass
    assert_invalid(f)
    assert_invalid(g)
    assert_invalid(h)
