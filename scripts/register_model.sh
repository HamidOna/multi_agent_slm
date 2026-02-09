#!/bin/bash
# Register a custom Olive-optimized model with Foundry Local.
#
# Usage: bash scripts/register_model.sh
#
# This copies the optimized ONNX model into Foundry's cache directory
# and creates the inference_model.json that Foundry needs to discover it.

set -e

MODEL_ALIAS="qwen3-0.6b-int4"
SOURCE_DIR="models/qwen3-0.6b-int4"
FOUNDRY_CACHE="$USERPROFILE/.foundry/cache/models"
TARGET_DIR="$FOUNDRY_CACHE/Custom/$MODEL_ALIAS"

echo "=== Registering $MODEL_ALIAS with Foundry Local ==="
echo ""

# Check source exists (Olive may output to model/ subfolder or directly)
if [ -f "$SOURCE_DIR/model/model.onnx" ]; then
    SOURCE_DIR="$SOURCE_DIR/model"
elif [ ! -f "$SOURCE_DIR/model.onnx" ]; then
    echo "ERROR: Optimized model not found at $SOURCE_DIR"
    echo "Run: python scripts/optimize_model.py first"
    exit 1
fi

# Clean up any previous registration
if [ -d "$TARGET_DIR" ]; then
    echo "Removing previous registration..."
    rm -rf "$TARGET_DIR"
fi

# Create target directory and copy all model files
echo "Copying model files to Foundry cache..."
mkdir -p "$TARGET_DIR"
cp "$SOURCE_DIR"/model.onnx "$TARGET_DIR/"
cp "$SOURCE_DIR"/model.onnx.data "$TARGET_DIR/"
cp "$SOURCE_DIR"/genai_config.json "$TARGET_DIR/"
cp "$SOURCE_DIR"/tokenizer.json "$TARGET_DIR/"
cp "$SOURCE_DIR"/tokenizer_config.json "$TARGET_DIR/"
cp "$SOURCE_DIR"/config.json "$TARGET_DIR/"
cp "$SOURCE_DIR"/generation_config.json "$TARGET_DIR/"

# Copy optional files (present depending on Olive/onnxruntime-genai version)
for f in special_tokens_map.json added_tokens.json merges.txt vocab.json chat_template.jinja model_config.json; do
    if [ -f "$SOURCE_DIR/$f" ]; then
        cp "$SOURCE_DIR/$f" "$TARGET_DIR/"
    fi
done

# Create inference_model.json with Qwen ChatML template + tool calling
echo "Creating inference_model.json..."
cat > "$TARGET_DIR/inference_model.json" << 'EOF'
{
  "Name": "qwen3-0.6b-int4",
  "PromptTemplate": {
    "system": "<|im_start|>system\n{Content}<|im_end|>",
    "user": "<|im_start|>user\n{Content}<|im_end|>",
    "assistant": "<|im_start|>assistant\n{Content}<|im_end|>",
    "prompt": "<|im_start|>user\n{Content}<|im_end|>\n<|im_start|>assistant"
  }
}
EOF

echo ""
echo "Done! Files copied to: $TARGET_DIR"
echo ""
ls -lh "$TARGET_DIR"
echo ""
echo "Verifying with foundry cache ls..."
foundry cache ls
