from sys import exception
from anthropic import AsyncAnthropic
from anthropic.types import (
    Message,
    MessageParam,
    CacheControlEphemeralParam,
    TextBlock,
    TextBlockParam,
    ThinkingBlock,
    ThinkingBlockParam,
)

from .parameters import (
    PARAMETERS,
    PARAMETER_MODEL_ID,
    PARAMETER_TEMPERATURE,
    PARAMETER_SYSTEM_PROMPT,
    PARAMETER_HUMAN_MESSAGE_TEXT,
    PARAMETER_MAX_OUTPUT_TOKENS_PER_MESSAGE,
    PARAMETER_MAX_OUTPUT_TOKENS_TOTAL,
    PARAMETER_MAX_ASSISTANT_MESSAGES,
    PARAMETER_SILENCE_LENGTH_THRESHOLD,
    PARAMETER_SILENCE_PERSISTENCE_THRESHOLD,
)
from .output import (
    write_line,
    write_lines,
    write_prologue,
    write_epilogue,
    write_message_param,
    write_message_streaming,
)
__all__ = ( "monologue", )

# WORK IN PROGRESS:
# moving output functions into `output.py`
# moving parameter names & descriptions into `parameters.py`

# TODO: re-implement the `end_conversation` tool

# TERMINATE_MONOLOGUE_TOOL = {
#     "name": "end_conversation",
#     "description": "Use this tool to end the conversation. This tool will close the conversation and prevent any further messages from being sent.",
#     "input_schema": {
#         "type": "object",
#         "properties": {},
#     },
# }

async def monologue(parameters, output_stream, info_stream):
    model_id = parameters[PARAMETER_MODEL_ID]
    temperature = parameters[PARAMETER_TEMPERATURE]
    system_prompt = parameters[PARAMETER_SYSTEM_PROMPT]
    human_message_text = parameters[PARAMETER_HUMAN_MESSAGE_TEXT]
    max_output_tokens_per_message = parameters[PARAMETER_MAX_OUTPUT_TOKENS_PER_MESSAGE]
    max_output_tokens_total = parameters[PARAMETER_MAX_OUTPUT_TOKENS_TOTAL]
    max_assistant_messages = parameters[PARAMETER_MAX_ASSISTANT_MESSAGES]
    silence_length_threshold = parameters[PARAMETER_SILENCE_LENGTH_THRESHOLD]
    silence_persistence_threshold = parameters[PARAMETER_SILENCE_PERSISTENCE_THRESHOLD]

    messages = []
    assistant_message_count = 0
    total_input_token_count = 0
    total_output_token_count = 0
    consecutive_silent_assistant_messages = 0
    termination_reason = None

    write_prologue(output_stream, parameters)
    try:
        async with AsyncAnthropic() as client:
            terminated = False
            while not terminated:
                user_message_param = MessageParam(
                    role = "user",
                    content = [
                        TextBlockParam(
                            type = "text",
                            text = human_message_text,
                            cache_control = CacheControlEphemeralParam(type = "ephemeral"),
                        ),
                    ],
                )
                messages.append(user_message_param)

                write_message_param(output_stream, user_message_param)
                write_line(info_stream, "<awaiting response...>")

                async with client.messages.stream(
                        model = model_id,
                        max_tokens = max_output_tokens_per_message,
                        temperature = temperature,
                        system = system_prompt,
                        # tools = [ TERMINATE_MONOLOGUE_TOOL ],
                        messages = messages,
                ) as claude_message_stream:

                    # remove the `cache_control` parameter from our record of
                    # the user message we just sent, so we don't send it again
                    # when generating subsequent messages in the monologue.
                    messages[-1]["content"][0]["cache_control"] = None

                    await write_message_streaming(output_stream, info_stream, claude_message_stream)

                claude_message = await claude_message_stream.get_final_message()
                messages.append(claude_message.model_dump(mode="json", include=["role", "content"]))

                assistant_message_count += 1
                input_token_count = claude_message.usage.input_tokens
                total_input_token_count += input_token_count
                output_token_count = claude_message.usage.output_tokens
                total_output_token_count += output_token_count
                write_lines(info_stream, (f"<used {input_token_count} input tokens & {output_token_count} output tokens for preceding message>", f"<used {total_input_token_count} input tokens & {total_output_token_count} output tokens in total>"))

                if output_token_count <= silence_length_threshold:
                    write_line(info_stream, f"<preceding message is at or below the threshold of {silence_length_threshold} tokens for silence>")
                    consecutive_silent_assistant_messages += 1
                    if consecutive_silent_assistant_messages >= silence_persistence_threshold:
                        write_line(info_stream, f"<terminating monologue after {consecutive_silent_assistant_messages} consecutive silent assistant messages>")
                        terminated = True
                        termination_reason = f"received {consecutive_silent_assistant_messages} consecutive assistant messages with {silence_length_threshold} or fewer tokens."
                    else:
                        write_line(info_stream, f"<{silence_persistence_threshold - consecutive_silent_assistant_messages} consecutive silent assistant messages remaining until termination>")
                elif consecutive_silent_assistant_messages > 0:
                        write_line(info_stream, f"<preceding message is above the threshold of {silence_length_threshold} tokens; resetting the silence counter>")
                        consecutive_silent_assistant_messages = 0
                if not terminated:
                    if assistant_message_count >= max_assistant_messages:
                        terminated = True
                        termination_reason = f"reached or exceeded maximum number of assistant messages ({max_assistant_messages})."
                    elif total_output_token_count >= max_output_tokens_total:
                        terminated = True
                        termination_reason = f"reached or exceeded maximum number of output tokens ({max_output_tokens_total})."
    except:
        error = exception()
        termination_reason = "error: " + repr(error)
        raise error
    finally:
        write_epilogue(output_stream, assistant_message_count, total_output_token_count, termination_reason)
