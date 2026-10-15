# Changelog

## 0.3.1 (October 15, 2026)

- The icon is now the shushing-face emoji 🤫, drawn from Windows' own emoji font on each computer (the artwork is Microsoft's, so it isn't shipped here). Recording and reading add a green or amber dot; off is gray.

## 0.3.0 (October 15, 2026)

- The webcam opens only on a hold and closes 15 seconds after the last phrase (`camera_warm_seconds`). Before, it stayed open for 10 idle minutes and locked other apps, such as video calls, out of the camera.
- "Silent Type on" switch in the tray menu: off releases the camera at once and ignores the keys.
- App icon: closed lips on a disc, in the Start menu, windows and tray; the tray color shows ready, recording, reading or off.

## 0.2.0 (October 15, 2026)

- Hash-locked installs for NVIDIA (`requirements-cuda.lock`) and CPU (`requirements-cpu.lock`); PyTorch 2.13 (CUDA 13 on NVIDIA), Pillow 12.3, gdown 5.2.2, setuptools 84. No known vulnerabilities in the locked set at release.
- MediaPipe 0.10.35 with its current face detector (BlazeFace short range), which drops the vulnerable protobuf dependency.
- Both models verified by full SHA-256 instead of a 5-character checksum prefix.
- Releasing Alt last no longer opens the app's menu bar: one unassigned key code (0xE8) is sent when a hold starts.
- `app.py` split into `session.py`, `window.py` and `tray.py`; code formatted and linted with Ruff.
- `env_file` setting to read the punctuation key from another `.env`, such as Dictate's.
- Update and uninstall steps, contributor notes, security note and a Windows CI workflow.

## 0.1.0 (October 15, 2026)

First member edition.
