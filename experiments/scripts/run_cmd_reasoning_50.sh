#!/bin/bash
set -e

# Run tau2bench telecom eval: command-a-reasoning, 50 samples

echo "🐝 Starting bee run: command-a-reasoning, 50 samples"
echo "Started at: $(date)"

# Load environment variables and export them
if [ -f ~/dev/eval-ds/.env ]; then
    set -a
    source ~/dev/eval-ds/.env
    set +a
    echo "✓ Loaded and exported environment variables"
else
    echo "❌ .env file not found!"
    exit 1
fi

# Verify API key is set
if [ -z "$CO_API_KEY_STAGING" ]; then
    echo "❌ CO_API_KEY_STAGING not set!"
    exit 1
fi
echo "✓ API key verified"

# Change to apiary bee directory
cd ~/dev/apiary/bee

# Run bee
.venv/bin/python3 -m bee \
  -I ~/dev/eval-ds/experiments/configs/tau2bench_telecom_cmd_reasoning_50.toml

echo ""
echo "✅ Bee run completed at: $(date)"

