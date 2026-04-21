#!/bin/bash
# Insomnia-specific environment overrides.
#
# Source this file inside any script that runs on Insomnia compute nodes:
#
#   # shellcheck source=scripts/insomnia_env.sh
#   source "$(dirname "${BASH_SOURCE[0]}")/insomnia_env.sh"
#
# It is safe to source on other clusters — each block is gated on a hostname
# pattern and exits silently if it doesn't match.
#
# On a non-Insomnia host, set INSOMNIA_ENV=1 to force-apply these settings:
#   INSOMNIA_ENV=1 bash scripts/vllm_serve.sh

if [[ "${INSOMNIA_ENV:-0}" == "1" || "$(hostname)" == ins* ]]; then
    # HPE Slingshot fabric: NCCL defaults to the IB/CXI transport, which hangs
    # on cxiWaitEventWait. Force TCP over eth0 instead.
    export NCCL_SOCKET_IFNAME=eth0
    export NCCL_IB_DISABLE=1
fi
