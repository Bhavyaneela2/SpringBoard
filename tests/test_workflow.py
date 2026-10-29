import unittest
from unittest.mock import patch

from backend.analyzer import analyze_code, detect_language
from frontend.uploads import decode_uploaded_source
from backend.reports import markdown_report


class WorkflowTests(unittest.TestCase):
    def test_language_detection_uses_extension_without_manual_selection(self):
        self.assertEqual(detect_language("class Demo {}", "Demo.java"), "java")
        self.assertEqual(detect_language("def hello():\n    pass", "snippet.txt"), "python")
        self.assertIsNone(detect_language("plain text", "snippet.txt"))

    def test_parallel_agents_produce_normalized_quality_and_security_findings(self):
        code = 'password = "not-a-placeholder"\nprint("debug")\nquery = "SELECT * FROM users WHERE id = \'" + user_id'
        result = analyze_code(code, "python", "sample.py")
        self.assertTrue(result["validation"]["valid"])
        self.assertEqual([finding["line"] for finding in result["findings"]], [1, 3, 2])
        self.assertTrue(any(f["agent"] == "Security Vulnerability Agent" for f in result["findings"]))
        self.assertTrue(any(f["agent"] == "Code Analysis Agent" for f in result["findings"]))

    def test_markdown_report_is_valid_for_empty_results(self):
        report = markdown_report({
            "filename": "clean.py",
            "language": "python",
            "findings": [],
            "severity_counts": {},
            "pr_summary": {"verdict": "No findings", "roadmap": []},
        })
        self.assertIn("# Code Review Report", report)
        self.assertIn("does not prove", report)

    def test_uploaded_source_is_decoded_and_invalid_uploads_are_rejected(self):
        self.assertEqual(decode_uploaded_source("Example.PY", b"\xef\xbb\xbfprint('x')"), "print('x')")
        with self.assertRaisesRegex(ValueError, "empty"):
            decode_uploaded_source("empty.py", b"")
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            decode_uploaded_source("notes.txt", b"print('x')")
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            decode_uploaded_source("bad.py", b"\xff")

    @patch("backend.analyzer.security_vulnerability_agent", side_effect=RuntimeError("scanner unavailable"))
    def test_agent_failure_preserves_other_agent_findings(self, _security_agent):
        result = analyze_code("print('debug')", "python", "sample.py")
        self.assertTrue(any(f["rule_id"] == "QUAL001" for f in result["findings"]))
        self.assertTrue(any("Security Vulnerability Agent failed" in warning for warning in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
