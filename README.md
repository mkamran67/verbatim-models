# Verbatim models

Public catalog of the on-device speech models the Verbatim Android app offers for download.

The app fetches `catalog.json` from this repo at most once an hour when Settings or onboarding opens.
It falls back to its last fetched copy, then to the copy bundled in the app.

## Checking for upstream updates

```sh
python3 check_updates.py          # report only, exits 1 when something changed
python3 check_updates.py --write  # move Vosk entries to their newest version
```

Vosk updates come from alphacephei's `model-list.json`.
An updated entry keeps its old directory name in `previousNames`, so users who have it installed see "Update available".
Whisper entries are checked against the sherpa-onnx `asr-models` GitHub release and are only reported, since upstream re-publishes under the same file names.
After a Whisper re-publish, update its `sha256` with `curl -sL <url> | shasum -a 256`.

Review the diff, then commit and push to `main` to publish.

## Rules the app enforces

- `schemaVersion` must be `1`.
- Download URLs must be `https` under `github.com/k2-fsa/sherpa-onnx/releases/download/` or `alphacephei.com/vosk/models/`.
- Every entry needs a lowercase hex `sha256` of its archive; the app deletes a download that does not match.
- Model names and `previousNames` must match `[A-Za-z0-9][A-Za-z0-9._-]*` and be unique.
- `sherpa-onnx-whisper-tiny` and `sherpa-onnx-whisper-base` must be present.

A catalog that breaks any rule is ignored and the app keeps its current one.

Run `python3 -m unittest test_check_updates` after changing the script.
