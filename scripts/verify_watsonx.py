#!/usr/bin/env python3
"""Verify WatsonX.ai API access and list available models.

Usage:
    python scripts/verify_watsonx.py --list-only   # just list models
    python scripts/verify_watsonx.py                # list models + run test inference
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)


def get_credentials():
    api_key = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url = os.environ.get("WATSONX_URL")

    if not all([api_key, project_id, url]):
        print("ERROR: Missing credentials. Ensure .env has:")
        print("  WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL")
        sys.exit(1)

    return {"api_key": api_key, "project_id": project_id, "url": url}


def list_models(creds):
    from ibm_watsonx_ai import APIClient, Credentials

    credentials = Credentials(url=creds["url"], api_key=creds["api_key"])
    client = APIClient(credentials, project_id=creds["project_id"])

    # Get the real supported models from the API, not the stale SDK enum
    specs = client.foundation_models.get_model_specs(limit=100)
    models = specs.get("resources", [])

    print("=== Supported Models on WatsonX ===\n")
    for m in sorted(models, key=lambda x: x["model_id"]):
        print(f"  {m['model_id']}")
    print(f"\n  Total: {len(models)} model(s)")

    # Highlight the ones we care about
    our_models = [
        m["model_id"]
        for m in models
        if any(
            k in m["model_id"]
            for k in ["llama", "maverick", "granite-3-3", "granite-4"]
        )
    ]
    if our_models:
        print("\n  Relevant to our project:")
        for m in our_models:
            print(f"    {m}")

    return models


def test_inference(creds):
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    credentials = Credentials(url=creds["url"], api_key=creds["api_key"])

    # Maverick is available on our WatsonX project
    model_id = "meta-llama/llama-4-maverick-17b-128e-instruct-fp8"
    print(f"\n=== Test Inference ({model_id}) ===\n")

    model = ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=creds["project_id"],
        params={
            "max_new_tokens": 200,
            "temperature": 0.7,
        },
    )

    prompt = (
        "A power transformer's dissolved gas analysis shows H2=450ppm and C2H2=120ppm. "
        "What fault type does this indicate?"
    )

    print(f"Prompt: {prompt}\n")
    response = model.generate_text(prompt)
    print(f"Response:\n  {response}\n")
    print("=== WatsonX Verified ===")


def main():
    parser = argparse.ArgumentParser(description="Verify WatsonX.ai access")
    parser.add_argument(
        "--list-only", action="store_true", help="Only list models, skip inference test"
    )
    args = parser.parse_args()

    creds = get_credentials()
    list_models(creds)

    if not args.list_only:
        test_inference(creds)


if __name__ == "__main__":
    main()
