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

@dataclass
class ChoiceParameter(Parameter):
    choices: list[str]

class InvalidParameterAnnotation(RuntimeError):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)



def parse_parameter(name: str, hint) -> Parameter:
    if isinstance(hint, _LiteralGenericAlias):
        return ChoiceParameter(name=name, description=name, choices=[str(a) for a in hint.__args__])
    for t in (int, float):
        if t == hint:
            return NumericParameter(name=name, description=name, t=t)
    raise InvalidParameterAnnotation(f"{name}: unknown parameter type: {hint}")



def parse_parameters(generator_func) -> list[Parameter]:
    return [parse_parameter(name, hint) for name, hint in inspect.get_annotations(generator_func).items() if name != "return"]

