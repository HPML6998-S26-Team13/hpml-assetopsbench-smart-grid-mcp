#!/bin/bash
# Test inference against a running vLLM server on Insomnia.
# Run from the login node after opening an SSH tunnel to the compute node:
#   ssh -N -L 8000:localhost:8000 <node_hostname>
#
# Usage:
#   bash scripts/test_inference.sh <host> [port] [model]
#
# Example:
#   bash scripts/test_inference.sh localhost 8000

set -euo pipefail

HOST="${1:?Usage: $0 <host> [port] [model]}"
PORT="${2:-8000}"
MODEL="models/Llama-3.1-8B-Instruct"
MODEL="${3:-$MODEL}"
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

validate_completion_json() {
  python3 -c '
import json
import sys

payload = json.load(sys.stdin)
if "error" in payload and payload["error"] is not None:
    raise SystemExit(f"error payload returned: {payload[\"error\"]}")
choices = payload.get("choices") or []
if not choices:
    raise SystemExit("no choices present in completion response")
text = (choices[0].get("text") or "").strip()
if not text:
    raise SystemExit("completion response was empty")
print(text)
'
}

validate_chat_json() {
  python3 -c '
import json
import sys

payload = json.load(sys.stdin)
if "error" in payload and payload["error"] is not None:
    raise SystemExit(f"error payload returned: {payload[\"error\"]}")
choices = payload.get("choices") or []
if not choices:
    raise SystemExit("no choices present in chat response")
message = choices[0].get("message") or {}
content = (message.get("content") or "").strip()
if not content:
    raise SystemExit("chat response was empty")
print(content)
'
}

# --- List models ---
echo ""
echo "[2/4] Available models:"
MODELS_RESPONSE="$(curl -s "$BASE_URL/v1/models")"
echo "$MODELS_RESPONSE" | python3 -m json.tool
echo "$MODELS_RESPONSE" | MODEL_TO_CHECK="$MODEL" python3 -c "
import json
import os
import sys

model = os.environ['MODEL_TO_CHECK']
payload = json.load(sys.stdin)
model_ids = [item.get('id') for item in payload.get('data', []) if item.get('id')]
if model not in model_ids:
    raise SystemExit(f\"ERROR: expected model {model!r} not in loaded models: {model_ids}\")
print(f\"  OK: {model} is loaded\")
"

# --- Completions API test ---
echo ""
echo "[3/4] Completions API (transformer DGA prompt):"
COMP_PAYLOAD="$(MODEL_TO_USE="$MODEL" python3 - <<'PY'
import json
import os

print(
    json.dumps(
        {
            "model": os.environ["MODEL_TO_USE"],
            "prompt": "A power transformer's dissolved gas analysis shows elevated hydrogen and acetylene levels. This pattern indicates",
            "max_tokens": 100,
            "temperature": 0.7,
        }
    )
)
PY
)"
COMP_RESPONSE=$(curl -s "$BASE_URL/v1/completions" \
    -H "Content-Type: application/json" \
    -d "$COMP_PAYLOAD")
echo "$COMP_RESPONSE" | python3 -m json.tool
COMP_TEXT="$(echo "$COMP_RESPONSE" | validate_completion_json)"
echo "  Completion preview: $COMP_TEXT"

# Extract tokens/sec from usage
PROMPT_TOKENS=$(echo "$COMP_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['usage']['prompt_tokens'])" 2>/dev/null || echo "?")
COMP_TOKENS=$(echo "$COMP_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['usage']['completion_tokens'])" 2>/dev/null || echo "?")
echo "  Prompt tokens: $PROMPT_TOKENS, Completion tokens: $COMP_TOKENS"

# --- Chat API test ---
echo ""
echo "[4/4] Chat API (work order prompt):"
CHAT_PAYLOAD="$(MODEL_TO_USE="$MODEL" python3 - <<'PY'
import json
import os

print(
    json.dumps(
        {
            "model": os.environ["MODEL_TO_USE"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Smart Grid maintenance assistant.",
                },
                {
                    "role": "user",
                    "content": "Transformer T-4021 shows DGA readings of H2=450ppm, C2H2=120ppm. What fault type does this indicate and what priority should the work order be?",
                },
            ],
            "max_tokens": 200,
            "temperature": 0.7,
        }
    )
)
PY
)"
CHAT_RESPONSE="$(curl -s "$BASE_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d "$CHAT_PAYLOAD")"
echo "$CHAT_RESPONSE" | python3 -m json.tool
CHAT_TEXT="$(echo "$CHAT_RESPONSE" | validate_chat_json)"
echo "  Chat preview: $CHAT_TEXT"

echo ""
echo "=== All Tests Passed ==="
echo "Environment is ready for MCP experiments."
