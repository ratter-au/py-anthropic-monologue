#!/usr/bin/env python3

from asyncio import run as async_run
from sys import stdin, stdout, stderr

from . import monologue
from .parameters import (
    AnthropicMonologueParameters,
    PARAMETERS
)

async def main():
    parameters = AnthropicMonologueParameters(PARAMETERS)
    parameters.load_from_json_stream(stdin)
    return await monologue(parameters, stdout, stderr)

async_run(main())
