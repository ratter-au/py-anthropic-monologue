from datetime import datetime, timezone
from json import dumps as json_dump_to_string
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
    PARAMETER_SYSTEM_PROMPT,
)

__all__ = (
    "timestamp",
    "write_line",
    "write_lines",
    "write_prologue",
    "write_epilogue",
    "write_message",
    "write_message_streaming",
)

PARAMETER_UNSPECIFIED = "(unspecified)"

def timestamp():
    return datetime.now(tz=timezone.utc).isoformat(" ", "seconds").removesuffix("+00:00") + " UTC"

def write_line(stream, text):
    stream.write(text)
    stream.write("\n")
    stream.flush()

def write_lines(stream, lines):
    for line in lines:
        stream.write(line)
        stream.write("\n")
    stream.flush()

def write_prologue(stream, parameters):
    stream.write("## Parameters\n\n")
    for (PARAMETER_KEY, PARAMETER) in PARAMETERS.items():
        if PARAMETER_KEY == PARAMETER_SYSTEM_PROMPT: continue
        PARAMETER_DESCRIPTION = PARAMETER["description"]
        parameter_value = parameters.get(PARAMETER_KEY, PARAMETER_UNSPECIFIED)
        stream.write(f"- {PARAMETER_DESCRIPTION}: {parameter_value}\n")
    system_prompt = parameters.get(PARAMETER_SYSTEM_PROMPT, PARAMETER_UNSPECIFIED)
    stream.write(f"\n## System prompt\n\n{system_prompt}\n")
    stream.write(f"\n## Monologue\n\nStarted at {timestamp()}.\n")
    stream.flush()

def write_epilogue(stream, assistant_message_count, total_output_token_count, termination_reason):
    write_lines(stream, ("", "---", "", f"Monologue terminated at {timestamp()} after {assistant_message_count} assistant messages with {total_output_token_count} output tokens.  Reason: {termination_reason}"))

def write_text_content_block(stream, text):
    write_line(stream, text)

def write_thinking_content_block(stream, thinking):
    write_lines(stream, ("`<thinking>`  ", thinking, "`</thinking>`"))

def write_unknown_content_block(stream, content):
    content_type = content.type
    write_lines(stream, (f"`<unhandled_content type=\"{content_type}\">`  ", "```python", repr(content), "```", "`</unhandled_content>`"))

def write_unknown_content_block_param(stream, content_block_param):
    content_type = content_block_param["type"]
    write_lines(stream, (f"`<unhandled_content type=\"{content_type}\">`  ", "```python", repr(content_block_param), "```", "`</unhandled_content>`"))

def write_message_role_header(stream, role):
    pretty_role = "User" if role == "user" else "Claude" if role == "assistant" else role
    write_lines(stream, ("", f"### {pretty_role}", ""))

def write_message(stream, message):
    write_message_role_header(stream, message.role)
    for content in message.content:
        content_type = content.type
        if content_type == "text":
            write_text_content_block(stream, content.text)
        elif content_type == "thinking":
            write_thinking_content_block(stream, content.thinking)
        else:
            write_unknown_content_block(stream, content)

def write_message_param(stream, message):
    write_message_role_header(stream, message["role"])
    for content in message["content"]:
        content_type = content["type"]
        if content_type == "text":
            write_text_content_block(stream, content["text"])
        elif content_type == "thinking":
            write_thinking_content_block(stream, content["thinking"])
        else:
            write_unknown_content_block_param(stream, content)

def write_message_start_event(stream, event):
    write_message_role_header(stream, event.message.role)

def write_content_block_start_event(stream, event):
    content_block = event.content_block
    content_block_type = content_block.type
    # TODO: handle more content block types
    if content_block_type == "text":
        pass
    elif content_block_type == "thinking":
        write_line(stream, "`<thinking>`  ")
    else:
        write_lines(stream, ("`<unhandled_content type=\"{content_block_type}\">`  ", "```python"))

def write_content_block_delta_event(stream, event, current_content_block_type):
    delta = event.delta
    # TODO: handle more content block types
    if current_content_block_type == "text":
        stream.write(delta.text)
    elif current_content_block_type == "thinking":
        stream.write(delta.thinking)
    else:
        pass
    stream.flush()

def write_content_block_stop_event(stream, event):
    content_block = event.content_block
    content_block_type = content_block.type
    if content_block_type == "text" or content_block_type == "thinking":
        write_line(stream, "")
    else:
        write_lines(stream, ("", "```json", repr(content_block), "```"))

async def write_message_streaming(output_stream, info_stream, message_event_stream):
    current_content_block_type = None
    async for event in message_event_stream:
        event_type = event.type
        if event_type == "message_start":
            write_line(info_stream, "<start of message>")
            write_message_start_event(output_stream, event)
        elif event_type == "content_block_start":
            current_content_block_type = event.content_block.type
            write_line(info_stream, f"<start of content block: {current_content_block_type}>")
            write_content_block_start_event(output_stream, event)
        elif event_type == "content_block_delta":
            write_content_block_delta_event(output_stream, event, current_content_block_type)
        elif event_type == "content_block_stop":
            content_block = event.content_block
            content_block_type = content_block.type
            current_content_block_type = None
            write_line(info_stream, f"<end of content block: {content_block_type}>")
            write_content_block_stop_event(output_stream, event)
            if content_block_type == "tool_use":
                raise NotImplementedError("Tool use is not implemented yet.")
        elif event_type == "text" or event_type == "message_delta":
            pass
        elif event_type == "message_stop":
            write_line(info_stream, "<end of message>")
            write_line(output_stream, "")
        else:
            write_line(info_stream, f"<unhandled event: {event_type}>")
