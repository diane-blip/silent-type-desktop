# Silent Type

Type by mouthing the words. Hold **Right Ctrl + Right Alt**, mouth a sentence at your webcam, let go, and it types at your cursor. No microphone, so I can use it in a coffee shop without narrating my emails to the room.

It was inspired by [amywork777's Lipflow](https://github.com/amywork777/lipflow), and the lip reading is [Auto-AVSR](https://github.com/mpc001/auto_avsr) from Imperial College London. The hard part is theirs, and it runs entirely on your computer. I built the Windows app around it so it sits next to Dictate: hold-to-type, a Recents popup in the tray, a running log, and a status strip that never shows your words.

Experimental. Recognition guesses wrong sometimes, so test it on your own face before you use it on client work.

## Install

Windows 10/11, Python 3.12 and a webcam.

```powershell
.\install.ps1           # NVIDIA GPU; needs a driver with CUDA 13 (nvidia-smi shows it)
.\install.ps1 -CpuOnly  # no NVIDIA card
```

It builds its own `.venv` from a hash-locked package list, downloads the 1 GB lip-reading model from the official Auto-AVSR link and Google's small MediaPipe face model, checks both by SHA-256, and adds **Silent Type** to the Start menu. On my RTX 5060, text lands 3 to 6 seconds after I let go, including a 24-second phrase. I haven't timed CPU-only; expect it to be slower.

Punctuation is optional. Copy `.env.example` to `.env` and add an `ANTHROPIC_API_KEY`, and Claude Haiku adds punctuation and capitals. It only keeps the result when every word matches what was lip-read; anything else, or any error, types the plain words. That step sends the text to Anthropic. Without a key, nothing leaves your computer. If you run Dictate, point `env_file` in settings at its `.env` instead of keeping a second copy of the key.

## What I found running it

- **Your webcam works for one app at a time.** Silent Type opens it when you hold the keys and lets go 15 seconds after your last phrase, so it never blocks a video call for long. The first hold shows "Starting camera · keep holding" for about two seconds; holds within those 15 seconds start instantly because the last half second is already in memory. Frames are never saved to disk.
- **The tray menu has an on/off switch** ("Silent Type on"). Off releases the camera at once and ignores the keys; the tray icon turns gray. Turn it off before a call if you've just used it.
- **No keyboard hook.** It reads the two keys' state every 20 ms. Any other key during the hold cancels it, so Ctrl+Alt shortcuts still work, and Escape cancels too.
- **Letting go of Alt last opens the app's menu** in anything with a menu bar (Notepad, Explorer), and the text would land in the menu. When a hold starts, Silent Type sends one unassigned key code (0xE8), the same trick AutoHotkey uses, so Windows doesn't treat the release as a menu press. If a menu still opens, the phrase is saved instead of typed.
- **It types only into the window you started in.** Switch windows before it finishes and the phrase is saved instead of typed. Left-click the tray icon for Recents; click a phrase to copy it.
- **It reads the biggest face in view**, so people walking behind you don't cancel a phrase.
- **The strip at the top only says Typed or Saved, not typed** (with the reason), never what you said.
- **There's no real length limit.** Long holds are read in 10-second parts while you're still going, so the text arrives right after you let go. A cut can land inside a word. A 10-minute stop catches a stuck key and types everything captured.
- **It refuses Dictate's pair** (Left Ctrl + Left Windows), so the two never fire together.
- **Laptop keyboards often have no Right Ctrl.** Change the pair in settings.

## Settings

`%LOCALAPPDATA%\Silent Type\settings.json`, written on first run. Quit and reopen after editing.

| Setting | Default | |
|---|---|---|
| `hold_pair` | `[163, 165]` | Two of: Left Ctrl 162, Right Ctrl 163, Left Alt 164, Right Alt 165, Left Windows 91, Right Windows 92 |
| `camera_warm_seconds` | `15` | How long the camera stays open after your last phrase |
| `punctuate` | `true` | `false` keeps everything local even with a key |
| `names` | `[]` | Names whose casing gets restored, like `"Cyberdyne Systems"` |
| `log_path` | empty | Where the log goes; empty means `silent-type-log.md` in this folder (ignored by Git) |
| `env_file` | empty | Another `.env` to read `ANTHROPIC_API_KEY` from |
| `max_seconds` | `600` | The stuck-key stop |

The model, history and app logs live in the same `%LOCALAPPDATA%\Silent Type` folder. Choose a different camera from the tray: **Camera and settings**.

## Update and uninstall

Update: quit Silent Type from the tray, `git pull`, delete `.venv`, and run `install.ps1` again. Settings, history and models stay where they are, and the models are rechecked, not downloaded again. The [changelog](CHANGELOG.md) lists what changed.

Uninstall: quit it, delete this folder, `%LOCALAPPDATA%\Silent Type` and the **Silent Type** shortcut in `%APPDATA%\Microsoft\Windows\Start Menu\Programs`.

## Checks

```powershell
.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
.venv\Scripts\pythonw -m silent_type.acceptance
```

The first runs the behavior tests. The second is a five-minute review run: hold your pair, mouth a phrase, and the recognized words show on the strip without typing into anything. `python -m tests.app_smoke`, `tests.hold_pipeline` and `tests.delivery_pipeline` exercise the real camera and model; the last one presses Right Ctrl + Right Alt through Windows, types a fixed phrase into a test window and checks the camera is released, so keep your hands off the keyboard while it runs. [CONTRIBUTING.md](CONTRIBUTING.md) has the lint and audit steps and how the modules fit together.

## Credits and terms

App code: MIT, see [LICENSE](LICENSE). Auto-AVSR code in `vendor/auto_avsr/` is unchanged and Apache 2.0, and the MediaPipe face model is Google's, Apache 2.0; [THIRD_PARTY.md](THIRD_PARTY.md) has the provenance and the citation. Upstream doesn't state terms for this checkpoint, and each install downloads its own copy, so check it against how you plan to use it.
