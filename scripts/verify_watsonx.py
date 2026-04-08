"""Verify WatsonX.ai access: auth, list available models, test inference.

Usage:
    # From team repo root, with .venv active and .env in place:
    .venv/bin/python scripts/verify_watsonx.py

    # Pick a different model:
    .venv/bin/python scripts/verify_watsonx.py --model meta-llama/llama-3-3-70b-instruct

    # Run a multi-trial latency benchmark:
    .venv/bin/python scripts/verify_watsonx.py --benchmark --trials 5 --max-tokens 128

Author: Wei Alexander Xin (wax1)
Team 13 / District 1101 — HPML SmartGridBench
"""

import argparse
import os
import sys
import time
from pathlib import Path


def load_dotenv(env_path: Path) -> None:
    # Minimal .env loader so we don't require python-dotenv
    if not env_path.exists():
        print(
            f"ERROR: {env_path} not found. Create it with WATSONX_* vars.",
            file=sys.stderr,
        )
        sys.exit(1)
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify WatsonX.ai access")
    parser.add_argument(
        "--model",
        default="meta-llama/llama-3-1-8b-instruct",
        help="Model ID to test inference against",
    )
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list available models, skip inference test",
    )
    parser.add_argument(
        "--filter",
        default="llama",
        help="Substring filter for model listing (default: llama)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run a multi-trial latency benchmark on the chosen model",
    )
    parser.add_argument(
        "--trials", type=int, default=3, help="Trials per benchmark run (default: 3)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=64,
        help="max_new_tokens per trial (default: 64)",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="Path to a text file to use as the prompt (overrides built-in smoke prompt)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    load_dotenv(repo_root / ".env")

    project_id = os.environ.get("WATSONX_PROJECT_ID")
    api_key = os.environ.get("WATSONX_API_KEY")
    url = os.environ.get("WATSONX_URL")

    missing = [
        k
        for k, v in [
            ("WATSONX_PROJECT_ID", project_id),
            ("WATSONX_API_KEY", api_key),
            ("WATSONX_URL", url),
        ]
        if not v
    ]
    if missing:
        print(f"ERROR: missing env vars: {missing}", file=sys.stderr)
        return 1

    print(f"[1/3] Authenticating to {url}...")
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
    except ImportError:
        print(
            "ERROR: ibm-watsonx-ai not installed. Run: pip install ibm-watsonx-ai",
            file=sys.stderr,
        )
        return 1

    creds = Credentials(url=url, api_key=api_key)
    try:
        client = APIClient(credentials=creds, project_id=project_id)
        print(f"  OK. Client version: {client.version}")
    except Exception as e:
        print(f"  FAILED: {e}", file=sys.stderr)
        return 1

    print(f"\n[2/3] Listing foundation models (filter: '{args.filter}')...")
    try:
        specs = client.foundation_models.get_model_specs()
        # Response shape: {"resources": [{"model_id": ..., "label": ..., ...}]}
        resources = specs.get("resources", []) if isinstance(specs, dict) else []
        filtered = [
            r for r in resources if args.filter.lower() in r.get("model_id", "").lower()
        ]
        if not filtered:
            print(f"  No models matched '{args.filter}'. Full count: {len(resources)}")
            print("  First 5 model IDs in account:")
            for r in resources[:5]:
                print(f"    - {r.get('model_id')}")
        else:
            print(f"  Found {len(filtered)} matching models:")
            for r in filtered:
                model_id = r.get("model_id", "?")
                label = r.get("label", "")
                short_desc = r.get("short_description", "")[:80]
                print(f"    - {model_id}")
                if label:
                    print(f"        label: {label}")
                if short_desc:
                    print(f"        desc:  {short_desc}")
    except Exception as e:
        print(f"  FAILED: {e}", file=sys.stderr)
        return 1

    if args.list_only:
        print("\n--list-only set, skipping inference test.")
        return 0

    print(f"\n[3/3] Testing inference on {args.model}...")
    try:
        model = ModelInference(
            model_id=args.model,
            credentials=creds,
            project_id=project_id,
        )
        if args.prompt_file:
            prompt = Path(args.prompt_file).read_text()
            print(
                f"  Using prompt from: {args.prompt_file} ({len(prompt)} chars, ~{len(prompt) // 4} tokens)"
            )
        else:
            prompt = "Answer in one short sentence: What is a smart grid?"
        params = {
            "max_new_tokens": args.max_tokens,
            "temperature": 0.1,
        }
        # First call (cold) -- separate from benchmark stats
        t0 = time.perf_counter()
        response = model.generate_text(prompt=prompt, params=params)
        cold_elapsed = time.perf_counter() - t0
        print(f"  Prompt:   {prompt}")
        print(f"  Response: {response}")
        print(f"  Cold call: {cold_elapsed:.2f}s ({args.max_tokens} max_new_tokens)")

        if args.benchmark:
            print(
                f"\n  Benchmark: {args.trials} warm trials, max_new_tokens={args.max_tokens}"
            )
            timings = []
            for i in range(args.trials):
                t0 = time.perf_counter()
                _ = model.generate_text(prompt=prompt, params=params)
                elapsed = time.perf_counter() - t0
                timings.append(elapsed)
                print(f"    trial {i + 1}: {elapsed:.2f}s")
            avg = sum(timings) / len(timings)
            mn, mx = min(timings), max(timings)
            print(f"  Warm avg: {avg:.2f}s (min {mn:.2f}, max {mx:.2f})")
            print(
                f"  Approx tokens/sec: {args.max_tokens / avg:.1f}  (assumes full max_new_tokens)"
            )

        print("\n  OK: WatsonX access verified end-to-end.")
    except Exception as e:
        print(f"  FAILED: {e}", file=sys.stderr)
        print("\n  Auth worked but inference failed. Possible causes:")
        print("    - Model ID is wrong (use --list-only to see available models)")
        print("    - Model is not enabled for this project tier")
        print("    - Rate limit or quota exceeded")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
