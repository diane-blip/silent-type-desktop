# How it fits together

| Module | Job |
|---|---|
| `app.py` | Coordinator. Owns Tk, the tray, the status strip and the held-key watcher; runs one `Session` at a time. Other threads reach Tk only through `post()`. |
| `session.py` | One phrase: wait for the camera, record, read 10-second parts while recording (`PartReader`), restore casing, punctuate, log, save, type. No widgets. |
| `hold_control.py` | Pure state machine for the held pair: settle, finish on release, cancel on other keys or focus change. |
| `windows.py` | Key state by `GetAsyncKeyState`, foreground window, Unicode `SendInput` typing with its guards, single-instance lock. |
| `camera.py` | Camera stream opened on a hold, with half-second pre-roll for follow-up phrases and close after `camera_warm_seconds`; recorded frames kept as JPEG. The webcam is exclusive, so never hold it longer. |
| `worker.py` / `recognition.py` | Model in a separate process with time limits; face detection (MediaPipe) and Auto-AVSR decoding. |
| `punctuate.py` | Optional Claude Haiku pass, accepted only when every word matches. |
| `window.py`, `tray.py`, `indicator.py`, `recents.py`, `icon.py` | The settings window, tray icon and on/off switch, click-through status strip, Recents popup and the 🤫 icon, drawn from Windows' emoji font (`python -m silent_type.icon` rebuilds the ignored `silent-type.ico`). |
| `state.py`, `log.py` | Settings, history (SQLite) and the markdown log. |

Rules the code holds to: no keyboard hooks, key suppression or injected modifiers (the only synthetic key is the unassigned 0xE8 menu mask); typing never touches the clipboard; text is typed only into the window that was in front when the hold began; recognized words are never logged to the app log or shown on the strip.

## Checks before a pull request

```powershell
.venv\Scripts\python -m pip install --require-hashes -r requirements-dev.txt
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m ruff format --check .
.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
.venv\Scripts\python -m pip_audit -r requirements-cuda.lock --disable-pip --no-deps
```

Then the hardware checks on a real webcam: `tests.app_smoke`, `tests.indicator_smoke`, `tests.hold_pipeline`, `tests.camera_pipeline`, `tests.delivery_pipeline` and `tests.menu_mask_check` (hands off the keyboard for the last two; your typing lands in their test windows and cancels the hold).

## Changing dependencies

Edit `requirements.txt` (or the PyTorch line in `requirements-cuda.in` / `requirements-cpu.in`), then regenerate both locks with [uv](https://docs.astral.sh/uv/). PyTorch's index serves its hashes, so nothing large downloads:

```powershell
uv pip compile requirements.txt requirements-cuda.in --generate-hashes --python-version 3.12 --python-platform x86_64-pc-windows-msvc --extra-index-url https://download.pytorch.org/whl/cu130 --index-strategy unsafe-best-match --no-header -o requirements-cuda.lock
uv pip compile requirements.txt requirements-cpu.in --generate-hashes --python-version 3.12 --python-platform x86_64-pc-windows-msvc --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match --no-header -o requirements-cpu.lock
```

No AI models from Chinese organizations, as a dependency or an optional backend.

## CI

`docs/ci-windows.yml` runs lint, formatting, the offline tests and the audit on Windows. To turn it on in your copy, move it to `.github/workflows/`; pushing a workflow file needs a GitHub token with the `workflow` scope.
