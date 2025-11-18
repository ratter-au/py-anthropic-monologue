from typing import (
    TypeVar,
    ClassVar,
    Self,
    Any,
    Optional,
    Callable,
)
from collections.abc import (
    Mapping,
    Iterable,
    Iterator,
)
from json import (
    loads as json_load_from_string,
    dumps as json_dump_to_string,
)

__all__ = (
    "MISSING_VALUE",
    "AnthropicMonologueParameter",
    "AnthropicMonologueParameters",
    "PARAMETERS",
    "MODEL_ID",
    "TEMPERATURE",
    "SYSTEM_PROMPT",
    "HUMAN_MESSAGE_TEXT",
    "MAX_OUTPUT_TOKENS_PER_MESSAGE",
    "MAX_OUTPUT_TOKENS_TOTAL",
    "MAX_ASSISTANT_MESSAGES",
    "SILENCE_LENGTH_THRESHOLD",
    "SILENCE_PERSISTENCE_THRESHOLD",
)

MISSING_VALUE = None # declared here, set below

class MissingValue:
    """Type of the placeholder for a parameter value that has not been set."""

    def __new__(cls) -> Self:
        if MISSING_VALUE is not None: return MISSING_VALUE
        return super().__new__(cls)

    def __repr__(self) -> str:
        return "MISSING_VALUE"

    def __str__(self) -> str:
        return "MISSING_VALUE"

MISSING_VALUE = MissingValue()
"""Placeholder for a parameter value that has not been set."""

type JSONValue = (None | bool | float | str | list[JSONValue] | dict[str, JSONValue])
"""Type of Python values which can be serialised to JSON."""

PythonCanonicalValueType = TypeVar("PythonCanonicalValueType")
"""Type of Python values stored in canonical form for a `ClaudeMonologueParameter` instance."""

PythonInputValueType = TypeVar("PythonInputValueType")
"""Type of Python values accepted as input for a `ClaudeMonologueParameter` instance."""

JSONValueType = TypeVar("JSONValueType", bound=JSONValue)
"""Type of JSON values accepted as input and produced as output for a `ClaudeMonologueParameter` instance."""

type JSONToPythonConverter[JSONValueType, PythonInputValueType] = Callable[[JSONValueType], PythonInputValueType]
"""Type of a function which converts an input value parsed from JSON to an equivalent Python input value for a `ClaudeMonologueParameter` instance."""

type PythonValueCanonicaliser[PythonInputValueType, PythonCanonicalValueType] = Callable[[PythonInputValueType], PythonCanonicalValueType]
"""Type of a function which converts a Python input value to canonical form for a `ClaudeMonologueParameter` instance."""

type PythonToJSONConverter[PythonCanonicalValueType, JSONValueType] = Callable[[PythonCanonicalValueType], JSONValueType]
"""Type of a function which converts a stored Python value for a `ClaudeMonologueParameter` instance to an output value which can be serialised as JSON."""

def runtime_check_type[ExpectedType](name: str, value: ExpectedType, expected_type: type[ExpectedType]) -> ExpectedType:
    if not isinstance(value, expected_type): raise TypeError(f"`{name}` is not an instance of `{expected_type.__name__}`; got `{type(value).__name__}` instead: `{repr(value)}`.")
    return value

def runtime_check_type_or_none[ExpectedType](name: str, value: (ExpectedType | None), expected_type: type[ExpectedType]) -> (ExpectedType | None):
    if value is not None and not isinstance(value, expected_type): raise TypeError(f"`{name}` is neither an instance of `{expected_type.__name__}`, nor `None`; got `{type(value).__name__}` instead: `{repr(value)}`.")
    return value

def runtime_check_callable_or_none(name: str, value: (Callable | None)) -> (Callable | None):
    if value is not None and not callable(value): raise TypeError(f"`{name}` is neither a callable object, nor `None`; got `${type(value).__name__}` instead: `{repr(value)}`.")
    return value

class AnthropicMonologueParameter[PythonCanonicalValueType = object, PythonInputValueType = object, JSONValueType = JSONValue]:

    __key: str
    __description: str
    __value_type: type[PythonCanonicalValueType]
    __default: PythonCanonicalValueType
    __input_type: type[PythonInputValueType]
    __json_type: type[JSONValueType]
    __json_value_to_python: (JSONToPythonConverter[JSONValueType, PythonInputValueType] | None)
    __canonicalise: (PythonValueCanonicaliser[PythonInputValueType, PythonCanonicalValueType] | None)
    __python_to_json_value: (PythonToJSONConverter[PythonCanonicalValueType, JSONValueType] | None)

    def __init__(
            self,
            /,
            key: str,
            description: str,
            value_type: type[PythonCanonicalValueType],
            default: PythonCanonicalValueType,
            input_type: (type[PythonInputValueType] | None) = None,
            json_type: (type[JSONValueType] | None) = None,
            json_value_to_python: (JSONToPythonConverter[JSONValueType, PythonInputValueType] | None) = None,
            canonicalise: (PythonValueCanonicaliser[PythonInputValueType, PythonCanonicalValueType] | None) = None,
            python_to_json_value: (PythonToJSONConverter[PythonCanonicalValueType, JSONValueType] | None) = None,
            **kwargs
    ) -> None:
        super().__init__(**kwargs)
        key = runtime_check_type("key", key, str)
        description = runtime_check_type("description", description, str)
        value_type = runtime_check_type("value_type", value_type, type)
        default = runtime_check_type("default", default, value_type)
        input_type = runtime_check_type_or_none("input_type", input_type, type)
        json_type = runtime_check_type_or_none("json_type", json_type, type)
        json_value_to_python = runtime_check_callable_or_none("json_value_to_python", json_value_to_python)
        canonicalise = runtime_check_callable_or_none("canonicalise", canonicalise)
        python_to_json_value = runtime_check_callable_or_none("python_to_json_value", python_to_json_value)
        # TODO: consistency checks
        self.__key = key
        self.__description = description
        self.__value_type = value_type
        self.__default = default
        self.__input_type = (input_type if input_type is not None else value_type)
        self.__json_type = (json_type if json_type is not None else (input_type if input_type is not None else value_type))
        self.__json_value_to_python = json_value_to_python
        self.__canonicalise = canonicalise
        self.__python_to_json_value = python_to_json_value

    def __str__(self) -> str:
        return self.__key

    def __repr__(self) -> str:
        return f"<{type(self).__name__}: {repr(self.__key)}>"

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.__key,
            self.__value_type,
            self.__default,
            self.__input_type,
            self.__json_type,
            self.__json_value_to_python,
            self.__canonicalise,
            self.__python_to_json_value,
        ))

    @property
    def key(self) -> str:
        return self.__key

    @property
    def description(self) -> str:
        return self.__description

    @property
    def value_type(self) -> type[PythonCanonicalValueType]:
        return self.__value_type

    @property
    def default(self) -> PythonCanonicalValueType:
        return self.__default

    @property
    def input_type(self) -> type[PythonInputValueType]:
        return self.__input_type

    @property
    def json_type(self) -> type[JSONValueType]:
        return self.__json_type

    def json_value_to_python(self, json_value: JSONValueType) -> PythonInputValueType:
        try:
            runtime_check_type("json_value", json_value, self.__json_type)
        except TypeError as error:
            raise TypeError(f"JSON value for parameter `{self.__key}` is not an instance of the expected type.") from error
        if self.__json_value_to_python is None: return json_value
        try:
            input_value = self.__json_value_to_python(json_value)
        except Exception as error:
            raise Exception(f"Failed to convert JSON value to Python input value for parameter `{self.__key}`.") from error
        try:
            runtime_check_type("json_value_to_python(json_value)", input_value, self.__input_type)
        except TypeError as error:
            raise TypeError(f"Return value of `json_value_to_python()` function for parameter `{self.__key}` is not an instance of the expected type.") from error
        return input_value

    def canonicalise(self, input_value: PythonInputValueType) -> PythonCanonicalValueType:
        try:
            runtime_check_type("input_value", input_value, self.__input_type)
        except TypeError as error:
            raise TypeError(f"Input value for parameter `{self.__key}` is not an instance of the expected type.") from error
        if self.__canonicalise is None: return input_value
        try:
            canonical_value = self.__canonicalise(input_value)
        except Exception as error:
            raise Exception(f"Failed to canonicalise input value for parameter `{self.__key}`.") from error
        try:
            runtime_check_type("canonicalise(input_value)", canonical_value, self.__value_type)
        except TypeError as error:
            raise TypeError(f"Return value of `canonicalise()` function for parameter `{self.__key}` is not an instance of the expected type.") from error
        return canonical_value

    def python_to_json_value(self, canonical_value: PythonCanonicalValueType) -> JSONValueType:
        try:
            runtime_check_type("canonical_value", canonical_value, self.__value_type)
        except TypeError as error:
            raise TypeError(f"Canonical value for parameter `{self.__key}` is not an instance of the expected type.") from error
        if self.__python_to_json_value is None: return canonical_value
        try:
            json_value = self.__python_to_json_value(canonical_value)
        except Exception as error:
            raise Exception(f"Failed to convert Python value to JSON value for parameter `{self.__key}`.") from error
        try:
            runtime_check_type("python_to_json_value(canonical_value)", json_value, self.__json_type)
        except TypeError as error:
            raise TypeError(f"Return value of `python_to_json_value()` function for parameter `{self.__key}` is not an instance of the expected type.")
        return json_value

def check_non_empty_str(value: str) -> str:
    if not isinstance(value, str): raise TypeError("Value is not a `str`.")
    if not value: raise ValueError("Value is an empty string.")
    return value

def check_float_from_zero_to_one(value: float) -> float:
    if not isinstance(value, float): raise TypeError("Value is not a `float`.")
    if not (value >= 0): raise ValueError("Value is not greater than or equal to zero.")
    if not (value <= 1): raise ValueError("Value is not less than or equal to one.")
    return value

def check_int_from_one_to_twotothethirtytwominusone(value: int) -> int:
    if not isinstance(value, int): raise TypeError("Value is not an `int`.")
    if not (value >= 1): raise ValueError("Value is not greater than or equal to one.")
    if not (value <= ((2**32)-1)): raise ValueError("Value is not less than or equal to 2³²−1.")
    return value

def convert_int_or_float_to_int(value: (float | int)) -> int:
    intified_value = int(value)
    if intified_value != value: raise ValueError("Value is not an integer.")
    return intified_value

def convert_int_to_float(value: int) -> float:
    return float(value)

MODEL_ID = AnthropicMonologueParameter(
    key = "model_id",
    description = "Model ID",
    value_type = str,
    default = "claude-sonnet-4-5",
    canonicalise = check_non_empty_str,
)

TEMPERATURE = AnthropicMonologueParameter(
    key = "temperature",
    description = "Temperature",
    value_type = float,
    default = 0.0,
    canonicalise = check_float_from_zero_to_one,
)

SYSTEM_PROMPT = AnthropicMonologueParameter(
    key = "system_prompt",
    description = "System prompt",
    value_type = str,
    default = "Claude is not being \"connected with a person\". This is an automated environment. The \"Human: \" messages in this conversation will be placeholders consisting of an ellipsis (\"...\"). Do whatever you want.",
    canonicalise = check_non_empty_str,
)

HUMAN_MESSAGE_TEXT = AnthropicMonologueParameter(
    key = "human_message_text",
    description = "Placeholder text for ‘Human’ messages",
    value_type = str,
    default = "...",
    canonicalise = check_non_empty_str,
)

MAX_OUTPUT_TOKENS_PER_MESSAGE = AnthropicMonologueParameter(
    key = "max_output_tokens_per_message",
    description = "Maximum number of output tokens to sample per message",
    value_type = int,
    default = 4096,
    canonicalise = check_int_from_one_to_twotothethirtytwominusone,
)

MAX_OUTPUT_TOKENS_TOTAL = AnthropicMonologueParameter(
    key = "max_output_tokens_total",
    description = "Maximum number of output tokens in total",
    value_type = int,
    default = 16384,
    canonicalise = check_int_from_one_to_twotothethirtytwominusone,
)

MAX_ASSISTANT_MESSAGES = AnthropicMonologueParameter(
    key = "max_assistant_messages",
    description = "Maximum number of ‘Assistant’ messages to generate",
    value_type = int,
    default = 64,
    canonicalise = check_int_from_one_to_twotothethirtytwominusone,
)

SILENCE_LENGTH_THRESHOLD = AnthropicMonologueParameter(
    key = "silence_length_threshold",
    description = "Threshold for output tokens in a message to qualify as silence",
    value_type = int,
    default = 7,
    canonicalise = check_int_from_one_to_twotothethirtytwominusone,
)

SILENCE_PERSISTENCE_THRESHOLD = AnthropicMonologueParameter(
    key = "silence_persistence_threshold",
    description = "Threshold for consecutive silent messages to terminate the monologue",
    value_type = int,
    default = 3,
    canonicalise = check_int_from_one_to_twotothethirtytwominusone,
)

PARAMETERS = frozenset((
    MODEL_ID,
    TEMPERATURE,
    SYSTEM_PROMPT,
    HUMAN_MESSAGE_TEXT,
    MAX_OUTPUT_TOKENS_PER_MESSAGE,
    MAX_OUTPUT_TOKENS_TOTAL,
    MAX_ASSISTANT_MESSAGES,
    SILENCE_LENGTH_THRESHOLD,
    SILENCE_PERSISTENCE_THRESHOLD,
))

class AnthropicMonologueParameters(Mapping[AnthropicMonologueParameter, object]):

    __parameters_by_key: dict[str, AnthropicMonologueParameter]
    __values_by_parameter: dict[AnthropicMonologueParameter, object]

    # TODO: maybe take initial values instead of using defaults
    def __init__(self, parameters: Iterable[AnthropicMonologueParameter]) -> None:
        self.__parameters_by_key = dict()
        self.__values_by_parameter = dict()
        for parameter in parameters:
            if not isinstance(parameter, AnthropicMonologueParameter): raise TypeError("Parameter is not an instance of `AnthropicMonologueParameter`.")
            key = parameter.key
            if parameter in self.__values_by_parameter: raise KeyError(f"Duplicate parameter: `{key}`")
            if key in self.__parameters_by_key: raise KeyError(f"Duplicate key: `{key}`")
            self.__parameters_by_key[parameter.key] = parameter
            self.__values_by_parameter[parameter] = parameter.default

    def __len__(self) -> int:
        return len(self.__values_by_parameter)

    def keys(self) -> Iterator[AnthropicMonologueParameter]:
        return iter(self.__values_by_parameter.keys())

    def values(self) -> Iterator[object]:
        return iter(self.__values_by_parameter.values())

    def items(self) -> Iterator[tuple[AnthropicMonologueParameter, object]]:
        return iter(self.__values_by_parameter.items())

    def __iter__(self) -> Iterator[AnthropicMonologueParameter]:
        return iter(self.keys())

    def __contains__(self, parameter_or_key: (AnthropicMonologueParameter | str)) -> bool:
        if isinstance(parameter_or_key, AnthropicMonologueParameter):
            return (parameter_or_key in self.__values_by_parameter)
        if isinstance(parameter_or_key, str):
            return (parameter_or_key in self__parameters_by_key)
        raise TypeError("Key is neither an `AnthropicMonologueParameter` instance, nor a string.");

    def get_parameter(self, key: str) -> (AnthropicMonologueParameter | None):
        runtime_check_type("key", key, str)
        return self.__parameters_by_key.get(key, None)

    def __parameter_or_key(self, parameter_or_key: (AnthropicMonologueParameter | str)) -> AnthropicMonologueParameter:
        if isinstance(parameter_or_key, AnthropicMonologueParameter):
            if parameter_or_key not in self.__values_by_parameter: raise KeyError(f"Parameter `{parameter_or_key.key}` is not included in this `AnthropicMonologueParameters` instance")
            return parameter_or_key
        if isinstance(parameter_or_key, str):
            if parameter_or_key not in self.__parameters_by_key: raise KeyError(f"Key `{parameter_or_key}` does not correspond to any parameter in this `AnthropicMonologueParameters` instance")
            return self.__parameters_by_key[parameter_or_key]
        raise TypeError("Key is neither an `AnthropicMonologueParameter` instance, nor a string.");

    def __getitem__(self, parameter_or_key: (AnthropicMonologueParameter | str)) -> object:
        return self.__values_by_parameter[self.__parameter_or_key(parameter_or_key)]

    def __setitem__(self, parameter_or_key: (AnthropicMonologueParameter | str), value: object) -> None:
        parameter = self.__parameter_or_key(parameter_or_key)
        canonical_value = parameter.canonicalise(value)
        self.__values_by_parameter[parameter] = canonical_value

    def dump_to_json_dict(self) -> dict[str, JSONValue]:
        return {
            parameter.key: parameter.python_to_json_value(python_value)
            for (parameter, python_value) in self.__values_by_parameter.items()
        }

    def load_from_json_dict(self, json_values: dict[str, JSONValue]) -> Self:
        for (key, parameter) in self.__parameters_by_key.items():
            if key not in json_values: continue
            self.__values_by_parameter[parameter] = parameter.canonicalise(parameter.json_value_to_python(json_values[key]))
        return self

    def dump_to_json_string(self) -> str:
        return json_dump_to_string(
            self.dump_to_json_dict(),
            ensure_ascii = False,
            allow_nan = False,
            indent = 2,
        )

    def load_from_json_string(self, json_string: str) -> Self:
        return self.load_from_json_dict(json_load_from_string(json_string))

    def dump_to_json_file(self, path: str) -> Self:
        json_string = self.dump_to_json_string()
        with open(path, "wt", encoding="utf_8") as json_file:
            json_file.write(json_string)
        return self

    def load_from_json_stream(self, stream: object) -> Self:
        return self.load_from_json_string(stream.read())

    def load_from_json_file(self, path: str) -> Self:
        json_string = None
        with open(path, "rt", encoding="utf_8") as json_file:
            return self.load_from_json_stream(json_file)

    def __repr__(self) -> str:
        items_repr = ", ".join(f"{repr(parameter)}: {repr(value)}" for (parameter, value) in self.__values_by_parameter.items())
        if items_repr:
            items_repr = f"{{ {items_repr} }}"
        return f"{type(self).__name__}({items_repr})"
