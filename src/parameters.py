from json import (
    loads as json_load_from_string,
    dumps as json_dump_to_string,
)

__all__ = (
    "PARAMETERS",
    "PARAMETER_MODEL_ID",
    "PARAMETER_TEMPERATURE",
    "PARAMETER_SYSTEM_PROMPT",
    "PARAMETER_HUMAN_MESSAGE_TEXT",
    "PARAMETER_MAX_OUTPUT_TOKENS_PER_MESSAGE",
    "PARAMETER_MAX_OUTPUT_TOKENS_TOTAL",
    "PARAMETER_MAX_ASSISTANT_MESSAGES",
    "PARAMETER_SILENCE_LENGTH_THRESHOLD",
    "PARAMETER_SILENCE_PERSISTENCE_THRESHOLD",
    "from_json",
    "to_json",
)

PARAMETER_MODEL_ID = "model_id"
PARAMETER_TEMPERATURE = "temperature"
PARAMETER_SYSTEM_PROMPT = "system_prompt"
PARAMETER_HUMAN_MESSAGE_TEXT = "human_message_text"
PARAMETER_MAX_OUTPUT_TOKENS_PER_MESSAGE = "max_output_tokens_per_message"
PARAMETER_MAX_OUTPUT_TOKENS_TOTAL = "max_output_tokens_total"
PARAMETER_MAX_ASSISTANT_MESSAGES = "max_assistant_messages"
PARAMETER_SILENCE_LENGTH_THRESHOLD = "silence_length_threshold"
PARAMETER_SILENCE_PERSISTENCE_THRESHOLD = "silence_persistence_threshold"

PARAMETERS = {
    PARAMETER_MODEL_ID: {
        "description": "Model ID",
        "python_type": str,
        "json_type": str,
    },
    PARAMETER_TEMPERATURE: {
        "description": "Temperature",
        "python_type": float,
        "json_type": float,
    },
    PARAMETER_SYSTEM_PROMPT: {
        "description": "System prompt",
        "python_type": str,
        "json_type": str,
    },
    PARAMETER_HUMAN_MESSAGE_TEXT: {
        "description": "Placeholder text for ‘Human’ messages",
        "python_type": str,
        "json_type": str,
    },
    PARAMETER_MAX_OUTPUT_TOKENS_PER_MESSAGE: {
        "description": "Maximum number of output tokens to sample per message",
        "python_type": int,
        "json_type": float,
    },
    PARAMETER_MAX_OUTPUT_TOKENS_TOTAL: {
        "description": "Maximum number of output tokens in total",
        "python_type": int,
        "json_type": float,
    },
    PARAMETER_MAX_ASSISTANT_MESSAGES: {
        "description": "Maximum number of ‘Assistant’ messages to generate",
        "python_type": int,
        "json_type": float,
    },
    PARAMETER_SILENCE_LENGTH_THRESHOLD: {
        "description": "Threshold for output tokens in a message to qualify as silence",
        "python_type": int,
        "json_type": float,
    },
    PARAMETER_SILENCE_PERSISTENCE_THRESHOLD: {
        "description": "Threshold for consecutive silent messages to terminate the monologue",
        "python_type": int,
        "json_type": float,
    },
}

def to_json(parameters):
    try:
        return json_dump_to_string(
            {
                PARAMETER_KEY: PARAMETER["json_type"](parameters[PARAMETER_KEY])
                for (PARAMETER_KEY, PARAMETER) in PARAMETERS.items()
            },
            ensure_ascii = False,
            allow_nan = False,
            indent = 2,
        )
    except KeyError as error:
        raise KeyError("Missing parameter") from error

def from_json(string):
    dict_from_json = json_load_from_string(string)
    if not isinstance(dict_from_json, dict): raise TypeError("JSON string does not evaluate to an object")
    try:
        return {
            PARAMETER_KEY: PARAMETER["python_type"](dict_from_json[PARAMETER_KEY])
            for (PARAMETER_KEY, PARAMETER) in PARAMETERS.items()
        }
    except KeyError as error:
        raise KeyError("Missing parameter") from error
