import unittest
from unittest.mock import patch

from backend.knowledge import answer_question, chunk_markdown


class RAGTests(unittest.TestCase):
    def test_markdown_is_split_into_chunks(self):
        text = "\n\n".join([f"## Section {i}\n" + ("secure coding guidance " * 25) for i in range(8)])
        chunks = chunk_markdown(text, chunk_size=350, overlap=40)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))
        self.assertTrue(all(len(chunk) <= 390 for chunk in chunks))

    def test_chunk_parameters_are_validated(self):
        with self.assertRaises(ValueError):
            chunk_markdown("hello", chunk_size=50)
        with self.assertRaises(ValueError):
            chunk_markdown("hello", chunk_size=100, overlap=100)

    @patch("backend.knowledge._rag.retrieve")
    @patch("backend.knowledge._generate_grounded_answer")
    def test_answer_uses_retrieved_context_when_no_llm_answer(self, generate, retrieve):
        retrieve.return_value = [{"text": "Use parameterized SQL queries.", "source": "secure_coding.md", "chunk": 2, "distance": 0.12}]
        generate.return_value = None
        result = answer_question("How do I prevent SQL injection?")
        self.assertIn("parameterized SQL", result["answer"])
        self.assertEqual(result["retrieval"], "embedding-based semantic search with Chroma vector store")
        self.assertEqual(result["sources"][0]["chunk"], 2)

    def test_empty_question_rejected(self):
        with self.assertRaises(ValueError):
            answer_question("   ")


if __name__ == "__main__":
    unittest.main()
