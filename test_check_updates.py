import unittest

from check_updates import apply_vosk_update, newer_vosk, sha256_of, whisper_drift

VOSK_LIST = [
    {"name": "vosk-model-small-en-us-0.15", "obsolete": "false", "size": 41205931,
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"},
    {"name": "vosk-model-small-en-us-0.4", "obsolete": "true", "size": 1,
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.4.zip"},
    {"name": "vosk-model-small-en-us-0.22", "obsolete": "false", "size": 42000000,
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.22.zip"},
    {"name": "vosk-model-small-en-us-zamia-0.5", "obsolete": "false", "size": 1,
     "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-zamia-0.5.zip"},
    {"name": "vosk-model-en-us-0.22-lgraph", "obsolete": "false", "size": 128000000,
     "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip"},
]


class NewerVosk(unittest.TestCase):
    def test_picks_highest_non_obsolete_version_of_the_same_family(self):
        self.assertEqual(newer_vosk("vosk-model-small-en-us-0.15", VOSK_LIST)["name"], "vosk-model-small-en-us-0.22")

    def test_versions_compare_numerically_not_as_text(self):
        # With 0.4 not obsolete, it still loses: 0.4 sorts after 0.22 as text, but (0, 22) > (0, 4).
        listed = [dict(m, obsolete="false") if m["name"].endswith("0.4") else m for m in VOSK_LIST]
        self.assertEqual(newer_vosk("vosk-model-small-en-us-0.15", listed)["name"], "vosk-model-small-en-us-0.22")

    def test_ignores_other_variants_and_suffixes(self):
        self.assertIsNone(newer_vosk("vosk-model-en-us-0.22-lgraph", VOSK_LIST))

    def test_current_version_returns_none(self):
        self.assertIsNone(newer_vosk("vosk-model-small-en-us-0.22", VOSK_LIST))


class ApplyVoskUpdate(unittest.TestCase):
    def test_moves_old_name_into_previous_names(self):
        entry = {"name": "vosk-model-small-en-us-0.15", "url": "old", "sizeBytes": 1, "sha256": "old", "previousNames": []}
        apply_vosk_update(entry, VOSK_LIST[2], "ab" * 32)
        self.assertEqual(entry["name"], "vosk-model-small-en-us-0.22")
        self.assertEqual(entry["url"], VOSK_LIST[2]["url"])
        self.assertEqual(entry["sizeBytes"], 42000000)
        self.assertEqual(entry["previousNames"], ["vosk-model-small-en-us-0.15"])
        self.assertEqual(entry["sha256"], "ab" * 32)


class Sha256Of(unittest.TestCase):
    def test_hashes_streamed_bytes(self):
        import io
        self.assertEqual(sha256_of(io.BytesIO(b"hello")), "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")


class WhisperDrift(unittest.TestCase):
    def test_reports_size_changes_and_missing_assets(self):
        assets = {"sherpa-onnx-whisper-tiny.tar.bz2": 100}
        entries = [{"name": "sherpa-onnx-whisper-tiny", "sizeBytes": 99}, {"name": "sherpa-onnx-whisper-base", "sizeBytes": 5}]
        self.assertEqual(
            whisper_drift(entries, assets),
            ["sherpa-onnx-whisper-tiny: upstream size 100 != catalog 99", "sherpa-onnx-whisper-base: missing from release"],
        )

    def test_matching_sizes_report_nothing(self):
        self.assertEqual(whisper_drift([{"name": "a", "sizeBytes": 1}], {"a.tar.bz2": 1}), [])


if __name__ == "__main__":
    unittest.main()
