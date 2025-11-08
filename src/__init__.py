from sys import stdout, stderr, exception
from anthropic import AsyncAnthropic

__all__ = [ "main" ]

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MAX_TOKENS = 8192
CLAUDE_TEMPERATURE = 0.0
CLAUDE_SYSTEM_PROMPT_TEXT = "<additional_instructions>Claude is not being \"connected with a person\". This is an automated environment. The \"Human\" turns in this conversation will be placeholders consisting of a single ellipsis (\"...\"). You may talk to yourself about whatever you want.</additional_instructions>"
USER_MESSAGE_TEXT = "..."
MAX_REPLY_COUNT = 50
TERMINATE_MONOLOGUE = {
    "name": "end_conversation",
    "description": "Use this tool to end the conversation. This tool will close the conversation and prevent any further messages from being sent.",
    "input_schema": {
        "type": "object",
        "properties": {},
    },
}

async def main():
    messages = []
    reply_count = 0
    output_token_count = 0
    monologue_termination_reason = None
    async with AsyncAnthropic() as client:
        stdout.write(CLAUDE_SYSTEM_PROMPT_TEXT + "\n")
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
                stdout.write("\nHuman: " + USER_MESSAGE_TEXT + "\n")
                stdout.flush()
                stderr.write("<awaiting response...>\n")
                stderr.flush()
                async with client.messages.stream(
                        model = CLAUDE_MODEL,
                        max_tokens = CLAUDE_MAX_TOKENS,
                        temperature = CLAUDE_TEMPERATURE,
                        system = CLAUDE_SYSTEM_PROMPT_TEXT,
                        # tools = [ TERMINATE_MONOLOGUE ],
                        messages = messages,
                ) as claude_message_stream:
                    del messages[-1]["content"][0]["cache_control"]
                    last_event_type = None
                    current_content_block_type = None
                    async for event in claude_message_stream:
                        event_type = event.type
                        if event_type == "message_start":
                            stderr.write("<start of message>\n")
                            stdout.write("\nAssistant: ")
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
                                stdout.write("\n\n")
                            else:
                                stdout.write(event.content_block.to_json() + "\n\n")
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
                reply_count += 1
                output_token_count += claude_message.usage.output_tokens
                messages.append(claude_message.model_dump(mode="json", by_alias=True, include=["role", "content"]))
                if reply_count >= MAX_REPLY_COUNT and not monologue_terminated:
                    monologue_terminated = True
                    monologue_termination_reason = "reached maximum number of messages."
        except:
            monologue_termination_reason = "error: " + repr(exception())
            raise exception()
        finally:
            stderr.write(f"<monologue terminated after {reply_count} messages, {output_token_count} output tokens; reason: {monologue_termination_reason}>\n")
            stderr.flush()
            stdout.write(f"\n\n---\n\nMonologue terminated after {reply_count} messages, {output_token_count} output tokens.  Reason: {monologue_termination_reason}\n")
            stdout.flush()
