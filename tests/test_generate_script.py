import unittest

from scripts.generate_script import DISCLAIMER, validate_script


APPROVED_SOURCE = "https://example.org/approved-source"


def valid_result() -> dict:
    return {
        "title": "A safe educational title",
        "hook": "A short educational hook",
        "spoken_script": " ".join(["education"] * 120) + " " + DISCLAIMER,
        "on_screen_lines": ["General education", "Check approved sources"],
        "caption": f"General education. {DISCLAIMER} AI-assisted visuals/editing used; face/voice are owner-authorized.",
        "claims": [{"text": "A cautious claim", "source_url": APPROVED_SOURCE, "confidence": "medium"}],
        "sources": [APPROVED_SOURCE],
        "confidence": "medium",
    }


class ValidateScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.topic = {"sources": [APPROVED_SOURCE]}

    def test_accepts_source_grounded_disclosed_script(self) -> None:
        validate_script(valid_result(), self.topic)

    def test_rejects_non_array_claims(self) -> None:
        result = valid_result()
        result["claims"] = "not an array"
        with self.assertRaisesRegex(RuntimeError, "claims must be a non-empty array"):
            validate_script(result, self.topic)

    def test_rejects_empty_claim_text(self) -> None:
        result = valid_result()
        result["claims"] = [{"text": "", "source_url": APPROVED_SOURCE, "confidence": "medium"}]
        with self.assertRaisesRegex(RuntimeError, "Every generated claim must include non-empty text"):
            validate_script(result, self.topic)

    def test_rejects_unapproved_claim_source(self) -> None:
        result = valid_result()
        result["claims"] = [{"text": "A claim", "source_url": "https://example.org/unapproved", "confidence": "medium"}]
        with self.assertRaisesRegex(RuntimeError, "outside the approved source list"):
            validate_script(result, self.topic)


if __name__ == "__main__":
    unittest.main()
