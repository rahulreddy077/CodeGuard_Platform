import unittest
import json
from backend.services.embedding import EmbeddingService
from backend.services.similarity import SimilarityService

class TestEmbeddingAndSimilarity(unittest.TestCase):
    def test_cosine_similarity_identical(self):
        v1 = [1.0, 2.0, 3.0, 4.0]
        v2 = [1.0, 2.0, 3.0, 4.0]
        sim = SimilarityService.calculate_cosine_similarity(v1, v2)
        self.assertEqual(sim, 1.0)

    def test_cosine_similarity_orthogonal(self):
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        sim = SimilarityService.calculate_cosine_similarity(v1, v2)
        self.assertEqual(sim, 0.0)

    def test_cosine_similarity_opposite(self):
        v1 = [1.0, 2.0]
        v2 = [-1.0, -2.0]
        sim = SimilarityService.calculate_cosine_similarity(v1, v2)
        self.assertEqual(sim, -1.0)

    def test_jaccard_similarity(self):
        str1 = "Module FunctionDef If Return"
        str2 = "Module FunctionDef For Return"
        sim = SimilarityService.calculate_jaccard_similarity(str1, str2)
        # Unique words: Module, FunctionDef, If, For, Return (5 words)
        # Intersection: Module, FunctionDef, Return (3 words)
        # Jaccard = 3 / 5 = 0.6
        self.assertEqual(sim, 0.6)

    def test_jaccard_similarity_empty(self):
        sim = SimilarityService.calculate_jaccard_similarity("", "Module")
        self.assertEqual(sim, 0.0)

    def test_embedding_generation(self):
        # This test checks embedding generation.
        # Since it depends on PyTorch/Transformers downloading the 476MB model on first run,
        # it verifies that a valid 768-dimensional float list is produced.
        code = "def hello():\n    print('world')"
        try:
            emb = EmbeddingService.get_embedding(code)
            self.assertIsInstance(emb, list)
            self.assertEqual(len(emb), 768)
            self.assertIsInstance(emb[0], float)
        except Exception as e:
            self.fail(f"Embedding generation failed: {str(e)}")

if __name__ == "__main__":
    unittest.main()
