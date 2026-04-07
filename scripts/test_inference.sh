#!/bin/bash
# Test inference against a running vLLM server on Insomnia.
# Run from the login node while vllm_serve.sh job is active.
#
# Usage:
#   bash scripts/test_inference.sh <node_hostname> [port]
#
# Example:
#   bash scripts/test_inference.sh ins080 8000

set -euo pipefail

HOST="${1:?Usage: $0 <node_hostname> [port]}"
PORT="${2:-8000}"
MODEL="models/Llama-3.1-8B-Instruct"
BASE_URL="http://$HOST:$PORT"

echo "=== vLLM Inference Test ==="
echo "Server: $BASE_URL"
echo ""

# --- Health check ---
echo "[1/4] Health check..."
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "  FAIL: Server not reachable at $BASE_URL"
    echo "  Check that the job is running: squeue -u \$USER"
    exit 1
fi
echo "  OK"

# --- List models ---
echo ""
echo "[2/4] Available models:"
curl -s "$BASE_URL/v1/models" | python3 -m json.tool

# --- Completions API test ---
echo ""
echo "[3/4] Completions API (transformer DGA prompt):"
COMP_RESPONSE=$(curl -s "$BASE_URL/v1/completions" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"prompt\": \"A power transformer's dissolved gas analysis shows elevated hydrogen and acetylene levels. This pattern indicates\",
        \"max_tokens\": 100,
        \"temperature\": 0.7
    }")
echo "$COMP_RESPONSE" | python3 -m json.tool

# Extract tokens/sec from usage
PROMPT_TOKENS=$(echo "$COMP_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['usage']['prompt_tokens'])" 2>/dev/null || echo "?")
COMP_TOKENS=$(echo "$COMP_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['usage']['completion_tokens'])" 2>/dev/null || echo "?")
echo "  Prompt tokens: $PROMPT_TOKENS, Completion tokens: $COMP_TOKENS"

# --- Chat API test ---
echo ""
echo "[4/4] Chat API (work order prompt):"
curl -s "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "{
        \"model\": \"$MODEL\",
        \"messages\": [
            {\"role\": \"system\", \"content\": \"You are a Smart Grid maintenance assistant.\"},
            {\"role\": \"user\", \"content\": \"Transformer T-4021 shows DGA readings of H2=450ppm, C2H2=120ppm. What fault type does this indicate and what priority should the work order be?\"}
        ],
        \"max_tokens\": 200,
        \"temperature\": 0.7
    }" | python3 -m json.tool

echo ""
echo "=== All Tests Passed ==="
echo "Environment is ready for MCP experiments."
