import unittest
from backend.analyzer import analyze_code, validate_source

class AnalyzerTests(unittest.TestCase):
    def test_python_syntax_error(self):
        result = validate_source("def broken(:\n pass", "python")
        self.assertFalse(result["valid"])

    def test_sql_concat_detected(self):
        code = 'query = "SELECT * FROM users WHERE name = \'" + username'
        result = analyze_code(code, "python", "sample.py")
        self.assertTrue(any(f["rule_id"] == "SEC001" for f in result["findings"]))

    def test_parameterized_query_not_flagged_as_sql_concat(self):
        code = 'cursor.execute("SELECT * FROM users WHERE name = ?", (username,))'
        result = analyze_code(code, "python", "sample.py")
        self.assertFalse(any(f["rule_id"] == "SEC001" for f in result["findings"]))

if __name__ == "__main__":
    unittest.main()
