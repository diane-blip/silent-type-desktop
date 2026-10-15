"""Download the lip-reading checkpoint and face model, each checked by full SHA-256."""

import hashlib
import json
import urllib.request

from silent_type.state import FACE_MODEL_NAME, MODEL_NAME, data_dir

# Auto-AVSR's official model zoo links this checkpoint (https://github.com/mpc001/auto_avsr#model-zoo).
# Upstream publishes only an MD5 prefix (49f77); the SHA-256 below is of the verified download.
CHECKPOINT = {
    "file": MODEL_NAME,
    "drive_id": "1r1kx7l9sWnDOCnaFHIGvOtzuhFyFA88_",
    "sha256": "fbf7cd70ff1c0e694b3030fb779dbb4570f04e4b841d62f9296c229e94878ddb",
}
# Google's MediaPipe face detector model. Google publishes no checksum; the SHA-256
# below is of the file served from this official URL on October 15, 2026.
FACE_MODEL = {
    "file": FACE_MODEL_NAME,
    "url": "https://storage.googleapis.com/mediapipe-models/face_detector/"
    "blaze_face_short_range/float16/1/blaze_face_short_range.tflite",
    "sha256": "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f",
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def install(model, fetch):
    folder = data_dir() / "models"
    folder.mkdir(exist_ok=True)
    destination = folder / model["file"]
    if destination.exists():
        if sha256(destination) != model["sha256"]:
            raise RuntimeError(f"{destination} does not match its expected SHA-256. Delete it and rerun.")
        print("Already installed and verified:", destination)
        return destination
    partial = destination.with_suffix(".download")
    fetch(partial)
    actual = sha256(partial)
    if actual != model["sha256"]:
        partial.unlink()
        raise RuntimeError(f"{model['file']} failed its SHA-256 check (got {actual}). Nothing was installed.")
    partial.replace(destination)
    print("Installed and verified:", destination)
    return destination


def fetch_checkpoint(partial):
    import gdown

    url = f"https://drive.google.com/uc?id={CHECKPOINT['drive_id']}"
    if not gdown.download(url, str(partial), quiet=False, resume=True):
        raise RuntimeError("Checkpoint download did not finish.")


def fetch_face_model(partial):
    urllib.request.urlretrieve(FACE_MODEL["url"], partial)


def main():
    checkpoint = install(CHECKPOINT, fetch_checkpoint)
    install(FACE_MODEL, fetch_face_model)
    (checkpoint.parent / "model-source.json").write_text(
        json.dumps(
            {
                "checkpoint": {"source": "https://github.com/mpc001/auto_avsr#model-zoo", **CHECKPOINT},
                "face_model": {
                    "source": "https://ai.google.dev/edge/mediapipe/solutions/vision/face_detector",
                    **FACE_MODEL,
                },
                "terms_status": "Checkpoint terms unspecified by upstream; see THIRD_PARTY.md.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
