import argparse
import re
from pathlib import Path

import model
import parse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path, help="file to write to")
    parser.add_argument("--format", "-f", choices=["openscad"], default="openscad", help="Output format")
    parser.add_argument("parameters", type=str, nargs="+", help="parameters in 'key=value' format")
    return parser.parse_args()

def parse_cmdline_params(args) -> dict[str, str]:
    result = {}
    for p in args.parameters:
        try:
            key, value = p.split("=")
        except ValueError:
            raise RuntimeError(f"parameter '{p}' does not follow key=value format")
        result[key] = value
    return result


def check_parameter(parameter_definition: parse.Parameter, value: str):
    try:
        if isinstance(parameter_definition, parse.NumericParameter):
            return parameter_definition.t(value)
        if isinstance(parameter_definition, parse.ChoiceParameter):
            if not value in parameter_definition.choices:
                raise RuntimeError(f"{value} must be one of {parameter_definition.choices}")
            return value
    except Exception as e:
        e.add_note(f"while parsing parameter {parameter_definition.name}")
        raise

def check_parameters(parameter_definitions: list[parse.Parameter], parameters: dict[str, str]):
    result = {}
    for p in parameter_definitions:
        try:
            definition = parameters[p.name]
        except KeyError:
            raise RuntimeError(f"value for '{p.name}=' not given on command line")
        value = check_parameter(p, definition)
        result[p.name] = value
    return result

def write_codes(out: Path, codes):
    if not out.exists():
        out.mkdir(parents=True)
    if not out.is_dir():
        raise RuntimeError(f"{out} is not a directory")
    for name, code in codes:
        with open(out / f"{name}.scad", "w") as f:
            f.write(code)


def main():
    args = parse_args()
    cmdline_parameters = parse_cmdline_params(args)
    generator_parameters = parse.parse_parameters(model.generate)
    checked_parameters = check_parameters(generator_parameters, cmdline_parameters)
    codes: list[tuple[str, str]] = model.generate(**checked_parameters)
    write_codes(args.out, codes)


if __name__ == "__main__":
    main()
