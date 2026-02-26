from dataclasses import dataclass
import inspect
from typing import Literal, Any, _LiteralGenericAlias

@dataclass
class Parameter:
    name: str
    description: str

@dataclass
class NumericParameter(Parameter):
    t: Any
    default: int|float|None

@dataclass
class ChoiceParameter(Parameter):
    choices: list[str]
    default: str|None

class InvalidParameterAnnotation(RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)



def parse_parameter(name: str, parameter: inspect.Parameter) -> Parameter:
    hint = parameter.annotation
    default = parameter.default
    if isinstance(hint, _LiteralGenericAlias):
        choices = [str(a) for a in hint.__args__]
        if default is not None and default not in choices:
            raise InvalidParameterAnnotation(f"{name}: invalid default (not valid choice): {default}")
        return ChoiceParameter(name=name, description=name, choices=choices, default=default)
    for t in (int, float):
        if t == hint:
            if not isinstance(default, t):
                raise InvalidParameterAnnotation("{name}: invalid default (wrong type): {default}")
            return NumericParameter(name=name, description=name, t=t, default=default)
    raise InvalidParameterAnnotation(f"{name}: unknown parameter type: {hint}")



def parse_parameters(generator_func) -> list[Parameter]:
    signature = inspect.signature(generator_func)
    return [parse_parameter(name, p) for name, p in signature.parameters.items()]

