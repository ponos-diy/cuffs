from typing import Literal, Any, _LiteralGenericAlias
import base64
import inspect
import importlib

import js
import pyodide
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch


class InvalidParameterException(RuntimeError):
    def __init__(self, parameters: list[str], message: str):
        super().__init__(f"Parameter(s) {parameters} are invalid: {message}")
        self.parameters = parameters

class Parameter:
    def __init__(self, description):
        self.description = description
        self.value = None

    def add_description(self, form):
        d = js.document.createElement("div")
        d.innerHTML = self.description
        d.classList.add("form-text")
        form.appendChild(d)
        return d

    def add_form_element(self, form):
        raise NotImplementedError()

ScadCodes = list[tuple[str, str]]

class ModelWrapper:
    def __init__(self, display, form, generator):
        assert display
        self.display = display
        self.model = generator
        self.parameters = {}
        self.viewers: dict[str, dict[str,Any]] = {}
        self.counter = 0
        self.start_button = None
        self.parameters: list[Parameter] = parse_parameters(generator)
        self.error_display = None
        self.init_form(form)

    def init_form(self, form):
        for p in self.parameters:
            p.add_form_element(form, self.update_scad)

        self.error_display = js.document.createElement("div")
        self.error_display.classList.add("alert")
        self.error_display.classList.add("alert-warning")
        self.error_display.style.visibility = "hidden"
        form.appendChild(self.error_display)

        self.start_button = js.document.createElement("button")
        self.start_button.innerHTML = "generate"
        self.start_button.classList.add("btn")
        self.start_button.classList.add("btn-primary")
        async def on_generate(event):
            await self.update_viewers()
        self.start_button.addEventListener("click", create_proxy(on_generate))
        self.start_button.disabled = True
        form.appendChild(self.start_button)



    def init_display(self, scad_codes: ScadCodes):
        for name, _ in scad_codes:
            render_container = createRendererSurrounding(self.display, name)
            link = js.document.createElement("a")
            link.innerHTML = f"download {name}"
            link.href = "#"
            render_container.appendChild(link)
            render_spinner = createRendererSpinner(render_container)
            render_viewer = createRenderer(render_container)

            assert render_viewer
            assert render_spinner
            render_spinner.style.display = "none"
            
            v = {"viewer": render_viewer, "spinner": render_spinner, "link": link}
            self.viewers[name] = v

    async def update_scad(self) -> dict[str, str] | None:
        try:
            parameters = {p.name: p.value for p in self.parameters}
            print(parameters)
            invalid_parameters = [name for name, value in parameters.items() if value is None]
            if invalid_parameters:
                raise InvalidParameterException(parameters=invalid_parameters, message="invalid input")
            scad_codes = self.model(**parameters)
        except InvalidParameterException as e:
            self.show_status_error(e)
            return None
        except Exception as e:
            self.show_status_error(e)
            return None
        else:
            self.no_error()
            return scad_codes

    async def update_viewers(self):
        scad_codes: ScadCodes | None = await self.update_scad()
        self.start_button.disabled = True
        if not scad_codes:
            return
        if not self.viewers:
            self.init_display(scad_codes)
        for name, _ in scad_codes:
            self.viewers[name]["spinner"].style.display = "block"
        for name, code in scad_codes:
            self.counter += 1
            await renderOpenscadToViewer(code, str(self.counter), self.viewers[name]["viewer"], self.viewers[name]["link"])
            self.viewers[name]["spinner"].style.display = "none"
            print(f"finished updating model {name}")

    def show_status_error(self, message: str | InvalidParameterException):
        if isinstance(message, InvalidParameterException):
            # TODO: mark forms as invalid
            pass
        self.error_display.innerHTML = str(message)
        self.error_display.style.visibility = "visible"
        self.start_button.disabled = True
        print(f"generation had error: {message}")

    def no_error(self):
        self.error_display.style.visibility = "hidden"
        self.start_button.disabled = False
        print("generation successful")

async def run(model):
    print("openswebcad loading")

    display = js.document.getElementById("model-display")
    form = js.document.getElementById("parameter-selection")
    assert display

    await load_local_includes(model)

    model_wrapper = ModelWrapper(display, form, model.generate)
    print("setup completed")

async def load_local_includes(model):
    if not hasattr(model, "includes"):
        return
    for name, url in model.includes.items():
        module = await load_file(name, url)
        setattr(model, name, module)

async def load_file(name: str, url: str):
    response = await pyfetch(f"./{name}.py")
    local = f"{name}.py"
    with open(local, "wb") as f:
        f.write(await response.bytes())
    spec = importlib.util.spec_from_file_location(name, local)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# parameter parsing
class NumericParameter(Parameter):
    def __init__(self, name: str, description: str, t: Literal[int, float]):
        super().__init__(description)
        self.name = name
        self.convert = t

    def add_form_element(self, form, on_change_cb):
        d = self.add_description(form)
        i = js.document.createElement("input")
        i.type = "number"
        i.classList.add("form-control")
        #i.id = f"parameter-{self.name}"

        async def on_change(event):
            try:
                self.value = self.convert(event.target.value)
            except ValueError as e:
                print(e)
                self.value = None
            await on_change_cb()
        i.addEventListener("change", create_proxy(on_change))

        
        form.appendChild(i)

class ChoiceParameter(Parameter):
    def __init__(self, name: str, description: str, choices: list[str]):
        super().__init__(description)
        self.name = name
        self.parameter_target = None
        self.choices = choices

    def add_form_element(self, form, on_change_cb):
        d = self.add_description(form)
        group = js.document.createElement("div")
        group.classList.add("btn-group")
        group.role = "group"
        group.ariaLabel = self.description
        
        for choice in self.choices:
            i = js.document.createElement("input")
            i.type = "radio"
            i.value = choice
            i.name = f"parameter-{self.name}"
            i.id = f"parameter-{self.name}-{choice}"
            i.classList.add("btn-check")
            i.autocomplete = "off"

            l = js.document.createElement("label")
            l.classList.add("btn")
            l.classList.add("btn-outline-primary")
            l.htmlFor = i.id
            l.innerHTML = choice
            #i.id = f"parameter-{self.name}"

            async def on_change(event, choice=choice):
                if event.target.checked:
                    self.value = choice
                print(f"choice {choice} changed to {event.target.checked}")
                await on_change_cb()
            i.addEventListener("change", create_proxy(on_change))

            group.appendChild(i)
            group.appendChild(l)

        
        form.appendChild(group)


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



def parse_parameters(generator_func):
    return [parse_parameter(name, hint) for name, hint in inspect.get_annotations(generator_func).items() if name != "return"]

