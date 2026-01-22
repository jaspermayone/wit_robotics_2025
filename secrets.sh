#!/bin/bash
# Simple wrapper to call script in scripts folder
cd "$(dirname "$0")"
./scripts/secrets.sh "$@"