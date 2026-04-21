#!/bin/bash
# Fix SSH configuration for Linux container (strip macOS-specific options)

# Set correct permissions on SSH keys
chmod 600 /root/.ssh/id_ed25519* 2>/dev/null || true

# Remove macOS-specific SSH options that don't exist in Linux
sed -i '/UseKeychain/d' /root/.ssh/config 2>/dev/null || true
sed -i '/AddKeysToAgent/d' /root/.ssh/config 2>/dev/null || true

echo "SSH configuration fixed for container"
