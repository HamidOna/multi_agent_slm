"""Optimize Qwen3 0.6B to INT4 ONNX using Microsoft Olive.

Usage:
    python scripts/optimize_model.py

Downloads the model from HuggingFace, converts to ONNX, and quantizes
to INT4 using the ONNX Runtime GenAI model builder.

Output: models/qwen3-0.6b-int4/

Requirements: pip install olive-ai onnxruntime-genai transformers
"""

import subprocess
import sys
from pathlib import Path

MODEL_ID = "Qwen/Qwen3-0.6B"
OUTPUT_DIR = "models/qwen3-0.6b-int4"


def ensure_model_local():
    """Download model to a local directory (avoids symlink issues on Windows)."""
    import os
    from huggingface_hub import snapshot_download

    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    local_dir = Path("models") / "hf-downloads" / MODEL_ID.split("/")[-1]
    local_path = snapshot_download(
        MODEL_ID, token=False, local_dir=str(local_dir)
    )
    print(f"Model cached at: {local_path}")
    return local_path


def main():
    output = Path(OUTPUT_DIR)
    if output.exists() and any(output.rglob("*.onnx")):
        print(f"Model already exists at {OUTPUT_DIR}")
        print("Delete the directory to re-optimize.")
        return

    print(f"Optimizing {MODEL_ID} -> INT4 ONNX")
    print(f"Output: {OUTPUT_DIR}\n")

    local_path = ensure_model_local()

    cmd = [
        sys.executable, "-m", "olive", "auto-opt",
        "--model_name_or_path", local_path,
        "--trust_remote_code",
        "--output_path", OUTPUT_DIR,
        "--device", "cpu",
        "--provider", "CPUExecutionProvider",
        "--precision", "int4",
        "--use_model_builder",
        "--use_ort_genai",
        "--log_level", "1",
    ]

    print(f"Running Olive optimization...\n")
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print(f"\nOptimization failed with exit code {result.returncode}")
        sys.exit(1)

    print("\nOptimization complete! Output files:")
    for f in sorted(output.rglob("*")):
        if f.is_file():
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.relative_to(output)}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
