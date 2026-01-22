#!/bin/bash
# Encrypt/decrypt secrets using age with SSH key (like agenix) - Linux version
set -e
cd "$(dirname "$0")"

SECRETS_FILE="src/secrets.h"
ENCRYPTED_FILE="src/secrets.h.age"
SSH_KEY="$HOME/.ssh/id_ed25519"

# Check if age is installed
if ! command -v age &> /dev/null; then
    echo "Error: 'age' encryption tool not found."
    echo "Install age based on your Linux distribution:"
    echo "  Ubuntu/Debian: sudo apt install age"
    echo "  Fedora: sudo dnf install age"
    echo "  Arch: sudo pacman -S age"
    echo "  Or download from: https://github.com/FiloSottile/age"
    exit 1
fi

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
        echo "Requires: age encryption tool"
        exit 1
        ;;
esac