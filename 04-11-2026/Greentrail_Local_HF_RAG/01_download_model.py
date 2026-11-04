"""Download a public Hugging Face model into this project once.

Run: python 01_download_model.py
No HF_TOKEN or paid Inference Providers credits required.
"""
from pathlib import Path
from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parent
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
MODEL_DIR = ROOT / "Models" / "Qwen2.5-0.5B-Instruct"

print("Downloading public model:", MODEL_ID)
print("Saving inside project:", MODEL_DIR)

snapshot_download(
    repo_id=MODEL_ID,
    local_dir=str(MODEL_DIR),
    allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt"],
)

print("\nModel downloaded successfully!")
print("Model files:")
for file in sorted(MODEL_DIR.iterdir()):
    if file.is_file():
        print(" -", file.name)
print("\nNext: python 02_local_rag.py")


