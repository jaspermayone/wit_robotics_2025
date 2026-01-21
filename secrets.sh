#!/bin/bash
# Encrypt/decrypt secrets using age with SSH key (like agenix)
set -e
cd "$(dirname "$0")"

SECRETS_FILE="src/secrets.h"
ENCRYPTED_FILE="src/secrets.h.age"
SSH_KEY="$HOME/.ssh/id_ed25519"

case "$1" in
    encrypt)
        if [ ! -f "$SECRETS_FILE" ]; then
            echo "Error: $SECRETS_FILE not found"
            exit 1
        fi
        age -R "${SSH_KEY}.pub" -o "$ENCRYPTED_FILE" "$SECRETS_FILE"
        echo "Encrypted $SECRETS_FILE -> $ENCRYPTED_FILE"
        ;;
    decrypt)
        if [ ! -f "$ENCRYPTED_FILE" ]; then
            echo "Error: $ENCRYPTED_FILE not found"
            echo "Copy secrets.h.example to secrets.h and fill in your values"
            exit 1
        fi
        age -d -i "$SSH_KEY" -o "$SECRETS_FILE" "$ENCRYPTED_FILE"
        echo "Decrypted $ENCRYPTED_FILE -> $SECRETS_FILE"
        ;;
    *)
        echo "Usage: $0 {encrypt|decrypt}"
        echo ""
        echo "  encrypt - Encrypt secrets.h using your SSH public key"
        echo "  decrypt - Decrypt secrets.h.age using your SSH private key"
        echo ""
        echo "Requires: brew install age"
        exit 1
        ;;
esac
