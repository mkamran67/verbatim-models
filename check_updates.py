#!/usr/bin/env python3
"""Check upstream model sources for updates to catalog.json.

Usage: python3 check_updates.py [--write]

Vosk: compares each entry with alphacephei's model-list.json and, with --write,
moves an entry to the newest non-obsolete version of the same family, keeping
the old name in previousNames so installed copies show "Update available".

Whisper: compares sizes with the sherpa-onnx asr-models GitHub release. Upstream
re-publishes in place under the same name, so drift is reported for manual review.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

CATALOG = Path(__file__).with_name("catalog.json")
VOSK_LIST_URL = "https://alphacephei.com/vosk/models/model-list.json"
WHISPER_RELEASE_URL = "https://api.github.com/repos/k2-fsa/sherpa-onnx/releases/tags/asr-models"
VERSION = re.compile(r"\d+(?:\.\d+)+")


def _version(text):
    return tuple(int(part) for part in text.split("."))


def newer_vosk(name, model_list):
    """The newest non-obsolete model of the same family as `name`, or None if `name` is current."""
    match = VERSION.search(name)
    if not match:
        return None
    family = re.compile(re.escape(name[: match.start()]) + f"({VERSION.pattern})" + re.escape(name[match.end():]))
    best, best_version = None, _version(match.group())
    for model in model_list:
        found = family.fullmatch(model["name"])
        if found and model.get("obsolete") != "true" and _version(found.group(1)) > best_version:
            best, best_version = model, _version(found.group(1))
    return best


def apply_vosk_update(entry, model):
    entry["previousNames"] = entry.get("previousNames", []) + [entry["name"]]
    entry["name"] = model["name"]
    entry["url"] = model["url"]
    entry["sizeBytes"] = model["size"]


def whisper_drift(entries, asset_sizes):
    problems = []
    for entry in entries:
        size = asset_sizes.get(entry["name"] + ".tar.bz2")
        if size is None:
            problems.append(f"{entry['name']}: missing from release")
        elif size != entry["sizeBytes"]:
            problems.append(f"{entry['name']}: upstream size {size} != catalog {entry['sizeBytes']}")
    return problems


def _fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "verbatim-models-check"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main(write):
    catalog = json.loads(CATALOG.read_text())
    vosk_list = _fetch_json(VOSK_LIST_URL)
    assets = {a["name"]: a["size"] for a in _fetch_json(WHISPER_RELEASE_URL)["assets"]}

    updates = []
    for entry in catalog["vosk"]:
        model = newer_vosk(entry["name"], vosk_list)
        if model:
            updates.append(f"{entry['name']} -> {model['name']}")
            if write:
                apply_vosk_update(entry, model)
    drift = whisper_drift(catalog["whisperOnnx"], assets)

    for line in updates:
        print("vosk update:", line)
    for line in drift:
        print("whisper needs review:", line)
    if not updates and not drift:
        print("All models are current.")
    if write and updates:
        CATALOG.write_text(json.dumps(catalog, indent=2) + "\n")
        print(f"Wrote {CATALOG.name}. Review the diff, commit and push to publish.")
    return 1 if (updates and not write) or drift else 0


if __name__ == "__main__":
    sys.exit(main("--write" in sys.argv[1:]))
