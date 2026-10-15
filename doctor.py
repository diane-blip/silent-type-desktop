"""Read-only local diagnostics: GPU, imports, source integrity, model and cameras."""

import hashlib
import json

from silent_type.punctuate import api_key
from silent_type.recognition import VENDOR, Recognizer, cameras
from silent_type.state import settings


def main():
    import torch

    manifest = json.loads((VENDOR / "provenance.json").read_text())
    changed = [
        path
        for path, digest in manifest["files"].items()
        if hashlib.sha256((VENDOR / path).read_bytes()).hexdigest() != digest
    ]
    if changed:
        raise RuntimeError(f"Upstream files changed: {changed}")
    print("PyTorch:", torch.__version__)
    print("CUDA:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name())
        print("GPU operation:", float((torch.ones(2, device="cuda") * 2).sum()))
    print("Cameras:", cameras())
    config = settings()
    recognizer = Recognizer(config)
    print("Checkpoint architecture loaded:", recognizer.device, len(recognizer.tokens), "tokens")
    print("No microphone capture. Lip reading runs locally.")
    on = config.get("punctuate", True) and api_key(config)
    print(
        "Punctuation: "
        + ("on; recognized text goes to Anthropic" if on else "off; nothing leaves this computer")
    )


if __name__ == "__main__":
    main()
