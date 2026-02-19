
class InvalidParameterException(RuntimeError):
    def __init__(self, parameters: list[str], message: str):
        super().__init__(f"Parameter(s) {parameters} are invalid: {message}")
        self.parameters = parameters


