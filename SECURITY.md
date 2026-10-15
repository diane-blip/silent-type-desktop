# Security

Silent Type runs with your Windows user's permissions, reads the state of your held keys and types into the window in front. It is not a sandbox; review the code and dependencies before installing.

- Installs are hash-locked: every package, PyTorch included, must match a SHA-256 in `requirements-cuda.lock` or `requirements-cpu.lock`. Both models are checked by full SHA-256 before they are used.
- Lip reading and face detection run locally. Camera frames stay in memory and are discarded after each phrase.
- With an `ANTHROPIC_API_KEY`, recognized text goes to Anthropic for punctuation. Keys live in plaintext `.env` files.
- History (`history.sqlite3`) and the phrase log are plaintext on your disk. Clear history from the app; delete the log file to remove it.

Never put keys or real phrases in an issue. Report a suspected problem privately to diane@swayrisecreative.com with a fictional reproduction.
