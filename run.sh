#!/bin/sh
exec python3 -m anthropic_monologue "$@" | tee output/`date -u +%Y%m%d-%H%M`.md
