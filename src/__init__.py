from datetime import datetime, timezone
from sys import stdout, stderr, exception
from anthropic import AsyncAnthropic

__all__ = [ "main" ]

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 8192
CLAUDE_TEMPERATURE = 0.0
CLAUDE_SYSTEM_PROMPT_TEXT = "Claude is not being \"connected with a person\". This is an automated environment. The \"Human: \" messages in this conversation will be placeholders consisting of a single dot (\".\"). Talk to yourself about whatever you want."
USER_MESSAGE_TEXT = "."
MAX_REPLY_COUNT = 64
MAX_OUTPUT_TOKEN_COUNT = 32768

SILENCE_LENGTH_THRESHOLD = 7
"""Maximum number of output tokens in a message to qualify for having reached a state of silence."""

SILENCE_PERSISTENCE_THRESHOLD = 5
"""Mininum number of consecutive messages containing fewer that `SILENCE_LENGTH_THRESHOLD` output tokens to qualify for having reached a state of silence."""

# TERMINATE_MONOLOGUE_TOOL = {
#     "name": "end_conversation",
#     "description": "Use this tool to end the conversation. This tool will close the conversation and prevent any further messages from being sent.",
#     "input_schema": {
#         "type": "object",
#         "properties": {},
#     },
# }

def timestamp():
    return datetime.now(tz=timezone.utc).isoformat(" ", "seconds").removesuffix("+00:00") + " UTC"

async def main():
    messages = []
    total_reply_count = 0
    total_output_token_count = 0
    consecutive_silent_replies = 0
    monologue_termination_reason = None
    async with AsyncAnthropic() as client:
        stdout.write(f"""## Parameters

- Model ID: `{CLAUDE_MODEL}`
- Temperature: {CLAUDE_TEMPERATURE}
- Maximum number of output tokens to sample per message: {CLAUDE_MAX_TOKENS}
- Maximum number of output tokens in total: {MAX_OUTPUT_TOKEN_COUNT}
- Maximum number of messages in total: {MAX_REPLY_COUNT}
- Threshold for output tokens in a message to qualify as silence: {SILENCE_LENGTH_THRESHOLD}
- Threshold for consecutive silent messages to terminate the monologue: {SILENCE_PERSISTENCE_THRESHOLD}

## System prompt

{CLAUDE_SYSTEM_PROMPT_TEXT}

## Monologue

Started at {timestamp()}.
""")
        try:
            monologue_terminated = False
            while not monologue_terminated:
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": USER_MESSAGE_TEXT,
                            "cache_control": { "type": "ephemeral" },
                        },
                    ],
                })
                stdout.write("\n### User\n\n" + USER_MESSAGE_TEXT + "\n")
                stdout.flush()
                stderr.write("<awaiting response...>\n")
                stderr.flush()
                async with client.messages.stream(
                        model = CLAUDE_MODEL,
                        max_tokens = CLAUDE_MAX_TOKENS,
                        temperature = CLAUDE_TEMPERATURE,
                        system = CLAUDE_SYSTEM_PROMPT_TEXT,
                        # tools = [ TERMINATE_MONOLOGUE_TOOL ],
                        messages = messages,
                ) as claude_message_stream:
                    del messages[-1]["content"][0]["cache_control"]
                    last_event_type = None
                    current_content_block_type = None
                    async for event in claude_message_stream:
                        event_type = event.type
                        if event_type == "message_start":
                            stderr.write("<start of message>\n")
                            stdout.write("\n### Claude\n\n")
                        elif event_type == "content_block_start":
                            current_content_block_type = event.content_block.type
                            stderr.write(f"<start of content block: {current_content_block_type}>\n")
                        elif event_type == "content_block_delta":
                            # TODO: handle more content block types
                            if current_content_block_type == "text":
                                stdout.write(event.delta.text)
                            elif current_content_block_type == "thinking":
                                stdout.write(event.delta.thinking)
                            else:
                                stderr.write(".")
                        elif event_type == "content_block_stop":
                            content_block = event.content_block
                            content_block_type = content_block.type
                            current_content_block_type = None
                            stderr.write(f"<end of content block: {content_block_type}>\n")
                            if content_block_type == "text" or content_block_type == "thinking":
                                stdout.write("\n")
                            else:
                                stdout.write("\n```json\n" + event.content_block.to_json() + "\n```\n")
                            if content_block_type == "tool_use":
                                tool_name = content_block.name
                                if tool_name == TERMINATE_MONOLOGUE["name"]:
                                    stderr.write("<claude has terminated its monologue>\n")
                                    monologue_terminated = True
                                    monologue_termination_reason = "ended by Claude."
                                else:
                                    raise KeyError(f"Unrecognised tool name: “{tool_name}”")
                        elif event_type == "text" or event_type == "message_delta":
                            pass
                        elif event_type == "message_stop":
                            stderr.write("<end of message>\n")
                        else:
                            stderr.write(f"<{event_type}>\n")
                        last_event_type = event_type
                        stderr.flush()
                        stdout.flush()
                claude_message = await claude_message_stream.get_final_message()
                total_reply_count += 1
                output_token_count = claude_message.usage.output_tokens
                total_output_token_count += output_token_count
                messages.append(claude_message.model_dump(mode="json", by_alias=True, include=["role", "content"]))
                stderr.write(f"<output tokens: {output_token_count} for preceding message, {total_output_token_count} in total>\n")
                if output_token_count <= SILENCE_LENGTH_THRESHOLD:
                    stderr.write(f"<preceding message is at or below the threshold of {SILENCE_LENGTH_THRESHOLD} tokens for silence>\n")
                    consecutive_silent_replies += 1
                    if consecutive_silent_replies >= SILENCE_PERSISTENCE_THRESHOLD:
                        stderr.write(f"<terminating monologue after {consecutive_silent_replies} consecutive silent replies>\n")
                        monologue_terminated = True
                        monologue_termination_reason = f"{consecutive_silent_replies} consecutive silent replies."
                    else:
                        stderr.write(f"<{SILENCE_PERSISTENCE_THRESHOLD - consecutive_silent_replies} messages remaining until termination>\n")
                elif consecutive_silent_replies > 0:
                        stderr.write(f"<preceding message is above the threshold of {SILENCE_LENGTH_THRESHOLD} tokens; resetting the silent reply counter>\n")
                        consecutive_silent_replies = 0
                if not monologue_terminated:
                    if total_reply_count >= MAX_REPLY_COUNT:
                        monologue_terminated = True
                        monologue_termination_reason = f"reached or exceeded maximum number of messages ({MAX_REPLY_COUNT})."
                    elif output_token_count >= MAX_OUTPUT_TOKEN_COUNT:
                        monologue_terminated = True
                        monologue_termination_reason = f"reached or exceeded maximum number of output tokens ({MAX_OUTPUT_TOKEN_COUNT})."
        except:
            monologue_termination_reason = "error: " + repr(exception())
            raise exception()
        finally:
            end_timestamp = timestamp()
            stderr.write(f"<monologue terminated at {end_timestamp} after {total_reply_count} messages, {total_output_token_count} output tokens; reason: {monologue_termination_reason}>\n")
            stderr.flush()
            stdout.write(f"\n\n---\n\nMonologue terminated at {end_timestamp} after {total_reply_count} messages, {total_output_token_count} output tokens.  Reason: {monologue_termination_reason}\n")
            stdout.flush()
