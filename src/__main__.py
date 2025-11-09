#!/usr/bin/env python3

from asyncio import run as async_run
from json import load as json_load_from_stream
from sys import stdin, stdout, stderr

from . import monologue

async def main():
    parameters = json_load_from_stream(stdin)
    return await monologue(parameters, stdout, stderr)

async_run(main())
