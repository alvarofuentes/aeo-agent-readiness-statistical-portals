"""Model allowlist used by every benchmark runner.

The policy remains fail-closed for remote/cloud models and unknown parameter
sizes.  The former 24B ceiling was explicitly lifted by the user; the current
local experimental ceiling is 40B so the installed 30B MoE Qwen variants can
be selected deliberately and recorded in the run manifest.
"""
from __future__ import annotations

import re

MAX_PARAMETER_B = 40.0

# Ollama's /api/tags endpoint does not expose parameter counts.  These are the
# local model names already documented by the project diagnostics.  Unknown
# names are rejected unless their tag contains an explicit parameter count, so
# a future >24B model cannot enter by accident.
KNOWN_PARAMETER_B = {
    "muse-glimmer:30b-mlx": 30.0,
    "gemma4:latest": 8.0,
    "qwen3.5:9b-mlx": 9.0,
    "deepseek-coder-v2:16b": 15.7,
    "mistral:latest": 7.2,
    "llama3.2:latest": 3.2,
    "devstral-small-2:24b": 24.0,
    "qwen3:30b-a3b": 30.5,
    "qwen3-coder:30b-a3b-q4_k_m": 30.5,
}


def parameter_size_b(model_name: str) -> float | None:
    known = KNOWN_PARAMETER_B.get(model_name.lower())
    if known is not None:
        return known
    match = re.search(r"(?<![0-9])([0-9]+(?:\.[0-9]+)?)b(?:[^a-z]|$)", model_name.lower())
    if match:
        return float(match.group(1))
    return None


def allowed_model(model_name: str) -> bool:
    name = model_name.lower()
    if ":cloud" in name or "cloud" in name:
        return False
    size = parameter_size_b(model_name)
    return size is not None and size <= MAX_PARAMETER_B


def assert_allowed_model(model_name: str) -> None:
    if not allowed_model(model_name):
        if "cloud" in model_name.lower():
            raise RuntimeError(f"Model '{model_name}' is remote/cloud and is not allowed")
        size = parameter_size_b(model_name)
        if size is not None:
            raise RuntimeError(
                f"Model '{model_name}' exceeds the configured local ceiling ({size:g}B > {MAX_PARAMETER_B:g}B)"
            )
        raise RuntimeError(f"Model '{model_name}' has no verified local parameter size and is not allowed")


def allowed_models(model_names: list[str]) -> list[str]:
    return [name for name in model_names if allowed_model(name)]
